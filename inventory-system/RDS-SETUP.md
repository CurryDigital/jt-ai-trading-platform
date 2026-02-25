# RDS Configuration Summary

## Database Endpoint
```
openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com:5432
```

## Database Name
```
tang_inventory
```

## Updated Configuration Files

### 1. `.env`
- Set `DB_HOST` to RDS endpoint
- Set `DB_PASSWORD` to your RDS master password (⚠️ must be changed)
- Set `DB_SSL=true` for encrypted connection

### 2. `docker-compose.yml`
- Removed local PostgreSQL container
- Backend now connects directly to RDS
- Added healthcheck for backend service

### 3. `scripts/setup-rds-db.sh`
- Creates `tang_inventory` database on RDS if it doesn't exist
- Usage: `DB_PASSWORD=your_pass ./scripts/setup-rds-db.sh`

## Setup Steps

```bash
cd /home/ubuntu/.openclaw/workspace/inventory-system

# 1. Edit .env with your RDS password
nano .env
# Change: DB_PASSWORD=CHANGE_ME  →  DB_PASSWORD=your_actual_password

# 2. Create database on RDS
DB_PASSWORD=your_password ./scripts/setup-rds-db.sh

# 3. Verify ports
./scripts/check-ports.sh

# 4. Start services
docker-compose up -d

# 5. Check logs
docker-compose logs -f backend
```

## Verification

Test the connection manually:
```bash
psql -h openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com \
     -U postgres -d tang_inventory
```

Check backend health:
```bash
curl http://localhost:3001/health
```

## Security Notes

- `.env` is gitignored — never commit credentials
- RDS uses SSL encryption (DB_SSL=true)
- Security group must allow port 5432 from EC2 instance
