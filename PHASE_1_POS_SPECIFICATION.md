# PHASE 1 — POS SYSTEM DETAILED SPECIFICATION
**Status:** Ready for Design & Planning  
**Timeline:** 2 Weeks (Weeks 1-2 post-Phase-0)  
**Objective:** Full POS system that a retailer can actually use to sell

---

## EXECUTIVE SUMMARY

Phase 1 delivers **complete Point-of-Sale functionality** allowing a cashier to:
1. Scan/search for products
2. Add items to cart
3. Apply discounts
4. Process payment (cash/UPI/card)
5. Print receipt (thermal printer)
6. Send receipt via WhatsApp
7. Handle offline mode (syncs when online)

**User:** Cashier at retail counter (busy, limited tech literacy)  
**Environment:** Fast internet connection OR offline queue when connection fails  
**Performance Target:** Each operation <2 seconds  
**Success:** Cashier can complete 50+ transactions per day without friction

---

## PHASE 1 DELIVERABLES

| Feature | Week | Status | Owner |
|---------|------|--------|-------|
| **Frontend: POS Page** | 1 | 📝 Design | Frontend Lead |
| **Backend: Sale Endpoints** | 1 | 📝 Design | Backend Lead |
| **Payment Integration** | 1-2 | 📝 Design | Backend Lead |
| **Thermal Receipt (ESC/POS)** | 2 | 📝 Design | Backend Lead |
| **WhatsApp Integration** | 2 | 📝 Design | Backend Lead |
| **Offline Transaction Queue** | 2 | 📝 Design | Frontend Lead |
| **Integration Tests** | 2 | 📝 Design | QA Lead |

---

## 1. FRONTEND: POS PAGE

### 1.1 Page Structure

```
┌─────────────────────────────────────────────────────────────┐
│  R-DIOS POS — [Store Name]  [Cashier: John]  [13:45]  🟢   │
├─────────────────────────────────────────────────────────────┤
│  [Search/Barcode Input] [Recent Items ▼] [Categories ▼]    │
├────────────────────────────────────────┬────────────────────┤
│                                        │  CART (Right Side) │
│ Product List:                          │  ─────────────── │
│ ┌──────────────────────────────────┐  │  Item        Qty │
│ │ 📦 Milk - ₹50                   │  │  Milk        x2  │
│ │    In Stock: 450                │  │  ₹50 × 2 = ₹100 │
│ │    [Quick Add] [More Info]      │  │  ─────────────── │
│ ├──────────────────────────────────┤  │  Tea         x1  │
│ │ 📦 Tea - ₹25                    │  │  ₹25 × 1 = ₹25  │
│ │    In Stock: 150                │  │  ─────────────── │
│ │    [Quick Add] [More Info]      │  │  Subtotal: ₹125 │
│ ├──────────────────────────────────┤  │  Discount: -₹0  │
│ │ 📦 Biscuits - ₹15               │  │  GST (18%): ₹22.5│
│ │    In Stock: 320                │  │  ─────────────── │
│ │    [Quick Add] [More Info]      │  │  TOTAL: ₹147.5  │
│ └──────────────────────────────────┘  │  ─────────────── │
│                                        │  [Apply Discount]│
│ Scrollable Product List               │  [Remove Item]   │
│ ← Paginate →                           │  [Clear Cart]    │
│                                        └────────────────────┤
├─────────────────────────────────────────────────────────────┤
│  [Complete Sale]  [Payment Methods]  [Hold Sale]  [Cancel]  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Key Components

#### Search/Barcode Input
```jsx
<div className="search-bar">
  <input
    type="text"
    placeholder="Scan barcode or search (₹, Name)"
    autoFocus
    onChange={handleSearch}
    onKeyDown={handleBarcodeEntry}
  />
  {/* Auto-add when barcode scanned */}
</div>
```

**Behavior:**
- Auto-focus on page load (cashier doesn't need to click)
- Barcode scanned → product auto-added to cart
- Pause barcode scanning during manual search
- Search by: name, barcode, or SKU

#### Product List (Scrollable)
```jsx
<div className="product-list">
  {products.map(product => (
    <ProductCard
      product={product}
      onAdd={() => addToCart(product)}
      onDetails={() => showProductDetails(product)}
    />
  ))}
  
  {/* Pagination at bottom */}
  <Pagination
    page={page}
    totalPages={totalPages}
    onPrevious={() => setPage(page - 1)}
    onNext={() => setPage(page + 1)}
  />
