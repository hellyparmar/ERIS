from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Category, InventoryItem, Outlet, PriceHistory, Product, Recipe, Sale, SaleItem, Supplier, User
from app.routers.common import csv_response, get_or_404, page_response, paginate
from app.schemas import CategoryIn, ProductIn
from app.security import get_current_user, require_manager, scoped_outlet_ids
from app.services import analytics as A
from app.services.capacity import EXPORTS
from app.services.inventory import stock_status

router = APIRouter(prefix="/api", tags=["products"])


# ------------------------------------------------------------------------------------------ categories
@router.get("/categories")
def list_categories(kind: str | None = Query(None, pattern="^(menu|ingredient)$"),
                    _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Categories with their item counts. kind=menu / kind=ingredient keeps the categories holding that kind (plus
    empty ones, so a new category can be used)."""
    rows = db.execute(select(Product.category_id, Product.kind, func.count(Product.id)).group_by(
        Product.category_id, Product.kind)).all()
    counts: dict[int, dict[str, int]] = {}
    for cat_id, k, n in rows:
        counts.setdefault(cat_id, {})[k] = n
    out = []
    for c in db.scalars(select(Category).order_by(Category.name)).all():
        by_kind = counts.get(c.id, {})
        if kind and by_kind and kind not in by_kind:
            continue
        out.append({"id": c.id, "name": c.name, "products": by_kind.get(kind, 0) if kind else sum(by_kind.values()),
                    "kind": next(iter(by_kind)) if len(by_kind) == 1 else None})
    return out


@router.post("/categories", status_code=201)
def create_category(body: CategoryIn, _: User = Depends(require_manager), db: Session = Depends(get_db)):
    if db.scalar(select(Category.id).where(func.lower(Category.name) == body.name.strip().lower())):
        raise HTTPException(409, "Category already exists")
    c = Category(name=body.name.strip())
    db.add(c)
    db.commit()
    return {"id": c.id, "name": c.name, "products": 0}


@router.put("/categories/{cat_id}")
def rename_category(cat_id: int, body: CategoryIn, _: User = Depends(require_manager), db: Session = Depends(get_db)):
    c = get_or_404(db, Category, cat_id, "Category")
    clash = db.scalar(select(Category.id).where(func.lower(Category.name) == body.name.strip().lower(), Category.id != cat_id))
    if clash:
        raise HTTPException(409, "Category already exists")
    c.name = body.name.strip()
    db.commit()
    return {"id": c.id, "name": c.name}


@router.delete("/categories/{cat_id}")
def delete_category(cat_id: int, _: User = Depends(require_manager), db: Session = Depends(get_db)):
    c = get_or_404(db, Category, cat_id, "Category")
    if db.scalar(select(func.count(Product.id)).where(Product.category_id == cat_id)):
        raise HTTPException(400, "Move or delete the products in this category first")
    db.delete(c)
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------------------------------------ products
def product_dict(p: Product) -> dict:
    net = p.selling_price - p.selling_price * p.tax_rate / (100 + p.tax_rate)
    margin = net - p.cost_price
    return {"id": p.id, "kind": p.kind, "sku": p.sku, "name": p.name, "category_id": p.category_id,
            "category": p.category.name if p.category else None, "supplier_id": p.supplier_id,
            "supplier": p.supplier.name if p.supplier else None, "unit": p.unit, "cost_price": p.cost_price,
            "selling_price": p.selling_price, "tax_rate": p.tax_rate, "hsn_code": p.hsn_code, "reorder_level": p.reorder_level,
            "is_active": p.is_active, "margin_pct": round(margin / net * 100, 1) if net else 0,
            "food_cost_pct": round(p.cost_price / net * 100, 1) if net else None}


@router.get("/products")
def list_products(search: str | None = None, category_id: int | None = None, supplier_id: int | None = None,
                  kind: str | None = Query(None, pattern="^(menu|ingredient)$"),
                  fields: str | None = Query(None, pattern="^basic$"),
                  active: bool | None = True, page: int = 1, page_size: int = Query(50, le=500),
                  sort: str = "name", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Menu items and/or ingredients. fields=basic skips the 30-day figures (for pickers: much faster)."""
    q = select(Product)
    if search:
        like = f"%{search.strip()}%"
        q = q.where(or_(Product.name.ilike(like), Product.sku.ilike(like)))
    if category_id:
        q = q.where(Product.category_id == category_id)
    if supplier_id:
        q = q.where(Product.supplier_id == supplier_id)
    if kind:
        q = q.where(Product.kind == kind)
    if active is not None:
        q = q.where(Product.is_active.is_(active))
    if fields == "basic":
        order = {"sku": Product.sku.asc(), "price": Product.selling_price.desc()}.get(sort, Product.name.asc())
        rows, total = paginate(db, q.order_by(order), page, page_size)
        return page_response([product_dict(r[0]) for r in rows], total, page, page_size)

    outlet_ids = scoped_outlet_ids(user)
    anchor = A.anchor_date(db)
    stock_q = select(InventoryItem.product_id, func.sum(InventoryItem.quantity)).group_by(InventoryItem.product_id)
    if outlet_ids:
        stock_q = stock_q.where(InventoryItem.outlet_id.in_(outlet_ids))
    stock = {pid: float(v) for pid, v in db.execute(stock_q).all()}
    sold_q = select(SaleItem.product_id, func.sum(SaleItem.quantity), func.sum(SaleItem.line_total)).join(
        Sale, Sale.id == SaleItem.sale_id).where(A.COMPLETED, SaleItem.sale_date > anchor - timedelta(days=30))
    if outlet_ids:
        sold_q = sold_q.where(SaleItem.outlet_id.in_(outlet_ids))
    sold = {pid: (float(u), float(r)) for pid, u, r in db.execute(sold_q.group_by(SaleItem.product_id)).all()}
    used: dict[int, float] = {}
    if kind != "menu":
        for (_o, item), rate in A.avg_daily_usage(db, 30, anchor, outlet_ids).items():
            used[item] = used.get(item, 0.0) + rate * 30
    items = []
    for p in db.scalars(q).all():
        units, revenue = sold.get(p.id, (0.0, 0.0))
        if p.kind == "ingredient":
            units = used.get(p.id, 0.0)
        items.append({**product_dict(p), "stock": round(stock.get(p.id, 0.0), 1), "units_30d": round(units, 1),
                      "revenue_30d": round(revenue, 2)})
    keyf = {"name": lambda r: r["name"], "sku": lambda r: r["sku"], "price": lambda r: -r["selling_price"],
            "revenue": lambda r: -r["revenue_30d"], "units": lambda r: -r["units_30d"],
            "stock": lambda r: r["stock"], "food_cost": lambda r: -(r["food_cost_pct"] or 0)}.get(sort, lambda r: r["name"])
    items.sort(key=keyf)
    page = max(1, page)
    return page_response(items[(page - 1) * page_size: page * page_size], len(items), page, page_size)


@router.get("/products/export")
def export_products(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    with EXPORTS():
        rows = [[p.kind, p.sku, p.name, p.category.name, p.unit, p.cost_price, p.selling_price, p.tax_rate,
                 p.reorder_level, p.supplier.name if p.supplier else "",
                 "; ".join(f"{r.ingredient.sku}={r.quantity:g}" for r in p.recipe)]
                for p in db.scalars(select(Product).order_by(Product.kind.desc(), Product.sku)).all()]
        return csv_response("menu_and_ingredients.csv", ["kind", "sku", "name", "category", "unit", "cost_price",
                                                         "selling_price", "tax_rate", "reorder_level", "supplier",
                                                         "recipe"], rows)


def _portions(db: Session, recipe: list[Recipe], outlet_ids: list[int] | None) -> list[dict]:
    """Portions of a dish each outlet can make from its ingredient stock (the scarcest ingredient decides)."""
    if not recipe:
        return []
    q = select(InventoryItem.outlet_id, InventoryItem.product_id, InventoryItem.quantity).where(
        InventoryItem.product_id.in_([r.ingredient_id for r in recipe]))
    if outlet_ids:
        q = q.where(InventoryItem.outlet_id.in_(outlet_ids))
    stock: dict[int, dict[int, float]] = {}
    for o, i, qty in db.execute(q).all():
        stock.setdefault(o, {})[i] = qty
    names = A.outlet_names(db)
    out = []
    for o, have in sorted(stock.items()):
        per = {r.ingredient_id: have.get(r.ingredient_id, 0.0) / r.quantity for r in recipe if r.quantity > 0}
        limit = min(per, key=per.get)
        out.append({"outlet_id": o, "outlet": names.get(o), "portions": max(0, int(per[limit])),
                    "limited_by": next(r.ingredient.name for r in recipe if r.ingredient_id == limit)})
    return out


@router.get("/products/{product_id}")
def get_product(product_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = get_or_404(db, Product, product_id, "Product")
    outlet_ids = scoped_outlet_ids(user)
    anchor = A.anchor_date(db)
    rng90 = A.DateRange(anchor - timedelta(days=89), anchor)
    rng30 = A.DateRange(anchor - timedelta(days=29), anchor)
    if p.kind == "ingredient":
        usage = A.avg_daily_usage(db, 28, anchor, outlet_ids)
        q = select(InventoryItem, Outlet).join(Outlet, Outlet.id == InventoryItem.outlet_id).where(
            InventoryItem.product_id == p.id).order_by(Outlet.id)
        if outlet_ids:
            q = q.where(InventoryItem.outlet_id.in_(outlet_ids))
        stock = []
        for inv, o in db.execute(q).all():
            rate = usage.get((o.id, p.id), 0)
            stock.append({"outlet_id": o.id, "outlet": o.name, "quantity": inv.quantity,
                          "reorder_level": inv.reorder_level, "avg_daily_demand": round(rate, 2),
                          "days_of_cover": round(inv.quantity / rate, 1) if rate else None,
                          "status": stock_status(inv.quantity, inv.reorder_level)})
        used_in = [{"id": d.id, "name": d.name, "quantity": r.quantity}
                   for r, d in db.execute(select(Recipe, Product).join(Product, Product.id == Recipe.menu_item_id).where(
                       Recipe.ingredient_id == p.id, Product.is_active.is_(True)).order_by(Product.name)).all()]
        costs = [{"date": d.isoformat(), "cost": c} for d, c in db.execute(
            select(PriceHistory.effective_from, PriceHistory.cost_price).where(PriceHistory.product_id == p.id)
            .order_by(PriceHistory.effective_from)).all()]
        return {**product_dict(p), "stock_by_outlet": stock,
                "total_stock": round(sum(s["quantity"] for s in stock), 2),
                "avg_daily_use": round(sum(s["avg_daily_demand"] for s in stock), 2),
                "used_in": used_in, "cost_history": costs[-12:]}

    stats = A.top_products(db, rng30, outlet_ids, 1, product_ids=[p.id])
    prev = A.top_products(db, rng30.previous(), outlet_ids, 1, product_ids=[p.id])
    recipe = list(p.recipe)
    return {
        **product_dict(p),
        "recipe": [{"ingredient_id": r.ingredient_id, "ingredient": r.ingredient.name, "sku": r.ingredient.sku,
                    "unit": r.ingredient.unit, "quantity": r.quantity, "unit_cost": r.ingredient.cost_price,
                    "cost": round(r.quantity * r.ingredient.cost_price, 2)} for r in recipe],
        "portions_by_outlet": _portions(db, recipe, outlet_ids),
        "last_30_days": stats[0] if stats else {"units": 0, "revenue": 0, "profit": 0},
        "previous_30_days": prev[0] if prev else {"units": 0, "revenue": 0, "profit": 0},
        "trend": A.revenue_series(db, rng90, outlet_ids, "week", product_id=p.id),
        "bought_with": [x for x in A.product_affinity(db, rng90, outlet_ids, limit=300, min_pair_count=10)
                        if p.id in (x["product_a_id"], x["product_b_id"])][:5],
    }


def _check_refs(db: Session, body: ProductIn) -> None:
    get_or_404(db, Category, body.category_id, "Category")
    if body.supplier_id:
        get_or_404(db, Supplier, body.supplier_id, "Supplier")
    for line in body.recipe or []:
        ing = db.get(Product, line.ingredient_id)
        if ing is None or ing.kind != "ingredient":
            raise HTTPException(400, f"Recipe line {line.ingredient_id} is not an ingredient")


def _apply_recipe(db: Session, p: Product, body: ProductIn) -> None:
    """Replace the recipe and set the food cost from it."""
    if p.kind != "menu" or body.recipe is None:
        return
    p.recipe = [Recipe(ingredient_id=line.ingredient_id, quantity=line.quantity) for line in body.recipe]
    db.flush()
    if body.recipe:
        costs = dict(db.execute(select(Product.id, Product.cost_price).where(
            Product.id.in_([line.ingredient_id for line in body.recipe]))).all())
        p.cost_price = round(sum(line.quantity * costs[line.ingredient_id] for line in body.recipe), 2)


@router.post("/products", status_code=201)
def create_product(body: ProductIn, _: User = Depends(require_manager), db: Session = Depends(get_db)):
    if db.scalar(select(Product.id).where(Product.sku == body.sku)):
        raise HTTPException(409, f"SKU {body.sku} already exists")
    _check_refs(db, body)
    p = Product(**body.model_dump(exclude={"recipe"}))
    db.add(p)
    db.flush()
    _apply_recipe(db, p, body)
    if p.kind == "ingredient":  # every kitchen gets a stock line for a new ingredient
        for o in db.scalars(select(Outlet)).all():
            db.add(InventoryItem(outlet_id=o.id, product_id=p.id, quantity=0, reorder_level=p.reorder_level))
    db.commit()
    db.refresh(p)
    return product_dict(p)


@router.put("/products/{product_id}")
def update_product(product_id: int, body: ProductIn, _: User = Depends(require_manager), db: Session = Depends(get_db)):
    p = get_or_404(db, Product, product_id, "Product")
    if body.sku != p.sku and db.scalar(select(Product.id).where(Product.sku == body.sku)):
        raise HTTPException(409, f"SKU {body.sku} already exists")
    if body.kind != p.kind:
        raise HTTPException(400, "A menu item cannot become an ingredient (or the other way round)")
    _check_refs(db, body)
    for k, v in body.model_dump(exclude={"recipe"}).items():
        setattr(p, k, v)
    _apply_recipe(db, p, body)
    db.commit()
    db.refresh(p)
    return product_dict(p)


@router.delete("/products/{product_id}")
def delete_product(product_id: int, _: User = Depends(require_manager), db: Session = Depends(get_db)):
    p = get_or_404(db, Product, product_id, "Product")
    from app.models import PurchaseOrderItem

    in_recipes = db.scalar(select(func.count(Recipe.id)).join(Product, Product.id == Recipe.menu_item_id).where(
        Recipe.ingredient_id == p.id, Product.is_active.is_(True)))
    if in_recipes:
        raise HTTPException(400, f"{p.name} is used in {in_recipes} active dish(es) - change those recipes first")
    used = db.scalar(select(func.count(SaleItem.id)).where(SaleItem.product_id == p.id)) or db.scalar(
        select(func.count(PurchaseOrderItem.id)).where(PurchaseOrderItem.product_id == p.id))
    if used:
        p.is_active = False
        db.commit()
        return {"ok": True, "deactivated": True,
                "message": "This item has sales or purchase history, so it was deactivated instead of deleted."}
    db.delete(p)
    db.commit()
    return {"ok": True, "deleted": True}
