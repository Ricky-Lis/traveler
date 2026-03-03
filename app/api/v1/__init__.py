from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.travel import router as travel_router
from app.api.v1.footprint import router as footprint_router
from app.api.v1.geocode import router as geocode_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth_router)
v1_router.include_router(travel_router)
v1_router.include_router(footprint_router)
v1_router.include_router(geocode_router)
