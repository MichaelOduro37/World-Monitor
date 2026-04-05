# Deploying World Monitor

This guide explains how to run World Monitor on the internet so you can access and
monitor it from anywhere. Choose the option that best suits your needs.

| Platform | Free tier | Difficulty | Best for |
|---|---|---|---|
| **[Render](#option-1--render-recommended)** | ✅ (limited) | ⭐ Easiest | Quick start, GitHub auto-deploy |
| **[Railway](#option-2--railway)** | ✅ ($5 credit/mo) | ⭐⭐ Easy | Generous free tier, great DX |
| **[Fly.io](#option-3--flyio)** | ✅ (limited) | ⭐⭐ Moderate | Always-on, global edge |
| **[VPS (self-hosted)](#option-4--self-hosted-vps)** | ❌ (~$5/mo) | ⭐⭐ Moderate | Full control, custom domain |

> **Free tier note**: Most free tiers spin down idle services after a period of
> inactivity. Upgrade to a paid plan for always-on monitoring.

---

## Option 1 – Render (Recommended)

Render deploys the **entire stack** (API, worker, web dashboard, PostgreSQL, Redis)
from the `render.yaml` file included in this repo — no configuration needed upfront.

### Step 1 – Fork the repository

Make sure you have your own fork of this repo on GitHub so Render can access it.

### Step 2 – Create a Blueprint on Render

1. Go to [dashboard.render.com](https://dashboard.render.com) and sign in with GitHub.
2. Click **"New" → "Blueprint"**.
3. Select your forked `World-Monitor` repository.
4. Render detects `render.yaml` and shows a preview of all five services.
5. Click **"Apply"** — Render creates and starts everything automatically.

Services created:

| Service | Type | What it does |
|---|---|---|
| `world-monitor-api` | Web service | FastAPI backend |
| `world-monitor-worker` | Background worker | Celery data ingestion & notifications |
| `world-monitor-web` | Static site | React map dashboard |
| `world-monitor-db` | Managed PostgreSQL | Stores all events & users |
| `world-monitor-redis` | Managed Redis | Task queue & cache |

### Step 3 – Set the required variables

A few variables are marked `sync: false` (intentionally blank) because they depend
on the URLs assigned after the first deploy.

**In `world-monitor-api` → Environment:**

| Variable | Value |
|---|---|
| `CORS_ORIGINS` | Your web frontend URL, e.g. `https://world-monitor-web.onrender.com` |
| `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` | *(optional)* For email alerts — see [Email setup](#email-setup-gmail) |
| `VAPID_PRIVATE_KEY` / `VAPID_PUBLIC_KEY` | *(optional)* For browser push — see [VAPID keys](#generating-vapid-keys) |

**In `world-monitor-worker` → Environment:**

| Variable | Value |
|---|---|
| `SECRET_KEY` | Copy the auto-generated value from `world-monitor-api → Environment → SECRET_KEY` |

**In `world-monitor-web` → Environment:**

| Variable | Value |
|---|---|
| `VITE_API_URL` | `https://world-monitor-api.onrender.com/api/v1` |

After setting `VITE_API_URL`, click **"Manual Deploy"** on `world-monitor-web` to
rebuild the frontend with the correct API URL.

### Step 4 – Access the app

| URL | What's there |
|---|---|
| `https://world-monitor-web.onrender.com` | Live map dashboard |
| `https://world-monitor-api.onrender.com/docs` | Interactive API docs |
| `https://world-monitor-api.onrender.com/health` | Health check |

---

## Option 2 – Railway

Railway supports managed PostgreSQL (with PostGIS), Redis, and Docker builds with
GitHub auto-deploys.

### Prerequisites

- [Railway account](https://railway.app) (sign up with GitHub)
- Railway CLI (optional): `npm install -g @railway/cli`

### Step 1 – Create a new project

Go to [railway.app](https://railway.app) → **"New Project" → "Deploy from GitHub
repo"** → select `World-Monitor`.

Railway will start deploying the backend using `railway.toml`.

### Step 2 – Add PostgreSQL and Redis

In the Railway dashboard for your project:

1. Click **"+ New"** → **"Database"** → **"Add PostgreSQL"**.
2. Click **"+ New"** → **"Database"** → **"Add Redis"**.

### Step 3 – Add the worker and web services

1. **Worker**: Click **"+ New"** → **"GitHub Repo"** → same repo, set **Root
   Directory** to `backend/`, set **Start Command** to:
   ```
   celery -A app.workers.celery_app worker --beat --loglevel=info
   ```
2. **Web**: Click **"+ New"** → **"GitHub Repo"** → same repo, set **Root
   Directory** to `web/`, set **Build Command** to:
   ```
   npm install --legacy-peer-deps && npm run build
   ```
   Set **Start Command** to `npx serve dist -l $PORT` (or use the Docker build
   by pointing to `web/Dockerfile`).

### Step 4 – Set environment variables

For the **backend** and **worker** services, Railway can inject database/Redis URLs
automatically using **Reference Variables**. In each service's Variables tab:

```
DATABASE_URL   = ${{Postgres.DATABASE_URL}}
REDIS_URL      = ${{Redis.REDIS_URL}}
SECRET_KEY     = <run: openssl rand -hex 32>
APP_ENV        = production
CORS_ORIGINS   = https://<your-web-service>.up.railway.app
```

For the **web** service:
```
VITE_API_URL = https://<your-api-service>.up.railway.app/api/v1
```

### Step 5 – Enable PostGIS (if needed)

In the PostgreSQL service → **Query** tab:
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

### Step 6 – Access the app

Railway assigns public URLs to each service automatically. Find them in each
service's **Settings → Domains** tab.

---

## Option 3 – Fly.io

### Prerequisites

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh
fly auth login
```

### Deploy the backend

```bash
cd backend

# Create the app (one-time)
fly launch --name world-monitor-api --region iad --no-deploy

# Create and attach a Postgres database
fly postgres create --name world-monitor-db --region iad
fly postgres attach world-monitor-db

# Create a Redis instance (Upstash)
fly redis create --name world-monitor-redis --region iad --no-eviction

# Set secrets
fly secrets set \
  SECRET_KEY=$(openssl rand -hex 32) \
  APP_ENV=production \
  REDIS_URL=$(fly redis status world-monitor-redis --json | jq -r '.privateUrl')

# Deploy
fly deploy
```

### Deploy the worker

```bash
# From the backend/ directory, create a second app for the worker
fly launch --name world-monitor-worker --region iad --no-deploy
fly secrets set \
  DATABASE_URL=$(fly postgres config show -a world-monitor-db | grep URI | awk '{print $2}') \
  REDIS_URL=$(fly redis status world-monitor-redis --json | jq -r '.privateUrl') \
  SECRET_KEY=<same value as API> \
  APP_ENV=production
fly deploy --config fly.worker.toml
```

### Deploy the frontend

```bash
cd web

fly launch --name world-monitor-web --region iad --no-deploy
fly deploy --build-arg VITE_API_URL=https://world-monitor-api.fly.dev/api/v1
```

Update CORS on the backend:
```bash
cd backend
fly secrets set CORS_ORIGINS=https://world-monitor-web.fly.dev
```

### Access the app

- Dashboard: `https://world-monitor-web.fly.dev`
- API: `https://world-monitor-api.fly.dev`
- API docs: `https://world-monitor-api.fly.dev/docs`

---

## Option 4 – Self-Hosted VPS

Best when you want full control, a custom domain, or always-on uptime without paying
cloud platform premiums.

Tested on **Ubuntu 22.04** with a $6/mo [Hetzner CX22](https://www.hetzner.com/cloud)
or [DigitalOcean Basic Droplet](https://www.digitalocean.com/pricing).

### Step 1 – Prepare the server

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in, then:
docker --version   # should print version
```

### Step 2 – Clone and configure

```bash
git clone https://github.com/MichaelOduro37/World-Monitor.git
cd World-Monitor

cp .env.production.example .env.production
nano .env.production   # set POSTGRES_PASSWORD and SECRET_KEY at minimum
```

Minimum required changes in `.env.production`:

```bash
POSTGRES_PASSWORD=<strong random password>
SECRET_KEY=<run: openssl rand -hex 32>
CORS_ORIGINS=http://<your-server-ip>   # or https://yourdomain.com
```

### Step 3 – Start the stack

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

All five services (db, redis, backend, worker, web) start automatically. The first
run builds Docker images which takes a few minutes.

Check everything is running:
```bash
docker compose -f docker-compose.prod.yml ps
```

### Step 4 – Access the app

- **Dashboard**: `http://<your-server-ip>`
- **API docs**: `http://<your-server-ip>/api/docs` *(via nginx proxy)*

### Step 5 – Add HTTPS + custom domain (recommended)

Point your domain's A record to the server IP, then:

```bash
sudo apt install nginx certbot python3-certbot-nginx -y

sudo tee /etc/nginx/sites-available/worldmonitor > /dev/null <<'EOF'
server {
    server_name monitor.yourdomain.com;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/worldmonitor /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Issue a free TLS certificate
sudo certbot --nginx -d monitor.yourdomain.com
```

Update `.env.production`:
```bash
CORS_ORIGINS=https://monitor.yourdomain.com
```

Restart the backend to pick up the new CORS setting:
```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d backend
```

---

## Generating VAPID Keys

VAPID keys enable browser push notifications. Generate them once:

```bash
pip install pywebpush
python - <<'EOF'
from pywebpush import Vapid
v = Vapid()
v.generate_keys()
print("VAPID_PRIVATE_KEY =", v.private_key.serialize().decode())
print("VAPID_PUBLIC_KEY  =", v.public_key.serialize().decode())
EOF
```

Copy the output into your environment variables.

---

## Email Setup (Gmail)

1. Enable **2-Step Verification** on your Google account.
2. Go to **Google Account → Security → App Passwords**.
3. Create an App Password for "Mail".
4. Set these environment variables:

```
SMTP_HOST     = smtp.gmail.com
SMTP_PORT     = 587
SMTP_USER     = you@gmail.com
SMTP_PASSWORD = <16-character app password from step 3>
SMTP_FROM     = you@gmail.com
```

---

## Viewing Logs

```bash
# Render — via dashboard or:
render logs --service world-monitor-api --tail

# Railway
railway logs

# Fly.io
fly logs -a world-monitor-api

# VPS
docker compose -f docker-compose.prod.yml logs -f
docker compose -f docker-compose.prod.yml logs -f backend worker
```

---

## Updating the App

After pushing new commits to the `main` branch:

- **Render / Railway**: Auto-deploys on push (configured by default).
- **Fly.io**: `fly deploy` from the service directory.
- **VPS**:
  ```bash
  git pull
  docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
  ```
