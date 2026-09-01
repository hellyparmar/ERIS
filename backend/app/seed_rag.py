import asyncio
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

async def seed_unstructured_data():
    """
    Seeds the vector database with unstructured knowledge:
    - Product descriptions
    - Supplier terms
    - Operational notes tied to Phase 2 data trends (e.g. Diwali spike, Monsoon dip)
    - Store policies
    """
    logger.info("Starting unstructured data ingestion for Vector RAG...")

    documents: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    ids: List[str] = []

    # 1. Menu Item Descriptions (Starters, Mains, Breads, Desserts, Beverages)
    menu_items = [
        ("Paneer Tikka", "A classic North Indian starter. Soft paneer cubes marinated in yogurt and spices, then grilled in a tandoor. Contains dairy and nuts.", "Starters"),
        ("Chicken Biryani", "Aromatic basmati rice cooked with tender chicken pieces, saffron, and whole spices. A signature main course dish.", "Mains"),
        ("Butter Naan", "Soft and fluffy Indian flatbread made with refined flour, baked in a tandoor, and brushed with generous amounts of butter.", "Breads"),
        ("Gulab Jamun", "Traditional Indian dessert. Deep-fried milk-solid balls soaked in a warm, fragrant sugar syrup spiced with cardamom.", "Desserts"),
        ("Mango Lassi", "A refreshing yogurt-based beverage blended with sweet mango pulp. Perfect for cooling down spicy meals.", "Beverages"),
        ("Samosa", "Crispy pastry filled with a spiced mixture of potatoes, peas, and coriander. Served with tamarind and mint chutney.", "Starters"),
        ("Dal Makhani", "A rich and creamy lentil dish slow-cooked for 12 hours with butter and cream. A hearty vegetarian main.", "Mains"),
        ("Garlic Naan", "Tandoori flatbread topped with minced garlic and cilantro. Pairs perfectly with rich curries.", "Breads"),
        ("Rasmalai", "Soft cottage cheese patties soaked in thickened, sweetened milk flavored with cardamom and saffron.", "Desserts"),
        ("Masala Chai", "Classic Indian spiced tea brewed with ginger, cardamom, and milk. A comforting hot beverage.", "Beverages")
    ]

    for item, desc, category in menu_items:
        documents.append(desc)
        metadatas.append({"type": "menu_item", "product": item, "category": category})
        ids.append(f"menu_{item.lower().replace(' ', '_')}")

    # 2. Supplier Terms
    suppliers = [
        ("Fresh Veggies Co.", "Provides daily deliveries of fresh vegetables. Payment terms are net 15 days. Minimum order value is ₹5000."),
        ("Premium Meats Ltd", "Supplies poultry and mutton products. Requires 48-hour advance notice for bulk orders. Payment due on delivery."),
        ("Dairy Best", "Provides milk, paneer, and butter. Deliveries happen twice daily. Weekly billing cycle with 7-day payment terms."),
        ("Spice World", "Supplies whole and powdered spices. Bulk orders get a 10% discount. Payment terms are net 30 days.")
    ]

    for supplier, terms in suppliers:
        documents.append(f"Supplier {supplier}: {terms}")
        metadatas.append({"type": "supplier_terms", "supplier": supplier})
        ids.append(f"supplier_{supplier.lower().replace(' ', '_').replace('.', '')}")

    # 3. Operational Notes tied to Phase 2 patterns
    ops_notes = [
        ("Outlet 1 saw a 30% dip in sales during the second week of July due to heavy monsoon rains causing severe waterlogging in the area, reducing footfall.", "All", "monsoon"),
        ("During Diwali week in late October, the sweets and desserts category saw a 3x spike in orders across all outlets due to festive gifting and bulk corporate orders.", "All", "diwali"),
        ("A localized festival in mid-January led to a 50% increase in weekend sales for Outlet 2, primarily driven by large family dine-ins.", "Outlet 2", "festival"),
        ("Supply chain disruptions in August caused a temporary shortage of premium meat, resulting in lower sales for non-vegetarian mains for 3 days.", "All", "supply_chain"),
        ("The introduction of a new weekend buffet menu at Outlet 3 in March increased average order value but slightly slowed down table turnover rates.", "Outlet 3", "operations"),
        ("Heatwave conditions in May drove a 200% increase in beverage sales, specifically Mango Lassi and cold drinks, across all locations.", "All", "weather"),
        ("Staff shortages during the Holi festival weekend led to longer wait times and a 15% drop in customer satisfaction scores.", "All", "hr"),
        ("A targeted marketing campaign offering 20% off on weekday lunches boosted Monday-Thursday afternoon sales by 40% in September.", "All", "marketing"),
        ("Road construction near Outlet 4 starting in November has negatively impacted evening footfall, causing a 10% sustained drop in revenue.", "Outlet 4", "external"),
        ("Introduction of the new WhatsApp ordering channel drove a 25% increase in repeat orders from loyal customers in Q1.", "All", "whatsapp")
    ]

    for i, (note, outlet, tag) in enumerate(ops_notes):
        documents.append(note)
        metadatas.append({"type": "operational_note", "outlet": outlet, "tag": tag})
        ids.append(f"ops_note_{i}")

    # 4. Store Policies
    policies = [
        ("Refund Policy", "Refunds for online orders are processed within 3-5 business days. No cash refunds are provided for dine-in complaints; instead, a replacement dish or store credit is offered."),
        ("Loyalty Program", "Customers earn 1 point for every ₹100 spent. Points can be redeemed on future visits, with 1 point equal to ₹1. Points expire after 12 months of inactivity."),
        ("Opening Hours", "Outlets 1, 2, and 3 are open from 11:00 AM to 11:00 PM daily. Outlet 4 is open from 8:00 AM to 10:00 PM to cater to the morning breakfast crowd."),
        ("Employee Discount", "Active staff members receive a 30% discount on all food items for personal consumption during their shifts, excluding beverages.")
    ]

    for policy_name, policy_desc in policies:
        documents.append(f"{policy_name}: {policy_desc}")
        metadatas.append({"type": "policy", "name": policy_name})
        ids.append(f"policy_{policy_name.lower().replace(' ', '_')}")

    # Execute Add to Vector DB
    try:
        from app.services.hybrid_rag import vector_rag_service
        vector_rag_service.add_documents(documents=documents, metadatas=metadatas, ids=ids)
        logger.info(f"Successfully seeded {len(documents)} unstructured RAG documents.")
        return {"status": "success", "count": len(documents)}
    except Exception as e:
        logger.warning(f"Failed or skipped RAG document seeding (chromadb may be optional): {e}")
        return {"status": "skipped", "error": str(e)}

if __name__ == "__main__":
    asyncio.run(seed_unstructured_data())
