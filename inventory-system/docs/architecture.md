# Architecture Documentation - Tang Inventory System

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Next.js 14 (Frontend)                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │   │
│  │  │  Dashboard  │  │  Inventory  │  │ Product Catalog │  │   │
│  │  │   (Port     │  │  Management │  │   Management    │  │   │
│  │  │    8081)    │  │             │  │                 │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTP/REST
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER (Express)                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Node.js 20 + Express.js                     │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │   │
│  │  │Products  │ │Inventory │ │  Alerts  │ │  Ledger    │  │   │
│  │  │  Routes  │ │  Routes  │ │  Routes  │ │  Routes    │  │   │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬──────┘  │   │
│  │       └─────────────┴────────────┴─────────────┘         │   │
│  │                         │                                │   │
│  │  ┌──────────────────────┴────────────────────────┐       │   │
│  │  │           Service Layer                        │       │   │
│  │  │  • FIFO Valuation Service                      │       │   │
│  │  │  • Low Stock Alert Service (15% threshold)     │       │   │
│  │  │  • Stock Movement Service                      │       │   │
│  │  └──────────────────────┬────────────────────────┘       │   │
│  │                         │                                │   │
│  │  ┌──────────────────────┴────────────────────────┐       │   │
│  │  │           Data Access Layer (Sequelize)        │       │   │
│  │  └──────────────────────┬────────────────────────┘       │   │
│  └─────────────────────────┼────────────────────────────────┘   │
└────────────────────────────┼────────────────────────────────────┘
                             │ SQL/TCP
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATA LAYER                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              PostgreSQL 15                               │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌────────────────┐   │   │
│  │  │   product_   │ │  inventory_  │ │  stock_ledger  │   │   │
│  │  │   catalog    │ │   levels     │ │                │   │   │
│  │  └──────────────┘ └──────────────┘ └────────────────┘   │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌────────────────┐   │   │
│  │  │   locations  │ │stock_movements│ │  fifo_layers   │   │   │
│  │  └──────────────┘ └──────────────┘ └────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

### Frontend (Next.js 14)
**Path:** `frontend/`  
**Port:** 8081 (host) → 3000 (container)

| Component | Responsibility | Upstream | Downstream |
|-----------|---------------|----------|------------|
| Dashboard | Executive overview, alerts | User | API: /alerts, /inventory/summary |
| Inventory | Stock movement UI, transfers | User | API: /inventory, /movements |
| Products | Catalog management | User | API: /products |
| Ledger | Audit trail view | User | API: /ledger |

### Backend (Express.js)
**Path:** `backend/`  
**Port:** 3001 (host) → 3000 (container)

| Component | Responsibility | Upstream | Downstream |
|-----------|---------------|----------|------------|
| Product Routes | CRUD for product_catalog | Frontend | Product Model |
| Inventory Routes | Stock levels, movements | Frontend | InventoryLevel Model, StockLedger Model |
| Alert Routes | Low stock detection (15%) | Frontend, Scheduler | InventoryLevel Model |
| Ledger Routes | Audit trail queries | Frontend | StockLedger Model |
| FIFO Service | Cost layer management | Inventory Routes | FIFO_Layers Model |
| Alert Service | Threshold checking | Background job | InventoryLevel Model, Notification |

### Database (PostgreSQL)
**Port:** 5433 (host) → 5432 (container)

| Table | Purpose | Keys | Relationships |
|-------|---------|------|---------------|
| product_catalog | Master product data | id (PK), sku (UK) | 1:N inventory_levels |
| inventory_levels | Per-location stock | id (PK), product_id, location_id | N:1 products, locations |
| stock_ledger | Immutable audit log | id (PK) | Records all movements |
| locations | Warehouse/Storage sites | id (PK) | 1:N inventory_levels |
| stock_movements | Transaction records | id (PK) | Creates ledger entries |
| fifo_layers | Cost tracking for FIFO | id (PK), product_id | N:1 products |

---

## Data Flow

### Stock Receipt (FIFO)
```
Frontend → POST /api/inventory/receive
    ↓
Backend: InventoryController.receiveStock()
    ├─→ Create stock_movement record
    ├─→ Create fifo_layer (lot, cost, qty, date)
    ├─→ Update inventory_levels.quantity (+)
    └─→ Insert stock_ledger entry (immutable)
    ↓
Database: ACID transaction committed
    ↓
Frontend: Refresh inventory view
```

### Stock Issue (FIFO)
```
Frontend → POST /api/inventory/issue
    ↓
Backend: InventoryController.issueStock()
    ├─→ Validate sufficient stock
    ├─→ FIFO Service: Allocate oldest cost layers
    ├─→ Create stock_movement record
    ├─→ Update inventory_levels.quantity (-)
    ├─→ Consume/Reduce fifo_layer quantities
    └─→ Insert stock_ledger entry
    ↓
Database: ACID transaction committed
    ↓
Frontend: Update UI with issued details
```

### Low Stock Alert
```
Scheduler → AlertService.checkLowStock()
    ├─→ Query: current_qty <= reorder_point * 0.15
    ├─→ Create alert_records for matches
    └─→ Notify subscribed users
    ↓
Frontend: Dashboard polls /api/alerts
    ↓
User: Views prioritized alert list
```

---

## Security & Constraints

### Port Isolation
- Frontend: **8081** (avoids 80/443 used by nginx)
- Backend: **3001** (avoids 3000 commonly used)
- Database: **5433** (avoids 5432 default)

### Data Integrity
- Stock ledger is **immutable** (append-only)
- All movements use database transactions
- Foreign key constraints enforce referential integrity
- Soft deletes for products (archive flag)

### FIFO Constraints
- Cannot issue more than available in cost layers
- Negative inventory not permitted
- Cost layers consumed oldest-first (by receipt_date)
