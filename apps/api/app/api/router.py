from fastapi import APIRouter

from app.api.routes import chat, connections, history, schema

api_router = APIRouter()
api_router.include_router(connections.router, tags=["connections"])
api_router.include_router(schema.router, tags=["schema"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(history.router, tags=["history"])
