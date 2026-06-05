from fastapi import APIRouter
from api.v1.endpoints import auth, users, dashboard,canvas

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(dashboard.api_router)
api_router.include_router(canvas.router)
