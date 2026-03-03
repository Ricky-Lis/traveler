import asyncio
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.footprint import Footprint, FootprintImage
from app.models.travel import Travel
from app.utils.geocode import reverse_geocode
from app.utils.oss import (
    upload_image,
    generate_thumbnail,
    url_to_key,
    delete_object,
)


class FootprintService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- 逆地理编码 ----------

    async def reverse_geocode(self, lat: float, lng: float) -> dict | None:
        """逆地理编码，在线程池中执行避免阻塞"""
        return await asyncio.to_thread(reverse_geocode, lng, lat)

    # ---------- 创建足迹 ----------

    async def create(
        self,
        user_id: int,
        latitude: Decimal,
        longitude: Decimal,
        travel_id: int | None = None,
        description: str | None = None,
        travel_time: datetime | None = None,
        location_name: str = "",
        address: str = "",
        district: str = "",
        city_name: str = "",
        province_name: str = "",
        country_name: str = "",
    ) -> Footprint:
        # 确定所属旅程：未传则自动归属当前「进行中」旅程
        if travel_id is None:
            ongoing = await self.db.scalar(
                select(Travel).where(
                    Travel.user_id == user_id,
                    Travel.status == 1,
                )
            )
            if ongoing is None:
                raise ValueError("未指定旅程且当前没有进行中的旅程，请先创建并开始一个旅程")
            travel_id = ongoing.id
        else:
            travel = await self._get_own_travel(travel_id, user_id)
            if travel.status not in (0, 1):
                raise ValueError("只能向草稿或进行中的旅程添加足迹")

        # 若未传地址信息，尝试逆地理
        if not address and not city_name:
            geo = await self.reverse_geocode(float(latitude), float(longitude))
            if geo:
                location_name = geo.get("location_name") or location_name
                address = geo.get("address") or address
                district = geo.get("district") or district
                city_name = geo.get("city_name") or city_name
                province_name = geo.get("province_name") or province_name
                country_name = geo.get("country_name") or country_name

        fp = Footprint(
            travel_id=travel_id,
            user_id=user_id,
            latitude=latitude,
            longitude=longitude,
            location_name=location_name or "",
            address=address or "",
            district=district or "",
            city_name=city_name or "",
            province_name=province_name or "",
            country_name=country_name or "中国",
            description=description,
            travel_time=travel_time,
        )
        self.db.add(fp)
        await self.db.flush()
        await self.db.refresh(fp)

        # 更新旅程足迹数
        await self.db.execute(
            update(Travel)
            .where(Travel.id == travel_id)
            .values(footprint_count=Travel.footprint_count + 1)
        )
        await self.db.flush()
        return fp

    # ---------- 更新足迹 ----------

    async def update_footprint(
        self,
        footprint_id: int,
        user_id: int,
        **fields,
    ) -> Footprint:
        fp = await self._get_own_footprint(footprint_id, user_id)

        location_keys = {
            "latitude", "longitude", "location_name", "address",
            "district", "city_name", "province_name", "country_name",
        }
        if any(k in fields for k in location_keys):
            fields["location_adjusted"] = True

        for key, value in fields.items():
            if value is None and key != "description":
                continue
            if key == "location_adjusted":
                setattr(fp, key, bool(value))
            elif hasattr(fp, key):
                setattr(fp, key, value)

        await self.db.flush()
        await self.db.refresh(fp)
        return fp

    # ---------- 删除足迹 ----------

    async def delete(self, footprint_id: int, user_id: int) -> None:
        fp = await self._get_own_footprint(footprint_id, user_id)
        travel_id = fp.travel_id
        image_count = fp.image_count

        # 删除 OSS 上的图片（含封面缩略图，封面即某张图的 thumbnail）
        for img in fp.images:
            for url in (img.original_url, img.thumbnail_url):
                key = url_to_key(url)
                if key:
                    await asyncio.to_thread(delete_object, key)

        await self.db.delete(fp)
        await self.db.flush()

        # 更新旅程计数
        await self.db.execute(
            update(Travel)
            .where(Travel.id == travel_id)
            .values(
                footprint_count=Travel.footprint_count - 1,
                image_count=Travel.image_count - image_count,
            )
        )
        await self.db.flush()

    # ---------- 详情 ----------

    async def get_detail(
        self,
        footprint_id: int,
        viewer_id: int | None = None,
    ) -> Footprint:
        fp = await self.db.get(Footprint, footprint_id)
        if fp is None:
            raise ValueError("足迹不存在")
        travel = await self.db.get(Travel, fp.travel_id)
        if not travel:
            raise ValueError("旅程不存在")
        if not travel.is_public and travel.user_id != viewer_id:
            raise PermissionError("无权查看此足迹")
        return fp

    # ---------- 按旅程列表（按 sort_order, travel_time, id） ----------

    async def list_by_travel(
        self,
        travel_id: int,
        viewer_id: int | None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "default",
    ) -> tuple[list[Footprint], int]:
        travel = await self.db.get(Travel, travel_id)
        if travel is None:
            raise ValueError("旅程不存在")
        if not travel.is_public and travel.user_id != viewer_id:
            raise PermissionError("无权查看此旅程的足迹")

        conditions = [Footprint.travel_id == travel_id]
        total = await self.db.scalar(
            select(func.count()).select_from(Footprint).where(*conditions)
        )
        total = total or 0

        if order_by == "travel_time":
            # MySQL 不支持 NULLS LAST，用 (IS NOT NULL DESC, time ASC) 实现 null 放最后
            order = (Footprint.travel_time.isnot(None).desc(), Footprint.travel_time.asc(), Footprint.id.asc())
        else:
            order = (Footprint.sort_order.asc(), Footprint.travel_time.isnot(None).desc(), Footprint.travel_time.asc(), Footprint.id.asc())

        stmt = (
            select(Footprint)
            .where(*conditions)
            .order_by(*order)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())
        return items, total

    # ---------- 上传图片（原图 + 缩略图） ----------

    async def upload_image(
        self,
        footprint_id: int,
        user_id: int,
        image_data: bytes,
        content_type: str,
        sort_order: int | None = None,
    ) -> FootprintImage:
        fp = await self._get_own_footprint(footprint_id, user_id)

        # 缩略图（地图 Marker 用）
        thumb_data = await asyncio.to_thread(
            generate_thumbnail, image_data, (400, 400)
        )
        original_url = await asyncio.to_thread(
            upload_image, "footprints/original", image_data, content_type
        )
        thumbnail_url = await asyncio.to_thread(
            upload_image, "footprints/thumb", thumb_data, content_type
        )

        # 排序：若未传则排在当前最后
        if sort_order is None:
            max_order = await self.db.scalar(
                select(func.coalesce(func.max(FootprintImage.sort_order), -1)).where(
                    FootprintImage.footprint_id == footprint_id
                )
            )
            sort_order = (max_order or -1) + 1

        img = FootprintImage(
            footprint_id=footprint_id,
            original_url=original_url,
            thumbnail_url=thumbnail_url,
            sort_order=sort_order,
        )
        self.db.add(img)
        await self.db.flush()
        await self.db.refresh(img)

        # 更新足迹图片数；若为首图则设封面
        fp.image_count += 1
        if not fp.cover_thumbnail_url:
            fp.cover_thumbnail_url = thumbnail_url
        await self.db.flush()
        await self.db.refresh(fp)

        # 更新旅程图片总数
        await self.db.execute(
            update(Travel)
            .where(Travel.id == fp.travel_id)
            .values(image_count=Travel.image_count + 1)
        )
        await self.db.flush()
        return img

    # ---------- 批量排序 ----------

    async def reorder(
        self,
        travel_id: int,
        user_id: int,
        items: list[tuple[int, int]],
    ) -> None:
        """items: [(footprint_id, sort_order), ...]"""
        await self._get_own_travel(travel_id, user_id)
        for fid, order in items:
            await self.db.execute(
                update(Footprint)
                .where(Footprint.id == fid, Footprint.travel_id == travel_id)
                .values(sort_order=order)
            )
        await self.db.flush()

    # ---------- 内部 ----------

    async def _get_own_travel(self, travel_id: int, user_id: int) -> Travel:
        travel = await self.db.get(Travel, travel_id)
        if travel is None:
            raise ValueError("旅程不存在")
        if travel.user_id != user_id:
            raise PermissionError("无权操作此旅程")
        return travel

    async def _get_own_footprint(self, footprint_id: int, user_id: int) -> Footprint:
        fp = await self.db.get(Footprint, footprint_id)
        if fp is None:
            raise ValueError("足迹不存在")
        if fp.user_id != user_id:
            raise PermissionError("无权操作此足迹")
        return fp
