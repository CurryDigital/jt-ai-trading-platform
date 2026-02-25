# User Stories - Tang Inventory System

## Persona 1: Warehouse Manager (Alex)

### US-WM-001: View Multi-Location Inventory
**As a** Warehouse Manager  
**I want** to see current stock levels across all warehouse locations  
**So that** I can quickly identify where stock is located and make informed transfer decisions

**Acceptance Criteria:**
- Dashboard shows inventory levels grouped by location
- Real-time quantity updates after stock movements
- Filter by product category and location
- Color-coded indicators for low/reorder points

---

### US-WM-002: Process Stock Movements
**As a** Warehouse Manager  
**I want** to record stock in, out, and transfers between locations  
**So that** the system accurately reflects physical inventory changes

**Acceptance Criteria:**
- Movement types: RECEIPT, ISSUE, TRANSFER, ADJUSTMENT
- Transfer requires source and destination locations
- System validates sufficient stock before ISSUE/TRANSFER
- Each movement is timestamped with user attribution
- Stock ledger auto-updates for audit trail

---

### US-WM-003: Monitor Low Stock Alerts
**As a** Warehouse Manager  
**I want** to receive alerts when inventory falls below 15% of reorder point  
**So that** I can proactively reorder before stockouts occur

**Acceptance Criteria:**
- Alert triggers when: `current_quantity <= reorder_point * 0.15`
- Alerts appear on dashboard with product details
- Alerts can be acknowledged/dismissed
- Historical alert log maintained

---

### US-WM-004: Review Stock Ledger
**As a** Warehouse Manager  
**I want** to view a complete audit trail of all stock movements  
**So that** I can trace discrepancies and maintain accountability

**Acceptance Criteria:**
- Immutable ledger records: date, product, quantity, movement type, user, reason
- Filterable by date range, product, location
- Export to CSV/PDF for reporting
- Ledger entries cannot be modified or deleted

---

## Persona 2: Purchasing Clerk (Sarah)

### US-PC-001: View Low Stock Alerts
**As a** Purchasing Clerk  
**I want** to see all products below the 15% reorder threshold  
**So that** I can generate purchase orders for replenishment

**Acceptance Criteria:**
- Priority-ranked list of low stock items
- Shows current quantity vs reorder point vs max stock
- Suggests order quantity: `max_stock - current_quantity`
- One-click create purchase order

---

### US-PC-002: Receive Incoming Stock
**As a** Purchasing Clerk  
**I want** to record received inventory with lot/batch numbers  
**So that** I can track FIFO valuation and expiry dates

**Acceptance Criteria:**
- Record: product, quantity, unit cost, lot number, expiry date (if applicable)
- System assigns FIFO layer based on receipt date
- Auto-updates inventory levels at receiving location
- Creates STOCK_LEDGER entry for audit trail

---

### US-PC-003: FIFO Cost Valuation
**As a** Purchasing Clerk  
**I want** the system to automatically apply FIFO costing  
**So that** inventory valuation reflects actual purchase costs

**Acceptance Criteria:**
- Cost assigned based on oldest stock first
- System tracks cost layers per lot/batch
- When issuing stock, oldest cost layer is consumed first
- Inventory valuation report shows current value by cost layer

---

### US-PC-004: Manage Product Catalog
**As a** Purchasing Clerk  
**I want** to maintain the product master data  
**So that** new products can be added to inventory tracking

**Acceptance Criteria:**
- Create/edit product: SKU, name, category, unit of measure
- Set reorder point and max stock levels
- Assign default warehouse location
- Soft delete (archive) discontinued products

---

## Process Flows

### Stock Receipt Process (Sarah → Alex)
```
1. Sarah receives PO delivery
2. Sarah records: product, qty, cost, lot#, expiry
3. System: Creates FIFO cost layer
4. System: Updates inventory_levels
5. System: Writes to stock_ledger
6. Alex notified of receipt at warehouse
```

### Stock Issue Process (Alex)
```
1. Alex receives pick request
2. Alex records: product, qty, destination, reason
3. System: Validates sufficient stock
4. System: Applies FIFO cost to issue
5. System: Updates inventory_levels
6. System: Writes to stock_ledger
```

### Low Stock Alert → Purchase Order
```
1. System detects: current_qty <= reorder_point * 0.15
2. System creates low stock alert
3. Sarah views prioritized alert list
4. Sarah generates PO for suggested qty
5. Sarah sends PO to supplier
```
