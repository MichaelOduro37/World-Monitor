# World Monitor 🌍

A real-time global event monitoring platform with web and mobile dashboards, multi-source ingestion, and smart notifications.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         World Monitor                           │
├──────────────┬──────────────────────────┬───────────────────────┤
│   Web App    │      Mobile App          │    Worker / Ingestion │
│  React+Vite  │    React Native (Expo)   │    Celery + Beat      │
│  Leaflet Map │    Expo Push Notifs      │    USGS/GDACS/RSS     │
└──────┬───────┴───────────┬──────────────┴──────────┬────────────┘
       │                   │                          │
       ▼                   ▼                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (REST)                        │
│   /auth  /events  /subscriptions  /rules  /sources              │
│   JWT auth · RBAC (admin/user) · OpenAPI docs at /docs          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌─────────────┐  ┌────────────┐  ┌─────────────┐
   │  PostgreSQL │  │   Redis    │  │Notifications│
   │  + PostGIS  │  │  (queue)   │  │ SMTP Email  │
   │  SQLAlchemy │  │            │  │ WhatsApp*   │
   │  Alembic    │  │            │  │ Web Push    │
   └─────────────┘  └────────────┘  └─────────────┘
```
*WhatsApp: optional, disabled by default

## Features

- 🌍 **Global Event Map** - Real-time visualization on OpenStreetMap
- 📡 **Multi-source Ingestion** - USGS Earthquakes, GDACS disaster alerts, RSS feeds
- 🔔 **Smart Notifications** - Email, Web Push; WhatsApp optional
- 🔐 **Email + Password Auth** - JWT with refresh tokens, RBAC
- 📱 **Mobile App** - React Native / Expo with push notifications
- 🐳 **Docker Compose** - One command local setup

## Quick Start (Local)

### Prerequisites
- Docker & Docker Compose
- Git

### 1. Clone and Configure
```bash
git clone https://github.com/MichaelOduro37/World-Monitor.git
cd World-Monitor
cp backend/.env.example backend/.env
# Edit backend/.env for your SMTP credentials (optional)
```

### 2. Start All Services
```bash
docker compose up --build
```
This starts: PostgreSQL, Redis, Backend API, Celery Worker, Web Dashboard.

### 3. Access Services
| Service | URL |
|---------|-----|
| Web Dashboard | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Health | http://localhost:8000/health |
| API Metrics | http://localhost:8000/metrics |

### 4. Create First Admin User
```bash
# Register via the web UI at http://localhost:3000/register
# Then promote to admin via API:
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"changeme","full_name":"Admin"}'
```

## Mobile App (Expo)

### Prerequisites
- Node.js 20+
- Expo CLI: `npm install -g expo-cli`

### Run
```bash
cd mobile
npm install --legacy-peer-deps
# Set API URL
echo "EXPO_PUBLIC_API_URL=http://YOUR_LOCAL_IP:8000" > .env

# Start Expo
npx expo start
# Scan QR code with Expo Go app on your phone
# Or press 'w' for web preview
```

## Environment Variables

### Backend (`backend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection |
| `SECRET_KEY` | dev key | JWT signing key - **change in production** |
| `SMTP_HOST` | `` | SMTP server (leave empty to disable email) |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USER` | `` | SMTP username |
| `SMTP_PASSWORD` | `` | SMTP password (Gmail: App Password) |
| `SMTP_FROM` | `` | From address |
| `WHATSAPP_ENABLED` | `false` | Enable WhatsApp notifications |
| `WHATSAPP_ACCESS_TOKEN` | `` | WhatsApp Cloud API token |
| `WHATSAPP_PHONE_NUMBER_ID` | `` | WhatsApp Cloud phone number ID |
| `VAPID_PRIVATE_KEY` | `` | Web Push VAPID private key |
| `VAPID_PUBLIC_KEY` | `` | Web Push VAPID public key |
| `INGESTION_INTERVAL_SECONDS` | `300` | How often to fetch new events |

### Generating VAPID Keys
```bash
pip install pywebpush
python -c "from py_vapid import Vapid; v = Vapid(); v.generate_keys(); print('Private:', v.private_pem().decode()); print('Public:', v.public_pem().decode())"
```

## Email Setup (Gmail)

1. Go to https://myaccount.google.com/apppasswords
2. Generate an App Password for "Mail"
3. Set in `backend/.env`:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_FROM=you@gmail.com
```

## WhatsApp Notifications

WhatsApp notifications are **disabled by default**. To enable:

