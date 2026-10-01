"""Validated CSV imports that persist sales and inventory data."""

from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Iterable

import pandas as pd
from sqlalchemy.orm import Session

from app.api.schemas import UploadResponse
from app.models.inventory import Inventory
from app.models.customers import Customer
from app.models.commerce import Product, Sale, SaleItem, StockMovement
from app.models.outlet import Outlet


class DataService:
    SALES_COLUMNS = {"sale_date", "outlet_id", "product_id", "quantity", "unit_price"}
    INVENTORY_COLUMNS = {"outlet_id", "product_id", "current_stock"}
    PAYMENT_METHODS = {"cash", "card", "upi", "netbanking", "wallet", "credit"}
    CHANNELS = {"offline", "online", "manual"}

    @staticmethod
    def _optional(row: pd.Series, key: str, default=None):
        value = row.get(key, default)
        return default if pd.isna(value) else value

    @staticmethod
    def _frame(file_content: bytes) -> pd.DataFrame:
        if len(file_content) > 10 * 1024 * 1024:
            raise ValueError("CSV files must be 10 MB or smaller")
        frame = pd.read_csv(io.BytesIO(file_content))
        frame.columns = [str(column).strip().lower() for column in frame.columns]
        if frame.empty:
            raise ValueError("CSV contains no data rows")
        return frame

    @staticmethod
    def _missing(frame: pd.DataFrame, required: Iterable[str]) -> list[str]:
        return sorted(set(required) - set(frame.columns))

    def process_sales_upload(
        self,
        file_content: bytes,
        db: Session,
        organization_id: int,
        allowed_outlet_ids: list[int],
        user_id: int | None = None,
    ) -> UploadResponse:
        try:
            frame = self._frame(file_content)
        except Exception as exc:
            return UploadResponse(rows_processed=0, validation_errors=[str(exc)], status="failed")

        missing = self._missing(frame, self.SALES_COLUMNS)
        if missing:
            return UploadResponse(
                rows_processed=0,
                validation_errors=[f"Missing required columns: {', '.join(missing)}"],
                status="failed",
            )

        errors: list[str] = []
        processed = 0
        allowed = set(allowed_outlet_ids)
        try:
            for index, row in frame.iterrows():
                row_number = index + 2
                try:
                    outlet_id = int(row["outlet_id"])
                    product_id = int(row["product_id"])
                    quantity = int(row["quantity"])
                    unit_price = Decimal(str(row["unit_price"]))
                    sale_date = pd.to_datetime(row["sale_date"], utc=True).to_pydatetime()
                    if outlet_id not in allowed:
                        raise ValueError("outlet is not accessible")
                    if quantity <= 0 or unit_price < 0:
                        raise ValueError("quantity must be positive and unit_price non-negative")

                    outlet = (
                        db.query(Outlet.id)
                        .filter(
                            Outlet.id == outlet_id,
                            Outlet.organization_id == organization_id,
                            Outlet.is_deleted.is_(False),
                        )
                        .first()
                    )
                    product = (
                        db.query(Product)
                        .filter(
                            Product.id == product_id,
                            Product.organization_id == organization_id,
                            Product.is_deleted.is_(False),
                        )
                        .first()
                    )
                    inventory = (
                        db.query(Inventory)
                        .filter(
                            Inventory.outlet_id == outlet_id,
                            Inventory.product_id == product_id,
                        )
                        .with_for_update()
                        .first()
                    )
                    if not outlet or not product:
                        raise ValueError("unknown outlet or product")
                    if not inventory or inventory.current_stock < quantity:
                        raise ValueError("insufficient inventory")

                    payment_method = str(self._optional(row, "payment_method", "cash")).strip().lower()
                    if payment_method not in self.PAYMENT_METHODS:
                        raise ValueError(f"unsupported payment_method '{payment_method}'")
                    discount = Decimal(str(self._optional(row, "discount_amount", 0) or 0))
                    tax = Decimal(str(self._optional(row, "tax_amount", 0) or 0))
                    if not discount.is_finite() or not tax.is_finite() or discount < 0 or tax < 0:
                        raise ValueError("discount_amount and tax_amount must be finite and non-negative")
                    subtotal = unit_price * quantity
                    total = subtotal + tax - discount
                    if total < 0:
                        raise ValueError("total amount cannot be negative")

                    customer_id = self._optional(row, "customer_id")
                    customer = None
                    if customer_id is not None:
                        customer = (
                            db.query(Customer)
                            .filter(
                                Customer.id == int(customer_id),
                                Customer.organization_id == organization_id,
                                Customer.is_deleted.is_(False),
                            )
                            .first()
                        )
                        if customer is None:
                            raise ValueError("unknown customer")

                    channel = str(self._optional(row, "channel", "offline")).strip().lower()
                    if channel not in self.CHANNELS:
                        raise ValueError(f"unsupported channel '{channel}'")

                    supplied_number = self._optional(row, "sale_number")
                    sale_number = str(supplied_number).strip() if supplied_number is not None else ""
                    if not sale_number:
                        sale_number = f"CSV-{uuid.uuid4().hex[:12].upper()}"
                    if db.query(Sale.id).filter(Sale.sale_number == sale_number).first():
                        raise ValueError(f"duplicate sale_number '{sale_number}'")

                    sale = Sale(
                        organization_id=organization_id,
                        outlet_id=outlet_id,
                        customer_id=customer.id if customer else None,
                        sale_number=sale_number,
                        sale_date=sale_date,
                        subtotal=subtotal,
                        tax_amount=tax,
                        discount_amount=discount,
                        total_amount=total,
                        payment_method=payment_method,
                        payment_status="paid",
                        amount_paid=total,
                        status="completed",
                        channel=channel,
                    )
                    sale.items.append(
                        SaleItem(
                            organization_id=organization_id,
                            product_id=product_id,
                            quantity=quantity,
                            unit_price=unit_price,
                            line_total=subtotal,
                        )
                    )
                    stock_before = inventory.current_stock
                    inventory.current_stock -= quantity
                    db.add(
                        StockMovement(
                            organization_id=organization_id,
                            outlet_id=outlet_id,
                            product_id=product_id,
                            movement_type="sale",
                            quantity=-quantity,
                            stock_before=stock_before,
                            stock_after=inventory.current_stock,
                            user_id=user_id,
                            notes="CSV sales import",
                        )
                    )
                    if customer:
                        customer.total_purchases = Decimal(customer.total_purchases or 0) + total
                        customer.total_transactions = int(customer.total_transactions or 0) + 1
                    db.add(sale)
                    db.flush()
                    processed += 1
                except (ValueError, TypeError, InvalidOperation) as exc:
                    errors.append(f"Row {row_number}: {exc}")
            db.commit()
        except Exception:
            db.rollback()
            raise

        return UploadResponse(
            rows_processed=processed,
            validation_errors=errors,
            status="success" if processed and not errors else "partial" if processed else "failed",
        )

    def process_inventory_upload(
        self,
        file_content: bytes,
        db: Session,
        organization_id: int,
        allowed_outlet_ids: list[int],
        user_id: int | None = None,
    ) -> UploadResponse:
        try:
            frame = self._frame(file_content)
        except Exception as exc:
            return UploadResponse(rows_processed=0, validation_errors=[str(exc)], status="failed")

        missing = self._missing(frame, self.INVENTORY_COLUMNS)
        if missing:
            return UploadResponse(
                rows_processed=0,
                validation_errors=[f"Missing required columns: {', '.join(missing)}"],
                status="failed",
            )

        errors: list[str] = []
        processed = 0
        allowed = set(allowed_outlet_ids)
        try:
            for index, row in frame.iterrows():
                row_number = index + 2
                try:
                    outlet_id = int(row["outlet_id"])
                    product_id = int(row["product_id"])
                    current_stock = int(row["current_stock"])
                    reserved_stock = int(self._optional(row, "reserved_stock", 0) or 0)
                    if outlet_id not in allowed:
                        raise ValueError("outlet is not accessible")
                    if current_stock < 0 or reserved_stock < 0 or reserved_stock > current_stock:
                        raise ValueError("stock values are invalid")
                    product = (
                        db.query(Product.id)
                        .filter(
                            Product.id == product_id,
                            Product.organization_id == organization_id,
                            Product.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if not product:
                        raise ValueError("unknown product")
                    outlet = (
                        db.query(Outlet.id)
                        .filter(
                            Outlet.id == outlet_id,
                            Outlet.organization_id == organization_id,
                            Outlet.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if not outlet:
                        raise ValueError("unknown outlet")
                    inventory = (
                        db.query(Inventory)
                        .filter(
                            Inventory.outlet_id == outlet_id,
                            Inventory.product_id == product_id,
                        )
                        .first()
                    )
                    stock_before = inventory.current_stock if inventory is not None else 0
                    if inventory is None:
                        inventory = Inventory(
                            organization_id=organization_id,
                            outlet_id=outlet_id,
                            product_id=product_id,
                        )
                        db.add(inventory)
                    inventory.current_stock = current_stock
                    inventory.reserved_stock = reserved_stock
                    inventory.last_restocked_at = datetime.now(timezone.utc)
                    if current_stock != stock_before:
                        db.add(
                            StockMovement(
                                organization_id=organization_id,
                                outlet_id=outlet_id,
                                product_id=product_id,
                                movement_type="adjustment",
                                quantity=current_stock - stock_before,
                                stock_before=stock_before,
                                stock_after=current_stock,
                                user_id=user_id,
                                notes="CSV inventory import",
                            )
                        )
                    processed += 1
                except (ValueError, TypeError) as exc:
                    errors.append(f"Row {row_number}: {exc}")
            db.commit()
        except Exception:
            db.rollback()
            raise

        return UploadResponse(
            rows_processed=processed,
            validation_errors=errors,
            status="success" if processed and not errors else "partial" if processed else "failed",
        )
