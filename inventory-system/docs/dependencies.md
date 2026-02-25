# Dependencies Map - Tang Inventory System

## File-to-Dependency Mapping

```
Legend:
  → : Depends on (downstream)
  ← : Used by (upstream)
```

### Infrastructure Layer

| File | Responsibility | Depends On | Used By |
|------|---------------|------------|---------|
| `docker-compose.yml` | Service orchestration | `.env` | Deployment |
| `.env` | Configuration | - | `docker-compose.yml`, `backend/src/config/database.js` |
| `scripts/check-ports.sh` | Port conflict detection | - | Manual execution |

### Backend Layer

| File | Responsibility | Depends On | Used By |
|------|---------------|------------|---------|
| `backend/package.json` | Dependency manifest | - | Build process |
| `backend/Dockerfile` | Container build | `package.json` | `docker-compose.yml` |
| `backend/src/app.js` | Express app entry | `config/database.js`, `routes/*` | `Dockerfile` CMD |
| `backend/src/config/database.js` | DB connection | `.env` | All models |
| `backend/src/models/Product.js` | Product entity | `config/database.js` | `routes/products.js`, `services/fifoValuation.js` |
| `backend/src/models/InventoryLevel.js` | Stock levels | `config/database.js`, `Product.js` | `routes/inventory.js`, `services/lowStockAlert.js` |
| `backend/src/models/StockLedger.js` | Audit trail | `config/database.js` | `routes/ledger.js`, `services/stockMovement.js` |
| `backend/src/models/Location.js` | Warehouse entity | `config/database.js` | `models/InventoryLevel.js` |
| `backend/src/models/FIFOLayer.js` | Cost tracking | `config/database.js`, `Product.js` | `services/fifoValuation.js` |
| `backend/src/routes/products.js` | Product CRUD API | `models/Product.js` | `app.js` |
| `backend/src/routes/inventory.js` | Stock movement API | `models/InventoryLevel.js`, `services/stockMovement.js` | `app.js` |
| `backend/src/routes/alerts.js` | Alert API | `services/lowStockAlert.js` | `app.js` |
| `backend/src/routes/ledger.js` | Audit API | `models/StockLedger.js` | `app.js` |
| `backend/src/services/fifoValuation.js` | FIFO logic | `models/FIFOLayer.js`, `models/InventoryLevel.js` | `routes/inventory.js` |
| `backend/src/services/lowStockAlert.js` | 15% threshold logic | `models/InventoryLevel.js`, `models/Product.js` | `routes/alerts.js`, Cron job |
| `backend/src/services/stockMovement.js` | Movement orchestration | `models/StockLedger.js`, `models/InventoryLevel.js`, `services/fifoValuation.js` | `routes/inventory.js` |
| `backend/migrations/001_initial_schema.sql` | DB schema | - | `docker-compose.yml` init |

### Frontend Layer

| File | Responsibility | Depends On | Used By |
|------|---------------|------------|---------|
| `frontend/package.json` | Dependency manifest | - | Build process |
| `frontend/Dockerfile` | Container build | `package.json`, `next.config.js` | `docker-compose.yml` |
| `frontend/next.config.js` | Next.js config | `.env` | `Dockerfile` |
| `frontend/src/app/layout.js` | Root layout | - | All pages |
| `frontend/src/app/page.js` | Dashboard | API: `/api/alerts`, `/api/inventory/summary` | User |
| `frontend/src/app/inventory/page.js` | Inventory view | API: `/api/inventory` | User |
| `frontend/src/app/products/page.js` | Product catalog | API: `/api/products` | User |
| `frontend/src/components/AlertPanel.js` | Alert display | `page.js` | User |
| `frontend/src/components/InventoryTable.js` | Stock grid | `app/inventory/page.js` | User |
| `frontend/src/components/MovementForm.js` | Stock in/out form | `app/inventory/page.js` | User |
| `frontend/src/lib/api.js` | API client | `.env` | All components |

### Documentation Layer

| File | Responsibility | Depends On | Used By |
|------|---------------|------------|---------|
| `README.md` | Setup guide | - | Users |
| `docs/user-stories.md` | Business requirements | - | Development |
| `docs/architecture.md` | System design | - | Development |
| `docs/decisions.md` | ADR log | - | Maintenance |
| `memory.md` | Project state | All files | Development |

---

## External Dependencies

### Production Runtime

| Package | Version | Purpose |
|---------|---------|---------|
| PostgreSQL | 15 | Primary database |
| Node.js | 20 LTS | Runtime |
| nginx (existing) | - | Reverse proxy on 80/443 |

### Backend NPM Dependencies

| Package | Purpose |
|---------|---------|
| express | Web framework |
| sequelize | ORM for PostgreSQL |
| pg | PostgreSQL driver |
| dotenv | Environment loading |
| cors | Cross-origin requests |
| helmet | Security headers |
| express-validator | Input validation |

### Frontend NPM Dependencies

| Package | Purpose |
|---------|---------|
| next | React framework |
| react | UI library |
| react-dom | DOM renderer |
| axios | HTTP client |
| tailwindcss | Styling |
| @headlessui/react | Accessible components |

---

## Dependency Graph (Simplified)

```
┌─────────────────────────────────────────────────────────┐
│                      User/Browser                        │
└─────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │  Dashboard │  │ Inventory  │  │  Products  │
    │   (8081)   │  │   (8081)   │  │   (8081)   │
    └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
          │               │               │
          └───────────────┼───────────────┘
                          ▼ HTTP
    ┌─────────────────────────────────────────────────┐
    │            Express API (3001)                    │
    │  ┌─────────┐ ┌─────────┐ ┌─────────┐            │
    │  │/products│ │/inventory│ │ /alerts │            │
    │  └────┬────┘ └────┬────┘ └────┬────┘            │
    └───────┼───────────┼───────────┼─────────────────┘
            │           │           │
            └───────────┼───────────┘
                        ▼ SQL
    ┌─────────────────────────────────────────────────┐
    │           PostgreSQL (5433)                      │
    │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
    │  │products│ │inventory│ │ ledger │ │  fifo  │   │
    │  └────────┘ └────────┘ └────────┘ └────────┘   │
    └─────────────────────────────────────────────────┘
```