1. Create a Meta Developer App: https://developers.facebook.com/
2. Set up WhatsApp Business API (free tier: 1000 messages/month)
3. Set in `backend/.env`:
```
WHATSAPP_ENABLED=true
WHATSAPP_ACCESS_TOKEN=your-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-id
```

**Note**: If you don't want to set up WhatsApp, the default mock sender logs messages without sending them. Use Email + Web Push as the free alternative.

## Adding New Event Sources

1. Create a new ingestor in `backend/app/workers/ingestion/`:
```python
from .base import BaseIngestor
from app.schemas.event import EventCreate

class MySourceIngestor(BaseIngestor):
    async def fetch(self) -> list[EventCreate]:
        # Fetch and normalize events
        return []
```

2. Register in `backend/app/workers/tasks.py` with the source type.
3. Add a Source record via the admin API: `POST /api/v1/sources`

## Deployment (Free Tiers)

### Option 1: Render.com (Recommended - Free tier available)
- Backend: Web Service (free tier, sleeps after inactivity)
- Worker: Background Worker
- Database: Render PostgreSQL (free 90 days, then ~$7/mo) ⚠️
- Redis: Upstash Redis (free tier, 10K requests/day)

See `docs/deploy-render.md` for step-by-step instructions.

### Option 2: Railway.app
- Free $5/month credit, ~500 hours
- Single `railway.toml` deploy
- See `docs/deploy-railway.md`

### Option 3: Fly.io
- Free allowance: 3 shared VMs, 3GB storage
- Deploy with `fly deploy`
- See `docs/deploy-fly.md`

### Option 4: Self-hosted VPS (Free options: Oracle Cloud Always Free, Google Cloud Free Tier)
```bash
# On your VPS:
git clone https://github.com/MichaelOduro37/World-Monitor.git
cd World-Monitor
cp backend/.env.example backend/.env
# Edit .env with production values
docker compose -f docker-compose.yml up -d
```

### Cost Summary
| Service | Option | Cost |
|---------|--------|------|
| Compute | Render/Railway/Fly.io free tier | **Free** (with limits) |
| Database | Supabase PostgreSQL | **Free** (500MB) |
| Redis | Upstash | **Free** (10K req/day) |
| Email | Gmail SMTP | **Free** |
| WhatsApp | Meta Cloud API | **Free** (1000 msg/month) |
| Maps | OpenStreetMap/Leaflet | **Free** |
| Data | USGS, GDACS, RSS | **Free** |

## API Reference

API docs auto-generated at: `http://localhost:8000/docs`

Key endpoints:
- `POST /api/v1/auth/register` - Create account
- `POST /api/v1/auth/login` - Get JWT token
- `GET /api/v1/events` - List events (filters: type, bbox, severity, q, start, end)
- `GET /api/v1/events/{id}` - Event detail
- `GET /api/v1/subscriptions` - My subscriptions
- `POST /api/v1/subscriptions` - Create subscription
- `GET /api/v1/sources` - (admin) List sources
- `GET /health` - Health check

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI (Python 3.11) |
| Database | PostgreSQL + PostGIS |
| Cache/Queue | Redis + Celery |
| Migrations | Alembic |
| Web Frontend | React 18 + Vite + Leaflet |
| Mobile | React Native + Expo |
| Auth | JWT (access + refresh tokens) |
| Email | SMTP (aiosmtplib) |
| Web Push | VAPID (pywebpush) |
| WhatsApp | Meta Cloud API (optional) |
| Data Sources | USGS, GDACS, RSS/Atom |
| Geo Enrichment | Nominatim (OpenStreetMap) |
| CI | GitHub Actions |

## Project Structure

```
World-Monitor/
├── backend/               # FastAPI API + Celery workers
│   ├── app/
│   │   ├── api/v1/       # REST endpoints
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Email, WhatsApp, WebPush
│   │   └── workers/      # Celery tasks + ingestors
│   ├── alembic/          # DB migrations
│   └── tests/            # pytest tests
├── web/                  # React + Vite dashboard
│   └── src/
│       ├── api/          # Axios client
│       ├── components/   # UI components
│       ├── pages/        # Route pages
│       └── store/        # Zustand state
├── mobile/               # React Native / Expo
│   ├── app/              # Expo Router screens
│   ├── components/       # RN components
│   └── store/            # State management
├── docker-compose.yml    # Local dev setup
└── .github/workflows/    # CI/CD
```

## License

MIT