</div>
```

#### Shopping Cart (Right Side)
```jsx
<div className="cart">
  <div className="cart-items">
    {cartItems.map(item => (
      <CartItem
        item={item}
        onQtyChange={(qty) => updateCartQty(item.id, qty)}
        onRemove={() => removeFromCart(item.id)}
      />
    ))}
  </div>
  
  <div className="cart-summary">
    <div className="subtotal">Subtotal: ₹{subtotal.toLocaleString('en-IN')}</div>
    <div className="discount">Discount: -₹{discount.toLocaleString('en-IN')}</div>
    <div className="gst">GST (18%): ₹{gst.toLocaleString('en-IN')}</div>
    <div className="total">TOTAL: ₹{total.toLocaleString('en-IN')}</div>
  </div>
  
  <button onClick={appliedDiscount} className="btn-discount">
    Apply Discount
  </button>
  <button onClick={completeSale} className="btn-primary">
    Complete Sale
  </button>
</div>
```

### 1.3 User Workflows

#### Workflow 1: Add Item via Barcode
```
1. Barcode scanner plugged in
2. Cashier scans product barcode
3. System reads barcode from input field
4. Auto-search for product by barcode
5. Product found → auto-add to cart
6. Qty incremented if already in cart
7. UI shows "Added: Milk ×2" (toast notification)
```

**Implementation:**
```javascript
const handleBarcodeEntry = (e) => {
  if (e.key === 'Enter') {
    const barcode = e.target.value.trim();
    
    if (!barcode) return;
    
    // Search product by barcode
    const product = products.find(p => p.barcode === barcode);
    
    if (product) {
      addToCart(product);
      e.target.value = '';  // Clear input for next scan
      showToast(`✅ Added: ${product.name} ×${cartItems[product.id]?.qty || 1}`);
    } else {
      showToast(`❌ Product not found`);
    }
  }
};
```

#### Workflow 2: Manual Search & Add
```
1. Cashier types "milk" in search
2. System shows matching products (real-time)
3. Cashier clicks "Quick Add" or selects quantity
4. Product added to cart
5. Cashier continues scanning/searching
```

#### Workflow 3: Apply Discount
```
1. Cashier enters all items
2. Clicks "Apply Discount"
3. Dialog opens: [Discount Type] [Amount]
4. Options: Flat ₹ amount, % discount, Coupon code
5. Discount applied to cart total
6. GST recalculated
```

#### Workflow 4: Complete Sale & Payment
```
1. Cashier clicks "Complete Sale"
2. Dialog: [Payment Method Selection]
3. Options: Cash, UPI, Card, Khata (credit)
4. Cashier selects payment method
5. If UPI/Card: show QR code or terminal prompt
6. Payment confirmed
7. Invoice created
8. Receipt printed automatically
9. Option to send receipt via WhatsApp
10. Cart cleared, ready for next customer
```

---

## 2. BACKEND: POS ENDPOINTS

### 2.1 Sales Endpoints

#### Endpoint 1: Create Sale
```
POST /api/v1/sales/create
```

**Request:**
```json
{
  "items": [
    {
      "product_id": 1,
      "quantity": 2,
      "price": 50,      // Price at time of sale (may differ from current)
      "discount": 0
    },
    {
      "product_id": 5,
      "quantity": 1,
      "price": 25,
      "discount": 5
    }
  ],
  "discount_total": 5,      // Cart-level discount
  "payment_method": "cash",  // Options: cash, upi, card, khata
  "notes": "Customer requested extra packaging"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "sale_id": "SALE-2026-02-14-001",
    "customer_id": null,         // Optional if customer not identified
    "items_count": 3,
    "subtotal": 125,
    "discount": 5,
    "gst": 21.6,
    "total": 141.6,
    "payment_method": "cash",
    "status": "completed",
    "timestamp": "2026-02-14T13:45:00Z",
    "receipt_number": "RCP-001",
    "invoice_id": null           // Generated later if needed
  },
  "message": "Sale created successfully"
}
```

**Business Logic:**
```python
# api/services/pos.py

