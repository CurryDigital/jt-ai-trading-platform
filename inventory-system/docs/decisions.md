# Architecture Decision Records (ADR)

## ADR-001: Port Isolation Strategy

**Status:** Accepted  
**Date:** 2026-02-16  
**Context:** VM already hosts nginx (80/443) and openclaw-gateway (18789/18792)

**Decision:** 
Use non-standard ports: 5433 (DB), 3001 (API), 8081 (Frontend)

**Rationale:**
- Avoids conflicts with existing production nginx
- Predictable mapping: add 1 to default ports
- Documented in README with verification script
- Easy to change via .env if needed

**Consequences:**
- Users must specify port in URLs
- Extra documentation burden
- Trade-off: safety vs. convenience

---

## ADR-002: Database Choice (PostgreSQL)

**Status:** Accepted  
**Date:** 2026-02-16  
**Context:** Requirement for AWS RDS deployment, data integrity, FIFO tracking

**Decision:**
Use PostgreSQL 15 with Sequelize ORM

**Rationale:**
- AWS RDS native support
- ACID compliance for stock movements
- JSONB support for flexible metadata
- Excellent concurrency for inventory locks
- Sequelize provides migrations and model validation

**Alternatives Considered:**
- MySQL: Less robust transaction handling
- MongoDB: No ACID, harder to enforce FIFO
- SQLite: Not suitable for multi-user warehouse ops

**Consequences:**
- Requires PostgreSQL knowledge
- Sequelize abstraction overhead acceptable for productivity

---

## ADR-003: FIFO Valuation Implementation

**Status:** Accepted  
**Date:** 2026-02-16  
**Context:** Requirement for FIFO costing on stock issues

**Decision:**
Implement explicit FIFO layers table with consumption tracking

**Schema:**
```sql
fifo_layers:
  - id, product_id, lot_number, unit_cost, 
    quantity_received, quantity_remaining, received_date
```

**Algorithm:**
On stock issue:
1. Select layers for product ORDER BY received_date ASC
2. Consume from oldest layer until quantity fulfilled
3. Update layer.remaining_quantity
4. Record cost used in stock_ledger

**Rationale:**
- Transparent audit trail per layer
- Handles partial consumption cleanly
- Supports lot tracking for expiry
- Easy to report current inventory value

**Consequences:**
- Extra table maintenance
- Slightly more complex issue transactions
- Cannot delete/edit historical layers (enforced in code)

---

## ADR-004: Stock Ledger Immutability

**Status:** Accepted  
**Date:** 2026-02-16  
**Context:** Audit requirement, regulatory compliance

**Decision:**
Stock ledger is append-only; no UPDATE or DELETE allowed

**Implementation:**
- Database user has INSERT only on stock_ledger
- Application layer enforces no update/delete routes
- Use compensating transactions for reversals

**Rationale:**
- Audit compliance (SOX, ISO)
- Fraud prevention
- Data integrity for dispute resolution
- Industry standard for inventory systems

**Consequences:**
- Corrections require reversal entries
- Storage grows indefinitely (acceptable)
- Query patterns must handle large tables

---

## ADR-005: Low Stock Alert Threshold

**Status:** Accepted  
**Date:** 2026-02-16  
**Context:** Requirement for 15% threshold

**Decision:**
Alert triggers when: `current_quantity <= reorder_point * 0.15`

**Implementation:**
```javascript
const threshold = product.reorder_point * 0.15;
const isLowStock = inventory.current_quantity <= threshold;
```

**Rationale:**
- Business requirement specifies 15%
- Provides early warning before stockout
- Separate from reorder point (which triggers PO)

**Consequences:**
- False positives if reorder_point is set too high
- Requires periodic review of threshold appropriateness

---

## ADR-006: Docker vs Direct Deployment

**Status:** Accepted  
**Date:** 2026-02-16  
**Context:** VM already uses Docker for existing website

**Decision:**
Use Docker Compose for isolation and consistency

**Rationale:**
- Existing Docker infrastructure on VM
- Consistent environment across dev/prod
- Easy rollback via image tags
- Network isolation between services

**Consequences:**
- Additional resource overhead (acceptable)
- Docker learning curve for maintainers
- Image build time on first deploy

---

## ADR-007: Backend-Frontend Separation

**Status:** Accepted  
**Date:** 2026-02-16  
**Context:** Clean architecture, potential for mobile apps

**Decision:**
Separate Next.js frontend and Express backend as distinct services

**Rationale:**
- Clear API contract between layers
- Frontend can be replaced (mobile app, different framework)
- Backend can scale independently
- Team separation possible

**Consequences:**
- Network hop latency (minimal on same host)
- CORS configuration needed
- Two deployment artifacts

---

## ADR-008: Multi-Location Inventory Model

**Status:** Accepted  
**Date:** 2026-02-16  
**Context:** Warehouse Manager needs multi-location visibility

**Decision:**
Separate `inventory_levels` table with location_id + product_id composite context

**Schema:**
```sql
inventory_levels:
  - product_id (FK)
  - location_id (FK)
  - quantity
  - reserved_quantity
  - updated_at
```

**Rationale:**
- Normalized design avoids duplication
- Easy to add new locations
- Supports location-specific reorder points
- Transfer between locations = two movements

**Consequences:**
- Join required for product + location queries
- Must handle location lifecycle (open/close)

---

## ADR-009: Environment Configuration Strategy

**Status:** Accepted  
**Date:** 2026-02-16  
**Context:** Multiple environments (dev, staging, prod RDS)

**Decision:**
Single `.env` file pattern with documented variables

**Pattern:**
- `.env.example` committed with defaults
- `.env` created locally from example, gitignored
- Same variable names across environments
- Production values in AWS Secrets Manager (future)

**Rationale:**
- Simple mental model
- 12-Factor App compliance
- Easy to switch between Docker and RDS

**Consequences:**
- Security: .env must not be committed
- Production credentials need secure storage (future enhancement)
