# PricePulse BD — Production Deployment & Operations Guide

This handbook provides production instructions for self-hosting **PricePulse BD** on any standard Linux VPS (Ubuntu 22.04/24.04, Debian 12, DigitalOcean Droplet, AWS EC2, or Hetzner).

---

## Architecture Overview

```
                      Internet / Clients
                     (Web Dashboard & Android)
                               │
                               ▼
                    [Nginx Reverse Proxy]
                     (Port 80/443 SSL SNI)
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │  Docker Container (pricepulse_bd_app)        │
        │  Port 8000: Uvicorn ASGI Runner (2 Workers)  │
        │                                              │
        │  ┌────────────────────┐ ┌──────────────────┐ │
        │  │ FastAPI REST API   │ │ React 18 SPA     │ │
        │  │ /api/v1/*          │ │ (Static Mount)   │ │
        │  └─────────┬──────────┘ └──────────────────┘ │
        │            │                                 │
        │            ▼                                 │
        │  SQLite 3 (WAL Mode, 5000ms Busy Timeout)   │
        │  Volume: /app/data/pricepulse.db             │
        └──────────────────────────────────────────────┘
```

---

## 1. Quick Start: Single-Command Docker Deployment

### Prerequisites
- Docker Engine 24.0+ & Docker Compose v2 installed.
- Git.

### Commands
```bash
# 1. Clone the production repository
git clone https://github.com/farhanshahriarpolok/PricePulse-BD.git
cd PricePulse-BD

# 2. Build and launch the containerized stack
docker compose up -d --build

# 3. Verify container liveness and healthcheck
docker compose ps
docker compose logs -f pricepulse-app
```

The container automatically:
- Builds the Vite React 18 production bundle inside Node 20.
- Boots FastAPI with 2 Uvicorn workers on port `8000`.
- Initializes the SQLite database at `/app/data/pricepulse.db` with WAL mode.
- Seeds all 65 canonical commodities, 64 districts, and 30-day baseline observations.

---

## 2. Nginx Reverse Proxy with Let's Encrypt SSL

### Step A: Install Nginx & Certbot
```bash
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx
```

### Step B: Configure Nginx Server Block
Create `/etc/nginx/sites-available/pricepulse`:
```nginx
server {
    server_name pricepulse.yourdomain.com;

    client_max_body_size 20M;

    # Gzip compression for high-performance React bundle delivery
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript image/svg+xml;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90s;
    }
}
```

### Step C: Enable Site & Issue SSL Certificate
```bash
sudo ln -s /etc/nginx/sites-available/pricepulse /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Issue automated Let's Encrypt certificate
sudo certbot --nginx -d pricepulse.yourdomain.com
```

---

## 3. Scheduled Daily Ingestion Setup

PricePulse BD collects daily morning agricultural bulletins from DAM, TCB, and retail storefronts. You can automate this via host cron or via the containerized worker profile.

### Option A: Via Docker Compose Worker Profile
```bash
# Run the continuous sync worker in the background
docker compose --profile worker up -d
```

### Option B: Via Host System Crontab
```bash
# Edit host crontab
crontab -e

# Run harvest every morning at 06:30 AM BST (00:30 UTC)
30 0 * * * docker exec pricepulse_bd_app python scripts/sync_daily_prices.py --all >> /var/log/pricepulse_sync.log 2>&1
```

---

## 4. SQLite Zero-Downtime Backup & Disaster Recovery

Because PricePulse BD uses SQLite WAL mode, database backups can be taken hot while transactions are actively executing:

```bash
# Create an atomic hot backup to host storage
docker exec pricepulse_bd_app sqlite3 /app/data/pricepulse.db ".backup '/app/data/backup_$(date +%Y%m%d).db'"

# Synchronize backup to remote off-site storage or S3
rsync -avz /var/lib/docker/volumes/pricepulse-bd_pricepulse_data/_data/backup_*.db user@backupserver:/backups/
```

---

## 5. Physical Android Device Sideloading (APK)

To build and distribute the native Android client to field agents, consumers, or defense evaluators:

1. **Build APK via Script:**
   ```bash
   python scripts/build_android_apk.py Release
   ```
2. **Transfer to Device:**
   - Copy `android/app/build/outputs/apk/release/app-release.apk` to phone storage, Google Drive, or send via Telegram.
3. **Install on Phone:**
   - Open phone **Settings** ➔ **Security** ➔ Enable **Install Unknown Apps**.
   - Tap the APK in the Files app and select **Install**.
   - Launch **PricePulse BD** from your app drawer.

---

## 6. Production Smoke Test Verification

Before signing off on any production deployment, run the automated verification suite:

```bash
python scripts/production_smoke_test.py
```

Expected Output:
```
[1/6] [PASS] API Health & Liveness
[2/6] [PASS] Taxonomy Completeness (65/65 staples)
[3/6] [PASS] Highway Transit Corridors & Spatial Arbitrage
[4/6] [PASS] 3-Channel Bazaar Basket Optimization
[5/6] [PASS] Saved Baskets Storage & CRUD
[6/6] [PASS] Static Frontend SPA Distribution
============================================================================
  ALL 6 PRODUCTION SMOKE TESTS PASSED! System is ready for deployment.
============================================================================
```