@log_operation("CREATE_SALE")
async def create_sale(sale_data: SaleCreate, db: Session) -> Sale:
    """Create a new POS sale transaction"""
    
    try:
        # Step 1: Validate items exist and have stock
        for item in sale_data.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                raise ValueError(f"Product {item.product_id} not found")
            if product.stock_qty < item.quantity:
                raise ValueError(f"Insufficient stock: {product.name}")
        
        # Step 2: Create sale record
        sale = Sale(
            sale_date=datetime.utcnow(),
            total_amount=0,  # Will calculate below
            payment_method=sale_data.payment_method,
            status="completed"
        )
        db.add(sale)
        db.flush()  # Get sale ID
        
        # Step 3: Create sale items & update inventory
        subtotal = 0
        for item_data in sale_data.items:
            product = db.query(Product).filter(Product.id == item_data.product_id).first()
            
            # Create sale item
            item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                quantity=item_data.quantity,
                price=item_data.price,
                discount=item_data.discount or 0,
                amount=item_data.price * item_data.quantity - (item_data.discount or 0)
            )
            db.add(item)
            
            # Update inventory
            product.stock_qty -= item_data.quantity
            product.last_sale_date = datetime.utcnow()
            db.add(product)
            
            subtotal += item.amount
        
        # Step 4: Calculate tax
        tax_rate = 0.18  # 18% GST
        total_tax = subtotal * tax_rate
        total_amount = subtotal + total_tax - (sale_data.discount_total or 0)
        
        # Step 5: Update sale with final amount
        sale.total_amount = total_amount
        sale.tax_amount = total_tax
        sale.discount_amount = sale_data.discount_total or 0
        
        db.commit()
        db.refresh(sale)
        
        logger.info(f"Sale created: {sale.id}, amount: {total_amount}")
        
        return sale
        
    except Exception as e:
        db.rollback()
        logger.error(f"Sale creation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
```

---

#### Endpoint 2: Get Sale Details
```
GET /api/v1/sales/{sale_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "SALE-2026-02-14-001",
    "items": [
      {"product_name": "Milk", "qty": 2, "price": 50, "total": 100},
      {"product_name": "Tea", "qty": 1, "price": 25, "total": 25}
    ],
    "subtotal": 125,
    "gst": 22.5,
    "discount": 0,
    "total": 147.5,
    "payment_method": "cash",
    "status": "completed",
    "receipt_url": "/receipts/RCP-001.pdf"
  }
}
```

---

#### Endpoint 3: List Recent Sales
```
GET /api/v1/sales?page=1&per_page=50
```

**Used For:** Dashboard, sales history, reconciliation

---

### 2.2 Payment Endpoints

#### Endpoint 1: Process Payment
```
POST /api/v1/payments/process
```

**Request:**
```json
{
  "sale_id": "SALE-2026-02-14-001",
  "amount": 147.5,
  "payment_method": "upi",
  "payment_details": {
    "upi_id": "user@phone",
    "transaction_id": "UPI123456789"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "transaction_id": "TXN-2026-02-14-001",
    "status": "success",
    "amount": 147.5,
    "timestamp": "2026-02-14T13:45:30Z"
  }
}
```

---

### 2.3 Receipt Endpoints

#### Endpoint 1: Generate Receipt (ESC/POS)
```
POST /api/v1/receipts/generate
```

**Request:**
```json
{
  "sale_id": "SALE-2026-02-14-001",
  "format": "escpos",  // Options: escpos, pdf, text
  "printer_width": 58  // Options: 58mm, 80mm
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "receipt_id": "RCP-001",
    "escpos_commands": "ESC...@...",  // Raw ESC/POS commands
    "file_url": "/receipts/RCP-001.pdf"
  }
}
```

**ESC/POS Format (58mm thermal printer):**
```python
def generate_escpos_receipt(sale: Sale, printer_width=58) -> str:
    """Generate ESC/POS commands for thermal receipt printer"""
    
    commands = ""
    
    # Initialize printer
    commands += "\x1B\x40"  # ESC @ - Reset printer
    
    # Header
    commands += f"{sale.store_name.center(32)}\n"
    commands += f"{'Date: ' + sale.timestamp.strftime('%d/%m/%Y %H:%M')}\n"
    commands += "-" * 32 + "\n"
    
    # Items
    commands += "Item               Qty  Price  Total\n"
    commands += "-" * 32 + "\n"
    
    for item in sale.items:
        item_line = f"{item.product_name[:15]:<15} {item.qty:>3} ₹{item.price:>5} ₹{item.amount:>6}\n"
        commands += item_line
    
    # Summary
    commands += "-" * 32 + "\n"
    commands += f"Subtotal:              ₹{sale.subtotal:>7.2f}\n"
    commands += f"Discount:              ₹{sale.discount:>7.2f}\n"
    commands += f"GST (18%):             ₹{sale.gst:>7.2f}\n"
    commands += "=" * 32 + "\n"
    commands += f"TOTAL:                 ₹{sale.total:>7.2f}\n"
    
    # Footer
    commands += f"Payment: {sale.payment_method.upper()}\n"
    commands += f"Thank you! Visit again.\n"
    commands += f"Receipt #: {sale.receipt_number}\n"
    
    # Cut paper
    commands += "\x1D\x56\x00"  # GS V 0 - Cut paper
    
    return commands
