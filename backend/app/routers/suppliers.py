"""Authenticated supplier management for the single organization."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.database import get_db_sync_dependency
from app.models.users import User
from app.schemas.supplier import SupplierCreate, SupplierUpdate
from app.services.supplier_service import SupplierService


router = APIRouter(prefix="/suppliers", tags=["suppliers"])


def _service(db: Session, user: User) -> SupplierService:
    return SupplierService(db, user.organization_id)


@router.post("/", status_code=201)
def create_supplier(
    data: SupplierCreate,
    db: Session = Depends(get_db_sync_dependency),
    current_user: User = Depends(require_role("admin")),
):
    supplier = _service(db, current_user).create(data.model_dump())
    return {"success": True, "data": SupplierService.serialize(supplier)}


@router.get("")
@router.get("/")
def list_suppliers(
    search: Optional[str] = None,
    city: Optional[str] = None,
    is_active: bool = True,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db_sync_dependency),
    current_user: User = Depends(require_role("admin")),
):
    return _service(db, current_user).list(search, city, is_active, page, per_page)


@router.get("/{supplier_id}")
def get_supplier(
    supplier_id: int, db: Session = Depends(get_db_sync_dependency), current_user: User = Depends(require_role("admin"))
):
    supplier = _service(db, current_user).get(supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"success": True, "data": SupplierService.serialize(supplier)}


@router.put("/{supplier_id}")
def update_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    db: Session = Depends(get_db_sync_dependency),
    current_user: User = Depends(require_role("admin")),
):
    supplier = _service(db, current_user).update(supplier_id, data.model_dump(exclude_unset=True))
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"success": True, "data": SupplierService.serialize(supplier)}


@router.delete("/{supplier_id}")
def delete_supplier(
    supplier_id: int, db: Session = Depends(get_db_sync_dependency), current_user: User = Depends(require_role("admin"))
):
    if not _service(db, current_user).deactivate(supplier_id):
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"success": True, "message": "Supplier deactivated"}
