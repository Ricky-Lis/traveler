from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ---------- 逆地理编码 ----------

class ReverseGeocodeResult(BaseModel):
    """逆地理编码结果"""
    location_name: str = Field(default="", description="地点/POI 名称")
    address: str = Field(default="", description="详细地址")
    district: str = Field(default="", description="区县")
    city_name: str = Field(default="", description="城市")
    province_name: str = Field(default="", description="省份")
    country_name: str = Field(default="", description="国家")


# ---------- 足迹 请求体 ----------

class FootprintCreate(BaseModel):
    """创建足迹（GPS 必填，归属旅程可自动）"""
    latitude: Decimal = Field(..., ge=-90, le=90, description="纬度")
    longitude: Decimal = Field(..., ge=-180, le=180, description="经度")
    travel_id: int | None = Field(default=None, description="所属旅程 ID，不传则自动归属当前进行中的旅程")
    description: str | None = Field(default=None, max_length=2000, description="足迹描述")
    travel_time: datetime | None = Field(default=None, description="到达时间（用于路线串联）")
    # 逆地理结果（可选，不传则服务端尝试逆地理）
    location_name: str = Field(default="", max_length=255)
    address: str = Field(default="", max_length=500)
    district: str = Field(default="", max_length=100)
    city_name: str = Field(default="", max_length=100)
    province_name: str = Field(default="", max_length=100)
    country_name: str = Field(default="", max_length=100)


class FootprintUpdate(BaseModel):
    """更新足迹（支持手动调整位置与描述）"""
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    location_name: str | None = None
    address: str | None = None
    district: str | None = None
    city_name: str | None = None
    province_name: str | None = None
    country_name: str | None = None
    location_adjusted: bool | None = Field(default=None, description="是否手动调整过位置")
    description: str | None = None
    travel_time: datetime | None = None
    sort_order: int | None = None


class FootprintReorderItem(BaseModel):
    footprint_id: int
    sort_order: int


class FootprintReorderRequest(BaseModel):
    """批量更新足迹排序（可拖动排序）"""
    items: list[FootprintReorderItem] = Field(..., min_length=1)


# ---------- 足迹 响应体 ----------

class FootprintImageInfo(BaseModel):
    id: int
    footprint_id: int
    original_url: str
    thumbnail_url: str
    width: int | None = None
    height: int | None = None
    size_kb: int | None = None
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FootprintInfo(BaseModel):
    """足迹详情（含图片列表）"""
    id: int
    travel_id: int
    user_id: int
    latitude: Decimal
    longitude: Decimal
    location_name: str
    address: str
    district: str
    city_name: str
    province_name: str
    country_name: str
    location_adjusted: bool
    description: str | None = None
    cover_thumbnail_url: str
    image_count: int
    travel_time: datetime | None = None
    sort_order: int
    created_at: datetime
    updated_at: datetime
    images: list[FootprintImageInfo] = []

    model_config = {"from_attributes": True}


class FootprintListItem(BaseModel):
    """足迹列表项（地图/路线用，可不含 images）"""
    id: int
    travel_id: int
    user_id: int
    latitude: Decimal
    longitude: Decimal
    location_name: str
    address: str
    district: str
    city_name: str
    province_name: str
    country_name: str
    location_adjusted: bool
    description: str | None = None
    cover_thumbnail_url: str
    image_count: int
    travel_time: datetime | None = None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FootprintListResponse(BaseModel):
    items: list[FootprintListItem]
    total: int
    page: int
    page_size: int
