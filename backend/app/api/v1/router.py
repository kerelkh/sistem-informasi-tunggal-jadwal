from fastapi import APIRouter

from app.features.auth.router import router as auth_router
from app.features.availability.router import router as availability_router
from app.features.health.router import router as health_router
from app.features.meetings.router import router as meetings_router
from app.features.notifications.router import router as notifications_router
from app.features.units.router import router as units_router
from app.features.users.router import router as users_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(units_router, prefix="/units", tags=["units"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(meetings_router, prefix="/meetings", tags=["meetings"])
api_router.include_router(availability_router, prefix="/availability", tags=["availability"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
