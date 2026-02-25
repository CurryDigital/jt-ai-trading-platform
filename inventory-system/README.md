# Tang Inventory System

A production-ready Inventory Management System built with Node.js/Express, Next.js, and PostgreSQL.

---

## ⚠️ Port Verification (CRITICAL)

Before starting containers, verify these ports are free:

```bash
# Check if ports are in use
sudo netstat -tlnp | grep -E ':(3001|8081)'
# OR
sudo ss -tlnp | grep -E ':(3001|8081)'
```

**Expected:** No output = ports available ✅  
**If output shows:** Address already in use → Change ports in `.env` before proceeding

### Current Port Mapping
| Service | Host Port | Container Port |
|---------|-----------|----------------|
| Backend API | 3001 | 3000 |
| Frontend | 8081 | 3000 |

**Existing services to avoid:**
- nginx: 80, 443
- openclaw-gateway: 18789, 18792

---

## Quick Start (AWS RDS)

This project uses **AWS RDS PostgreSQL** at `openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com`.

### 1. Set RDS Password

Edit `.env` and set your RDS master password:

```bash
DB_PASSWORD=your_actual_rds_password
```

### 2. Create Database on RDS

```bash
# Run the database creation script
DB_PASSWORD=your_rds_password ./scripts/setup-rds-db.sh
```

This creates the `tang_inventory` database on RDS.

### 3. Verify Ports

```bash
./scripts/check-ports.sh
```

### 4. Start Services

```bash
docker-compose up -d
```

The backend will automatically:
- Connect to RDS PostgreSQL
- Run migrations to create tables
- Seed default locations (Main Warehouse, Retail Store, Virtual)

### 5. Access
- Frontend: http://localhost:8081
- API: http://localhost:3001
- Health Check: http://localhost:3001/health

---

## Troubleshooting

### RDS Connection Issues

**Error: `password authentication failed`**
- Verify `DB_PASSWORD` in `.env` matches your RDS master password
- Run: `DB_PASSWORD=your_pass ./scripts/setup-rds-db.sh` to test

**Error: `no pg_hba.conf entry`**
- The RDS security group must allow inbound PostgreSQL (5432) from your EC2 instance
- Check RDS Security Group rules in AWS Console

**Error: `Connection timeout`**
- Verify RDS instance is in `available` state
- Confirm EC2 and RDS are in the same VPC or have proper peering

### Port Conflicts

If ports 3001 or 8081 are in use:

```bash
# Edit .env and change ports
API_PORT=3002
FRONTEND_PORT=8082

# Then restart
docker-compose up -d
```

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────────────────┐
│   Next.js   │────▶│   Express   │────▶│  AWS RDS PostgreSQL         │
│  (Port 8081)│     │  (Port 3001)│     │  openclaw.cjs04usueagu...   │
└─────────────┘     └─────────────┘     └─────────────────────────────┘
                                                   │
                                              tang_inventory
                                              ├── product_catalog
                                              ├── inventory_levels
                                              ├── stock_ledger
                                              ├── fifo_layers
                                              └── locations
```

---

## User Roles

### Warehouse Manager
- View multi-location inventory levels
- Process stock movements (in/out/transfers)
- Monitor low stock alerts
- Review stock ledger audit trail

### Purchasing Clerk
- View low stock alerts (15% threshold)
- Create purchase orders based on reorder points
- Receive incoming stock
- Update inventory levels with FIFO costing

---

## Database Schema

### Core Tables
- `product_catalog` — Master product data with soft delete
- `locations` — Warehouse/storage locations
- `inventory_levels` — Per-location stock quantities (composite key: product+location)
- `stock_ledger` — Immutable audit trail of all movements
- `fifo_layers` — Cost tracking for FIFO valuation
- `stock_movements` — Movement transaction records

### Business Logic
- **Low Stock Alert:** `current_quantity <= reorder_point * 0.15`
- **FIFO Valuation:** Costs assigned based on oldest receipt date first

---

## Development Commands

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Database shell (RDS)
psql -h openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com \
     -U postgres -d tang_inventory

# Restart service
docker-compose restart backend
docker-compose restart frontend

# Stop all
docker-compose down
```

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/products` | List all products |
| `POST /api/products` | Create product |
| `GET /api/inventory` | List inventory levels |
| `POST /api/inventory/receive` | Receive stock (creates FIFO layer) |
| `POST /api/inventory/issue` | Issue stock (consumes FIFO) |
| `GET /api/alerts` | Low stock alerts |
| `GET /api/ledger` | Stock ledger audit trail |
| `GET /api/locations` | Warehouse locations |

---

## Files Modified

- `.env` — RDS connection config
- `docker-compose.yml` — Removed local PostgreSQL, uses RDS only
- `scripts/setup-rds-db.sh` — Database creation script
- `README.md` — This file
