from datetime import date, datetime

from pydantic import BaseModel, Field


# ---------- 请求体 ----------

class TravelCreate(BaseModel):
    """创建旅程"""
    title: str = Field(..., min_length=1, max_length=100, description="旅程标题")
    description: str | None = Field(default=None, max_length=2000, description="旅程描述")
    start_date: date | None = Field(default=None, description="出发日期")
    end_date: date | None = Field(default=None, description="结束日期")
    is_public: bool = Field(default=True, description="是否公开")


class TravelUpdate(BaseModel):
    """更新旅程（所有字段可选）"""
    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    start_date: date | None = None
    end_date: date | None = None
    is_public: bool | None = None


class TravelStatusUpdate(BaseModel):
    """更新旅程状态"""
    status: int = Field(..., ge=0, le=2, description="0-草稿 1-进行中 2-已完成")


# ---------- 响应体 ----------

class TravelInfo(BaseModel):
    """旅程详情"""
    id: int
    user_id: int
    title: str
    description: str | None = None
    cover_image_url: str
    start_date: date | None = None
    end_date: date | None = None
    status: int
    is_public: bool
    view_count: int
    footprint_count: int
    image_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TravelListResponse(BaseModel):
    """旅程列表响应（分页）"""
    items: list[TravelInfo]
    total: int
    page: int
    page_size: int
