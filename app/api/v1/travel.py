from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query

from app.dependencies import get_travel_service, get_footprint_service, get_current_user, get_optional_user
from app.services.travel import TravelService
from app.services.footprint import FootprintService
from app.models.user import User
from app.schemas.travel import (
    TravelCreate,
    TravelUpdate,
    TravelStatusUpdate,
    TravelInfo,
    TravelListResponse,
)
from app.schemas.footprint import (
    FootprintListResponse,
    FootprintListItem,
    FootprintReorderRequest,
)
from app.schemas.user import MessageResponse

router = APIRouter(prefix="/travels", tags=["旅程"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_COVER_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("", response_model=TravelInfo, status_code=status.HTTP_201_CREATED, summary="创建旅程")
async def create_travel(
    body: TravelCreate,
    current_user: User = Depends(get_current_user),
    svc: TravelService = Depends(get_travel_service),
):
    try:
        travel = await svc.create(
            user_id=current_user.id,
            title=body.title,
            description=body.description,
            start_date=body.start_date,
            end_date=body.end_date,
            is_public=body.is_public,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return TravelInfo.model_validate(travel)


@router.get("/mine", response_model=TravelListResponse, summary="我的旅程列表")
async def list_my_travels(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    travel_status: int | None = Query(default=None, alias="status", ge=0, le=2),
    current_user: User = Depends(get_current_user),
    svc: TravelService = Depends(get_travel_service),
):
    items, total = await svc.list_my_travels(
        user_id=current_user.id, page=page, page_size=page_size, status=travel_status,
    )
    return TravelListResponse(
        items=[TravelInfo.model_validate(t) for t in items],
        total=total, page=page, page_size=page_size,
    )


@router.get("/public", response_model=TravelListResponse, summary="公开旅程列表")
async def list_public_travels(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    svc: TravelService = Depends(get_travel_service),
):
    items, total = await svc.list_public_travels(page=page, page_size=page_size)
    return TravelListResponse(
        items=[TravelInfo.model_validate(t) for t in items],
        total=total, page=page, page_size=page_size,
    )


@router.get("/{travel_id}", response_model=TravelInfo, summary="旅程详情")
async def get_travel(
    travel_id: int,
    current_user: User | None = Depends(get_optional_user),
    svc: TravelService = Depends(get_travel_service),
):
    viewer_id = current_user.id if current_user else None
    try:
        travel = await svc.get_detail(travel_id, viewer_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return TravelInfo.model_validate(travel)


@router.put("/{travel_id}", response_model=TravelInfo, summary="更新旅程")
async def update_travel(
    travel_id: int,
    body: TravelUpdate,
    current_user: User = Depends(get_current_user),
    svc: TravelService = Depends(get_travel_service),
):
    try:
        travel = await svc.update_travel(
            travel_id=travel_id,
            user_id=current_user.id,
            **body.model_dump(exclude_unset=True),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return TravelInfo.model_validate(travel)


@router.put("/{travel_id}/status", response_model=TravelInfo, summary="更新旅程状态")
async def update_travel_status(
    travel_id: int,
    body: TravelStatusUpdate,
    current_user: User = Depends(get_current_user),
    svc: TravelService = Depends(get_travel_service),
):
    try:
        travel = await svc.update_status(travel_id, current_user.id, body.status)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return TravelInfo.model_validate(travel)


@router.post("/{travel_id}/cover", response_model=TravelInfo, summary="上传旅程封面")
async def upload_cover(
    travel_id: int,
    file: UploadFile = File(..., description="封面图片"),
    current_user: User = Depends(get_current_user),
    svc: TravelService = Depends(get_travel_service),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的图片格式，仅支持 {', '.join(ALLOWED_IMAGE_TYPES)}",
        )

    data = await file.read()
    if len(data) > MAX_COVER_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="封面图片不能超过 5 MB",
        )

    try:
        travel = await svc.upload_cover(travel_id, current_user.id, data, file.content_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return TravelInfo.model_validate(travel)


@router.post("/{travel_id}/view", summary="浏览量 +1")
async def record_view(
    travel_id: int,
    current_user: User | None = Depends(get_optional_user),
    svc: TravelService = Depends(get_travel_service),
):
    viewer_id = current_user.id if current_user else None
    try:
        view_count = await svc.increment_view(travel_id, viewer_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return {"view_count": view_count}


@router.delete("/{travel_id}", response_model=MessageResponse, summary="删除旅程")
async def delete_travel(
    travel_id: int,
    current_user: User = Depends(get_current_user),
    svc: TravelService = Depends(get_travel_service),
):
    try:
        await svc.delete(travel_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return MessageResponse(message="旅程已删除")


# ---------- 足迹（按旅程） ----------

@router.get(
    "/{travel_id}/footprints",
    response_model=FootprintListResponse,
    summary="按旅程列出足迹",
)
async def list_travel_footprints(
    travel_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    order_by: str = Query(default="default", description="default | travel_time"),
    current_user: User | None = Depends(get_optional_user),
    svc: FootprintService = Depends(get_footprint_service),
):
    """按 sort_order / travel_time 排序，用于地图与路线串联。"""
    viewer_id = current_user.id if current_user else None
    try:
        items, total = await svc.list_by_travel(travel_id, viewer_id, page, page_size, order_by)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return FootprintListResponse(
        items=[FootprintListItem.model_validate(f) for f in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.put(
    "/{travel_id}/footprints/reorder",
    response_model=MessageResponse,
    summary="批量排序足迹",
)
async def reorder_footprints(
    travel_id: int,
    body: FootprintReorderRequest,
    current_user: User = Depends(get_current_user),
    svc: FootprintService = Depends(get_footprint_service),
):
    """可拖动排序，按 travel_id 下 footprint_id + sort_order 批量更新。"""
    try:
        items = [(r.footprint_id, r.sort_order) for r in body.items]
        await svc.reorder(travel_id, current_user.id, items)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return MessageResponse(message="排序已更新")
