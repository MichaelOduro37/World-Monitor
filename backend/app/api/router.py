from fastapi import APIRouter

from app.api.v1 import auth, events, subscriptions, rules, sources, stats, stream

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(events.router)
api_router.include_router(subscriptions.router)
api_router.include_router(rules.router)
api_router.include_router(sources.router)
api_router.include_router(stats.router)
api_router.include_router(stream.router)
