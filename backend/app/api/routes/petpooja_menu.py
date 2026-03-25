"""
Petpooja Menu Management API
Handles menu CRUD operations, categories, and item availability
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

router = APIRouter(prefix="/api/petpooja/menu")

# In-memory menu storage (in production, use database)
MENU_ITEMS = {}
NEXT_ITEM_ID = 1

# Predefined categories
CATEGORIES = ["Starters", "Main Course", "Desserts", "Beverages"]

# Sample menu items
SAMPLE_MENU = [
    {"name": "Paneer Tikka", "category": "Starters", "price": 280, "description": "Grilled cottage cheese with spices", "is_veg": True, "is_available": True, "prep_time": 15},
    {"name": "Chicken Tikka", "category": "Starters", "price": 320, "description": "Grilled chicken marinated in yogurt and spices", "is_veg": False, "is_available": True, "prep_time": 20},
    {"name": "Veg Spring Rolls", "category": "Starters", "price": 180, "description": "Crispy rolls with mixed vegetables", "is_veg": True, "is_available": True, "prep_time": 12},
    {"name": "Fish Fingers", "category": "Starters", "price": 350, "description": "Crispy fried fish strips", "is_veg": False, "is_available": True, "prep_time": 15},
    
    {"name": "Butter Chicken", "category": "Main Course", "price": 380, "description": "Creamy tomato-based chicken curry", "is_veg": False, "is_available": True, "prep_time": 25},
    {"name": "Dal Makhani", "category": "Main Course", "price": 280, "description": "Creamy black lentils", "is_veg": True, "is_available": True, "prep_time": 20},
    {"name": "Biryani (Veg)", "category": "Main Course", "price": 320, "description": "Aromatic rice with vegetables", "is_veg": True, "is_available": True, "prep_time": 30},
    {"name": "Biryani (Chicken)", "category": "Main Course", "price": 380, "description": "Aromatic rice with chicken", "is_veg": False, "is_available": True, "prep_time": 35},
    {"name": "Paneer Butter Masala", "category": "Main Course", "price": 320, "description": "Cottage cheese in rich tomato gravy", "is_veg": True, "is_available": True, "prep_time": 20},
    
    {"name": "Gulab Jamun", "category": "Desserts", "price": 120, "description": "Sweet milk dumplings in sugar syrup", "is_veg": True, "is_available": True, "prep_time": 5},
    {"name": "Ice Cream", "category": "Desserts", "price": 100, "description": "Assorted flavors", "is_veg": True, "is_available": True, "prep_time": 2},
    {"name": "Rasmalai", "category": "Desserts", "price": 140, "description": "Cottage cheese in sweet milk", "is_veg": True, "is_available": True, "prep_time": 5},
    
    {"name": "Masala Chai", "category": "Beverages", "price": 40, "description": "Indian spiced tea", "is_veg": True, "is_available": True, "prep_time": 5},
    {"name": "Fresh Lime Soda", "category": "Beverages", "price": 60, "description": "Refreshing lime drink", "is_veg": True, "is_available": True, "prep_time": 3},
    {"name": "Mango Lassi", "category": "Beverages", "price": 80, "description": "Sweet mango yogurt drink", "is_veg": True, "is_available": True, "prep_time": 5},
    {"name": "Cold Coffee", "category": "Beverages", "price": 100, "description": "Chilled coffee with ice cream", "is_veg": True, "is_available": True, "prep_time": 5},
]

class MenuItem(BaseModel):
    name: str
    category: str
    price: float
    description: Optional[str] = ""
    is_veg: bool = True
    is_available: bool = True
    prep_time: int = 15  # minutes
    image_url: Optional[str] = None

class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    is_veg: Optional[bool] = None
    is_available: Optional[bool] = None
    prep_time: Optional[int] = None
    image_url: Optional[str] = None

def initialize_menu():
    """Initialize menu with sample items"""
    global MENU_ITEMS, NEXT_ITEM_ID
    if not MENU_ITEMS:
        for item in SAMPLE_MENU:
            MENU_ITEMS[NEXT_ITEM_ID] = {
                "id": NEXT_ITEM_ID,
                **item,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            NEXT_ITEM_ID += 1

@router.get("/categories")
async def get_categories():
    """Get all menu categories"""
    return {"categories": CATEGORIES}

@router.get("/items")
async def get_menu_items(category: Optional[str] = None, available_only: bool = False):
    """Get all menu items, optionally filtered by category and availability"""
    initialize_menu()
    
    items = list(MENU_ITEMS.values())
    
    if category:
        items = [item for item in items if item["category"] == category]
    
    if available_only:
        items = [item for item in items if item["is_available"]]
    
    # Group by category
    items_by_category = {}
    for item in items:
        cat = item["category"]
        if cat not in items_by_category:
            items_by_category[cat] = []
        items_by_category[cat].append(item)
    
    return {
        "total_items": len(items),
        "items": items,
        "items_by_category": items_by_category
    }

@router.get("/items/{item_id}")
async def get_menu_item(item_id: int):
    """Get a specific menu item"""
    initialize_menu()
    
    if item_id not in MENU_ITEMS:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    return MENU_ITEMS[item_id]

@router.post("/items")
async def create_menu_item(item: MenuItem):
    """Create a new menu item"""
    global NEXT_ITEM_ID
    initialize_menu()
    
    if item.category not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {CATEGORIES}")
    
    new_item = {
        "id": NEXT_ITEM_ID,
        **item.dict(),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    MENU_ITEMS[NEXT_ITEM_ID] = new_item
    NEXT_ITEM_ID += 1
    
    return {
        "message": "Menu item created successfully",
        "item": new_item
    }

@router.put("/items/{item_id}")
async def update_menu_item(item_id: int, item_update: MenuItemUpdate):
    """Update an existing menu item"""
    initialize_menu()
    
    if item_id not in MENU_ITEMS:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    # Update only provided fields
    update_data = item_update.dict(exclude_unset=True)
    
    if "category" in update_data and update_data["category"] not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {CATEGORIES}")
    
    MENU_ITEMS[item_id].update(update_data)
    MENU_ITEMS[item_id]["updated_at"] = datetime.now().isoformat()
    
    return {
        "message": "Menu item updated successfully",
        "item": MENU_ITEMS[item_id]
    }

@router.patch("/items/{item_id}/availability")
async def toggle_availability(item_id: int, is_available: bool):
    """Toggle menu item availability"""
    initialize_menu()
    
    if item_id not in MENU_ITEMS:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    MENU_ITEMS[item_id]["is_available"] = is_available
    MENU_ITEMS[item_id]["updated_at"] = datetime.now().isoformat()
    
    return {
        "message": f"Item {'enabled' if is_available else 'disabled'} successfully",
        "item": MENU_ITEMS[item_id]
    }

@router.delete("/items/{item_id}")
async def delete_menu_item(item_id: int):
    """Delete a menu item"""
    initialize_menu()
    
    if item_id not in MENU_ITEMS:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    deleted_item = MENU_ITEMS.pop(item_id)
    
    return {
        "message": "Menu item deleted successfully",
        "item": deleted_item
    }

@router.get("/popular")
async def get_popular_items(limit: int = 5):
    """Get popular menu items (mock - in production, based on order frequency)"""
    initialize_menu()
    
    # Mock popularity based on item ID (lower ID = more popular)
    popular_items = sorted(MENU_ITEMS.values(), key=lambda x: x["id"])[:limit]
    
    return {
        "popular_items": popular_items
    }