```

---

#### Endpoint 2: Send Receipt via WhatsApp
```
POST /api/v1/receipts/send-whatsapp
```

**Request:**
```json
{
  "sale_id": "SALE-2026-02-14-001",
  "customer_phone": "+919876543210"  // India format: +91...
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message_id": "WHATSAPP-MSG-123",
    "status": "sent",
    "customer_phone": "+919876543210"
  }
}
```

**WhatsApp Message Format:**
```
Hii! 👋
Your receipt from R-DIOS Store

📦 Milk ×2 = ₹100
📦 Tea ×1 = ₹25

Subtotal: ₹125
GST: ₹22.5
TOTAL: ₹147.5

Payment: Cash ✅

Thank you! 🙏
Receipt #: RCP-001
Time: 13:45
Date: 14/02/2026
```

---

## 3. OFFLINE MODE

### 3.1 Offline Transaction Queue

**Scenario:** Cashier starts sale, internet goes down mid-transaction

**Solution:** Store transactions locally using IndexedDB, sync when online

```javascript
// src/services/offlineQueue.js

class OfflineQueue {
  async add(transaction) {
    // Store in IndexedDB
    const db = await this.openDB();
    const tx = db.transaction('transactions', 'readwrite');
    await tx.objectStore('transactions').add(transaction);
  }
  
  async getAll() {
    // Retrieve all queued transactions
    const db = await this.openDB();
    const tx = db.transaction('transactions', 'readonly');
    return await tx.objectStore('transactions').getAll();
  }
  
  async sync() {
    // Sync all queued transactions when online
    const transactions = await this.getAll();
    
    for (const txn of transactions) {
      try {
        await api.post('/api/v1/sales/create', txn);
        await this.remove(txn.id);  // Remove from queue after sync
      } catch (error) {
        logger.error(`Failed to sync transaction ${txn.id}`, error);
      }
    }
  }
}
```

---

## 4. INTEGRATION TESTS

```python
# tests/test_pos_integration.py

def test_complete_pos_workflow():
    """Test end-to-end POS workflow"""
    
    # Step 1: Create sale
    sale_response = client.post("/api/v1/sales/create", json={
        "items": [
            {"product_id": 1, "quantity": 2, "price": 50}
        ],
        "payment_method": "cash"
    })
    assert sale_response.status_code == 201
    sale_id = sale_response.json()["data"]["sale_id"]
    
    # Step 2: Process payment
    payment_response = client.post("/api/v1/payments/process", json={
        "sale_id": sale_id,
        "amount": 118,
        "payment_method": "cash"
    })
    assert payment_response.status_code == 200
    
    # Step 3: Generate receipt
    receipt_response = client.post("/api/v1/receipts/generate", json={
        "sale_id": sale_id,
        "format": "escpos"
    })
    assert receipt_response.status_code == 200
    assert "escpos_commands" in receipt_response.json()["data"]
    
    # Step 4: Verify inventory updated
    inventory = client.get("/api/v1/inventory/list?page=1")
    product = next(p for p in inventory.json()["data"] if p["id"] == 1)
    assert product["stock_qty"] == initial_qty - 2
    
    print("✅ Complete POS workflow test passed")
```

---

## 5. SUCCESS CRITERIA

**Phase 1 = SUCCESS when:**

```
✅ Cashier can scan barcode → item auto-added to cart
✅ Cashier can manually search and add items
✅ Cart shows real-time totals with GST calculation
✅ Discount application works correctly
✅ Payment processed successfully
✅ Receipt printed on thermal printer
✅ Receipt sent via WhatsApp
✅ Offline mode queues transactions
✅ Integration tests 100% pass
✅ Performance: <2 seconds per operation
✅ Zero transaction loss even if internet fails
```

---

## 6. TIMELINE

```
WEEK 1 (Days 1-5):
├─ Day 1: Design + API specs
├─ Day 2: Backend endpoints implementation
├─ Day 3: Frontend page implementation
├─ Day 4: Payment integration
└─ Day 5: Testing + bug fixes

WEEK 2 (Days 6-10):
├─ Day 6: Thermal receipt implementation
├─ Day 7: WhatsApp integration
├─ Day 8: Offline mode implementation
├─ Day 9: Integration testing
└─ Day 10: Performance optimization + go-live readiness
```

---

*Phase 1 POS System Specification  
Ready for Development Team  
Proceed after Phase 0 gate approval*
