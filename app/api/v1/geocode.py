from fastapi import APIRouter, Depends, Query

from app.dependencies import get_footprint_service, get_current_user
from app.services.footprint import FootprintService
from app.models.user import User
from app.schemas.footprint import (
    ReverseGeocodeResult,
    FootprintListResponse,
    FootprintListItem,
    FootprintReorderRequest,
)
from app.schemas.user import MessageResponse

router = APIRouter(tags=["逆地理编码"])


@router.get(
    "/geocode/reverse",
    response_model=ReverseGeocodeResult,
    summary="逆地理编码",
)
async def reverse_geocode(
    lat: float = Query(..., ge=-90, le=90, description="纬度"),
    lng: float = Query(..., ge=-180, le=180, description="经度"),
    current_user: User = Depends(get_current_user),
    svc: FootprintService = Depends(get_footprint_service),
):
    """根据经纬度获取地址信息（高德 Web 服务）。需配置 AMAP_WEB_SERVICE_KEY。"""
    result = await svc.reverse_geocode(lat, lng)
    if result is None:
        return ReverseGeocodeResult()
    return ReverseGeocodeResult(**result)
