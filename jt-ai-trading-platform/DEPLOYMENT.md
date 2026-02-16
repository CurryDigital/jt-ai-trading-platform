# Deployment Guide - JT AI Trading Platform

**Environment**: AWS EC2 (Ubuntu) + Cloudflare SSL  
**Domain**: https://trade.jtcml.com  
**Last Updated**: 2026-02-16

---

## Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| Ubuntu | 22.04+ | OS |
| Python | 3.12 | Backend runtime |
| Node.js | 20+ | Frontend build |
| Nginx | Latest | Reverse proxy + SSL |
| PostgreSQL | 15+ | RDS database |

---

## Environment Variables

Copy `.env.template` to `.env` and fill in values:

```bash
cp backend/.env.template backend/.env
```

### Required Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `AZURE_OPENAI_API_KEY` | Azure Portal | OpenAI service API key |
| `AZURE_OPENAI_ENDPOINT` | Azure Portal | Endpoint URL (e.g., `https://<resource>.openai.azure.com/`) |
| `AZURE_OPENAI_DEPLOYMENT` | Azure Portal | Model deployment name |
| `AZURE_OPENAI_API_VERSION` | Azure Docs | API version (e.g., `2025-03-01-preview`) |
| `SERPER_API_KEY` | Serper.dev | Google search API key |

---

## SSL Certificates (Cloudflare)

### 1. Generate Origin Certificate
- Cloudflare Dashboard → SSL/TLS → Origin Server → Create Certificate
- Save as:
  - `certs/trade_jtcml_cert.pem`
  - `certs/trade_jtcml_key.pem`

### 2. Set Permissions
```bash
chmod 600 certs/*.pem
```

### 3. Nginx Configuration
Located at: `/etc/nginx/sites-enabled/trade.jtcml.com`

---

## Installation Steps

### 1. System Dependencies
```bash
sudo apt-get update
sudo apt-get install -y nginx python3-pip nodejs npm
```

### 2. Python Dependencies
```bash
cd backend
pip3 install -r requirements.txt --break-system-packages
# OR use virtual environment (recommended for production)
```

### 3. Frontend Build
```bash
cd frontend
npm install
npm run build
```

### 4. Database Setup
```bash
# Run DDL scripts from db_setup/
psql -h <RDS_ENDPOINT> -U <USER> -d aitrading -f db_setup/INITIAL_RDS_DDL.sql
```

### 5. Nginx Setup
```bash
sudo cp nginx.conf /etc/nginx/sites-available/trade.jtcml.com
sudo ln -sf /etc/nginx/sites-available/trade.jtcml.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. Start Backend
```bash
cd backend
source .env  # Load environment variables
./start.sh   # Or: python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

---

## Service Management

### Check Status
```bash
# Nginx
sudo systemctl status nginx

# Backend
pgrep -f uvicorn

# All ports
ss -tlnp | grep -E '(80|443|8000)'
```

### Restart Services
```bash
# Restart nginx
sudo systemctl reload nginx

# Restart backend
pkill -f uvicorn
cd backend && ./start.sh
```

---

## Troubleshooting

### Backend Won't Start
```bash
# Check logs
tail -50 backend/backend.log

# Verify env vars are set
echo $AZURE_OPENAI_API_KEY

# Test import
python3 -c "from app.main import app; print('OK')"
```

### SSL Issues
```bash
# Test nginx config
sudo nginx -t

# Check certificate paths
ls -la certs/

# Verify permissions
stat certs/*.pem
```

### Database Connection
```bash
# Test RDS connectivity
psql -h openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com \
     -U openclaw_user -d aitrading -c "SELECT 1"
```

### 500 Internal Server Error

**Symptom**: Website shows "500 Internal Server Error nginx/1.24.0"

**Check nginx error log**:
```bash
sudo tail -50 /var/log/nginx/trade.jtcml.com.error.log
```

**Common causes and fixes**:

#### 1. Permission Denied on Frontend Files
**Error**: `stat() "/path/to/frontend/dist/index.html" failed (13: Permission denied)`

**Fix**:
```bash
# Change ownership to nginx user (www-data)
sudo chown -R www-data:www-data /home/ubuntu/.openclaw/workspace/jt-ai-trading-platform/frontend/dist/
sudo chmod -R 755 /home/ubuntu/.openclaw/workspace/jt-ai-trading-platform/frontend/dist/

# Ensure nginx can traverse the path
sudo chmod 755 /home/ubuntu/
sudo chmod 755 /home/ubuntu/.openclaw/
sudo chmod 755 /home/ubuntu/.openclaw/workspace/
```

#### 2. API Routes Returning 404
**Error**: `/api/*` requests return 404 instead of hitting backend

**Cause**: Incorrect `proxy_pass` configuration strips the `/api/` prefix

**Fix** in `nginx.conf`:
```nginx
# WRONG - strips /api/
proxy_pass http://127.0.0.1:8000/;

# CORRECT - preserves /api/
proxy_pass http://127.0.0.1:8000/api/;
```

#### 3. Internal Redirection Cycle
**Error**: `rewrite or internal redirection cycle while internally redirecting to "/index.html"`

**Cause**: Frontend `try_files` catching API requests

**Fix**: Ensure API location blocks are defined BEFORE the frontend location block in nginx config:
```nginx
# API routes first
location /api/ { ... }
location /v1/api/ { ... }

# Frontend last (catch-all)
location / { ... }
```

### Testing the Fix
```bash
# Test local backend
curl http://127.0.0.1:8000/api/signals/1

# Test through nginx (localhost)
curl -k https://127.0.0.1/api/signals/1

# Test full chain
curl -k https://trade.jtcml.com/api/signals/1
```

---

## Security Checklist

- [ ] SSL certificates have 600 permissions
- [ ] `.env` file is gitignored
- [ ] `certs/` directory is gitignored
- [ ] Nginx configured with security headers
- [ ] Database uses IAM auth (not hardcoded password)
- [ ] UFW/firewall enabled (ports 22, 80, 443 only)

---

## File Locations

| Component | Path |
|-----------|------|
| SSL Certs | `jt-ai-trading-platform/certs/` |
| Env File | `jt-ai-trading-platform/backend/.env` |
| Nginx Config | `/etc/nginx/sites-enabled/trade.jtcml.com` |
| Frontend Build | `jt-ai-trading-platform/frontend/dist/` |
| Backend Logs | `jt-ai-trading-platform/backend/backend.log` |
| Systemd Service | `/etc/systemd/system/trading-platform.service` (optional) |

---

## Production Considerations

1. **Use systemd** for process management instead of nohup
2. **Set up log rotation** with logrotate
3. **Enable Cloudflare proxy** (orange cloud) after testing
4. **Configure automated backups** for RDS
5. **Set up monitoring** (CloudWatch, Prometheus, etc.)

---

*End of Deployment Guide*
