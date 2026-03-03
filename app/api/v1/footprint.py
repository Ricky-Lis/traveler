from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File

from app.dependencies import get_footprint_service, get_current_user, get_optional_user
from app.services.footprint import FootprintService
from app.models.user import User
from app.schemas.footprint import (
    FootprintCreate,
    FootprintUpdate,
    FootprintInfo,
    FootprintListItem,
    FootprintListResponse,
    FootprintImageInfo,
)
from app.schemas.user import MessageResponse

router = APIRouter(prefix="/footprints", tags=["足迹"])


@router.post("", response_model=FootprintInfo, status_code=status.HTTP_201_CREATED, summary="创建足迹")
async def create_footprint(
    body: FootprintCreate,
    current_user: User = Depends(get_current_user),
    svc: FootprintService = Depends(get_footprint_service),
):
    """创建足迹。可选传 travel_id；不传则自动归属当前「进行中」的旅程。"""
    try:
        fp = await svc.create(
            user_id=current_user.id,
            latitude=body.latitude,
            longitude=body.longitude,
            travel_id=body.travel_id,
            description=body.description,
            travel_time=body.travel_time,
            location_name=body.location_name,
            address=body.address,
            district=body.district,
            city_name=body.city_name,
            province_name=body.province_name,
            country_name=body.country_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return FootprintInfo(
        **{k: getattr(fp, k) for k in FootprintInfo.model_fields if k != "images"},
        images=[],
    )


@router.get("/{footprint_id}", response_model=FootprintInfo, summary="足迹详情")
async def get_footprint(
    footprint_id: int,
    current_user: User | None = Depends(get_optional_user),
    svc: FootprintService = Depends(get_footprint_service),
):
    viewer_id = current_user.id if current_user else None
    try:
        fp = await svc.get_detail(footprint_id, viewer_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return FootprintInfo(
        **{k: getattr(fp, k) for k in FootprintInfo.model_fields if k != "images"},
        images=[FootprintImageInfo.model_validate(img) for img in fp.images],
    )


@router.put("/{footprint_id}", response_model=FootprintInfo, summary="更新足迹")
async def update_footprint(
    footprint_id: int,
    body: FootprintUpdate,
    current_user: User = Depends(get_current_user),
    svc: FootprintService = Depends(get_footprint_service),
):
    """支持手动调整位置、描述、到达时间、排序等。"""
    try:
        fp = await svc.update_footprint(
            footprint_id,
            current_user.id,
            **body.model_dump(exclude_unset=True),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return FootprintInfo(
        **{k: getattr(fp, k) for k in FootprintInfo.model_fields},
        images=[FootprintImageInfo.model_validate(img) for img in fp.images],
    )


@router.delete("/{footprint_id}", response_model=MessageResponse, summary="删除足迹")
async def delete_footprint(
    footprint_id: int,
    current_user: User = Depends(get_current_user),
    svc: FootprintService = Depends(get_footprint_service),
):
    try:
        await svc.delete(footprint_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return MessageResponse(message="足迹已删除")


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/{footprint_id}/images", response_model=FootprintImageInfo, status_code=status.HTTP_201_CREATED, summary="上传足迹图片")
async def upload_footprint_image(
    footprint_id: int,
    file: UploadFile = File(..., description="图片文件"),
    current_user: User = Depends(get_current_user),
    svc: FootprintService = Depends(get_footprint_service),
):
    """上传原图并自动生成缩略图（OSS）。首图将作为足迹封面。"""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的图片格式，仅支持 {', '.join(ALLOWED_IMAGE_TYPES)}",
        )
    data = await file.read()
    if len(data) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="图片不能超过 10 MB",
        )
    try:
        img = await svc.upload_image(
            footprint_id, current_user.id, data, file.content_type or "image/jpeg"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return FootprintImageInfo.model_validate(img)
