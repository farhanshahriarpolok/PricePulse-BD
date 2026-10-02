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
        │  Port 8000: Uvicorn Runner (1 Worker, UID 1000)
        │                                              │
        │  ┌────────────────────┐ ┌──────────────────┐ │
        │  │ FastAPI REST API   │ │ React 18 SPA     │ │
        │  │ /api/v1/*          │ │ (Static Mount)   │ │
        │  └─────────┬──────────┘ └──────────────────┘ │
        │            │                                 │
        │            ▼                                 │
        │  SQLite 3 (WAL Mode, 5000ms Busy Timeout)   │
        │  Volume: /app/data (DB & Backups)           │
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
- Boots FastAPI with 1 Uvicorn worker on localhost port `127.0.0.1:8000` (preserving singleton in-process scheduler).
- Executes as an unprivileged user (`pricepulse`, UID 1000).
- Initializes the SQLite database at `/app/data/pricepulse.db` with WAL mode.
- Directs automated hot backups to persistent volume storage at `/app/data/backups/`.
- Seeds all 65 canonical commodities, 64 districts, and 30-day baseline observations.

---

## 2. Nginx Reverse Proxy with Let's Encrypt SSL

### Step A: Install Nginx & Certbot
```bash
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx
```

### Step B: Configure Nginx Server Block with Rate Limiting (Phase 5D.3)
Create `/etc/nginx/sites-available/pricepulse`:
```nginx
# Rate limiting zone for compute-intensive Viva simulation shock injection (Phase 5D.3)
# Key: $binary_remote_addr (10MB memory stores ~160,000 distinct client IPs)
# Rate: 5 requests per second (5r/s) strictly protecting hypothetical supply shock evaluations
limit_req_zone $binary_remote_addr zone=simulation_shock_limit:10m rate=5r/s;

server {
    server_name pricepulse.yourdomain.com;

    client_max_body_size 20M;

    # Gzip compression for high-performance React bundle delivery
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript image/svg+xml;

    # 1. Protected Route: Simulation Shock Injection (Phase 5D.3)
    #    Limited to 5 req/sec with a controlled burst=10 nodelay.
    #    Returns HTTP 429 (Too Many Requests) when burst capacity is exceeded.
    location = /api/v1/simulation/inject-shock {
        limit_req zone=simulation_shock_limit burst=10 nodelay;
        limit_req_status 429;

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

    # 2. General REST API and Static React SPA Pass-Through (Unthrottled)
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

### Step C: Enable Site & Reload Nginx
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

## 4. SQLite Zero-Downtime Hot Backup & Disaster Recovery (Phase 5D.2)

PricePulse BD includes a production-grade hot backup utility (`scripts/backup_db.py`) utilizing Python's native SQLite Online Backup API (`sqlite3.Connection.backup`). It safely captures live WAL databases without interrupting active write transactions.

### Workflow & Invariants:
1. **Live Snapshot**: Copies pages online to an ephemeral `.db.tmp` file.
2. **Deep Verification**: Executes `PRAGMA integrity_check;` and verifies critical table schemas (`commodities`, `sources`, `price_observations`, `districts`, `divisions`).
3. **Atomic Promotion**: Successfully verified snapshots are atomically promoted to `pricepulse_backup_YYYYMMDD_HHMMSS.db`.
4. **Retention Pruning**: Automatically prunes older backups beyond the configured retention limit (default: 7 snapshots).
5. **Fail-Safe Rollback**: If verification fails, the `.tmp` file is purged, the last-known good backup is preserved, and a non-zero exit code is returned.

### Manual Backup Execution:
```bash
# Direct Python execution (Linux or Windows host)
python scripts/backup_db.py --retention-count 7

# Inside Docker container (automatically persists to /app/data/backups via named volume)
docker exec pricepulse_bd_app python scripts/backup_db.py --retention-count 14

# Synchronize verified backups to remote off-site storage or S3
rsync -avz /var/lib/docker/volumes/pricepulse_data/_data/backups/ user@backupserver:/backups/
```

### Automated Scheduling Options:
- **Host Linux Crontab (Nightly at 02:00 AM)**:
  ```cron
  0 2 * * * cd /opt/pricepulse-bd && python3 scripts/backup_db.py --retention-count 14 >> /var/log/pricepulse_backup.log 2>&1
  ```
- **Windows Task Scheduler (Local Development)**:
  ```powershell
  schtasks /create /tn "PricePulseDB_Backup" /tr "D:\PricePulse BD\venv\Scripts\python.exe D:\PricePulse BD\scripts\backup_db.py" /sc daily /st 02:00
  ```

---

## 5. Source Health Observability & Rolling 7-Day Telemetry (Phase 5D.1)

To ensure persistent reliability monitoring across server reboots, provider check attempts are stored in the SQLite `source_health_logs` table with an idempotent `UNIQUE(source_name, date)` constraint.

### Key Capabilities:
- **Zero Hallucination / Pure Math**: Availability is deterministically computed as:
  $$\text{Availability } (\%) = \frac{\text{Successful Checks}}{\text{Total Checks}} \times 100$$
- **Unskewed Latency Metrics**: Latency averages, minimums, and maximums are computed exclusively from successful checks; network timeouts and HTTP errors never artificially lower latency metrics.
- **Rolling 7-Day Aggregation**: `GET /api/v1/system/sources` aggregates observations over the trailing 7 calendar days, handling missing observation days gracefully without treating unattempted dates as failures.
- **Full API Compatibility**: Exposes both live operational state (`current_status`, `last_sync`, `last_success`, `last_failure`) and historical 7-day durability (`rolling_7d_availability`, `rolling_7d_avg_latency_ms`).

---

## 6. Physical Android Device Sideloading (APK)

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

## 7. Production Smoke Test Verification

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

---

## 8. Administrative Security & API Key Safeguards (Phase 6B)

To secure administrative mutations against anonymous calls in production, PricePulse BD enforces server-side API key authentication via the `X-API-Key` HTTP header.

### Protected Mutation Endpoints:
- `POST /api/v1/observations/manual` (Field spot price submission)
- `POST /api/v1/system/sync` (On-demand data harvest initiation)

### Environment Variable Configuration:
Configure the secret key on your server or container environment:
```bash
export PRICEPULSE_ADMIN_API_KEY="your-strong-random-32char-secret-key"
```

In `docker-compose.yml` or container environment files (`.env`):
```yaml
environment:
  - PRICEPULSE_ADMIN_API_KEY=${PRICEPULSE_ADMIN_API_KEY}
```

### Security Invariants & Fail-Closed Design:
1. **Fail-Closed Default**: If `PRICEPULSE_ADMIN_API_KEY` is not configured or empty, administrative endpoints reject all mutation attempts with `HTTP 401 Unauthorized`.
2. **Timing-Safe Digest**: Uses Python's `secrets.compare_digest()` to prevent timing attack side-channels.
3. **Zero Secret Leaks**: The configured secret is never emitted in error envelopes, server logs, API docs, URL parameters, or frontend code bundles.
4. **Public Endpoints Untouched**: Read endpoints (`GET /health`, `GET /api/v1/system/sources`, `GET /api/v1/commodities`, etc.) and the Viva Simulation Sandbox (`POST /api/v1/simulation/inject-shock`, rate-limited via Nginx) remain unauthenticated.

### Example Authenticated Ingestion Trigger:
```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/system/sync \
  -H "X-API-Key: your-strong-random-32char-secret-key"
```
