#!/usr/bin/env bash
set -euo pipefail

# ─── Colour helpers ────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[start]${NC} $*"; }
warn()  { echo -e "${YELLOW}[start]${NC} $*"; }

# ─── 1. Copy .env if missing ────────────────────────────────────────────────────
if [ ! -f backend/.env ]; then
  if [ ! -f backend/.env.example ]; then
    echo "ERROR: backend/.env.example not found. Cannot continue." >&2
    exit 1
  fi
  warn "backend/.env not found — copying from backend/.env.example"
  cp backend/.env.example backend/.env
  warn "Edit backend/.env to add your SMTP / VAPID / WhatsApp credentials before using notifications."
else
  info "backend/.env already exists — skipping copy."
fi

# ─── 2. Start all services ──────────────────────────────────────────────────────
info "Starting all services with Docker Compose …"
docker compose up --build -d

# ─── 3. Print access URLs ───────────────────────────────────────────────────────
echo ""
info "All services are up!"
echo ""
echo "  Web Dashboard  → http://localhost:3000"
echo "  API Docs       → http://localhost:8000/docs"
echo "  API Health     → http://localhost:8000/health"
echo ""
info "Tail logs with:  docker compose logs -f"
info "Stop services:   docker compose down"
