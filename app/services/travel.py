import asyncio
from datetime import date

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.models.travel import Travel
from app.utils.oss import upload_image, generate_thumbnail, url_to_key, delete_object

REDIS_VIEW_PREFIX = "travel:view:"
VIEW_COUNT_FLUSH_THRESHOLD = 10


class TravelService:

    def __init__(self, db: AsyncSession, rds: redis.Redis):
        self.db = db
        self.rds = rds

    # ---------- 创建旅程 ----------

    async def create(
        self,
        user_id: int,
        title: str,
        description: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        is_public: bool = True,
    ) -> Travel:
        if start_date and end_date and end_date < start_date:
            raise ValueError("结束日期不能早于出发日期")

        travel = Travel(
            user_id=user_id,
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            is_public=int(is_public),
        )
        self.db.add(travel)
        await self.db.flush()
        await self.db.refresh(travel)
        return travel

    # ---------- 更新旅程 ----------

    async def update_travel(
        self,
        travel_id: int,
        user_id: int,
        **fields,
    ) -> Travel:
        travel = await self._get_own_travel(travel_id, user_id)

        for key, value in fields.items():
            if value is None:
                continue
            if key == "is_public":
                value = int(value)
            setattr(travel, key, value)

        if travel.start_date and travel.end_date and travel.end_date < travel.start_date:
            raise ValueError("结束日期不能早于出发日期")

        await self.db.flush()
        await self.db.refresh(travel)
        return travel

    # ---------- 更新状态 ----------

    async def update_status(self, travel_id: int, user_id: int, status: int) -> Travel:
        travel = await self._get_own_travel(travel_id, user_id)

        if status == 1:
            ongoing = await self.db.scalar(
                select(Travel).where(
                    Travel.user_id == user_id,
                    Travel.status == 1,
                    Travel.id != travel_id,
                )
            )
            if ongoing:
                raise ValueError(f"你已有进行中的旅程「{ongoing.title}」，请先结束后再开始新旅程")

        travel.status = status
        await self.db.flush()
        await self.db.refresh(travel)
        return travel

    # ---------- 上传封面 ----------

    async def upload_cover(
        self, travel_id: int, user_id: int, image_data: bytes, content_type: str
    ) -> Travel:
        travel = await self._get_own_travel(travel_id, user_id)

        if travel.cover_image_url:
            old_key = url_to_key(travel.cover_image_url)
            if old_key:
                await asyncio.to_thread(delete_object, old_key)

        thumb_data = await asyncio.to_thread(generate_thumbnail, image_data, (800, 800))
        url = await asyncio.to_thread(upload_image, "covers", thumb_data, content_type)

        travel.cover_image_url = url
        await self.db.flush()
        await self.db.refresh(travel)
        return travel

    # ---------- 删除旅程 ----------

    async def delete(self, travel_id: int, user_id: int) -> None:
        travel = await self._get_own_travel(travel_id, user_id)

        if travel.cover_image_url:
            old_key = url_to_key(travel.cover_image_url)
            if old_key:
                await asyncio.to_thread(delete_object, old_key)

        await self.db.delete(travel)
        await self.db.flush()

    # ---------- 获取详情 ----------

    async def get_detail(self, travel_id: int, viewer_id: int | None = None) -> Travel:
        travel = await self.db.get(Travel, travel_id)
        if travel is None:
            raise ValueError("旅程不存在")

        if not travel.is_public and travel.user_id != viewer_id:
            raise PermissionError("无权查看此旅程")

        return travel

    # ---------- 浏览量 +1（Redis 缓冲写入） ----------

    async def increment_view(self, travel_id: int, viewer_id: int | None = None) -> int:
        travel = await self.get_detail(travel_id, viewer_id)

        rds_key = f"{REDIS_VIEW_PREFIX}{travel_id}"
        count = await self.rds.incr(rds_key)

        if count >= VIEW_COUNT_FLUSH_THRESHOLD:
            await self.rds.delete(rds_key)
            await self.db.execute(
                update(Travel)
                .where(Travel.id == travel_id)
                .values(view_count=Travel.view_count + count)
            )
            await self.db.flush()
            await self.db.refresh(travel)

        return travel.view_count + count

    # ---------- 我的旅程列表 ----------

    async def list_my_travels(
        self, user_id: int, page: int = 1, page_size: int = 20, status: int | None = None
    ) -> tuple[list[Travel], int]:
        conditions = [Travel.user_id == user_id]
        if status is not None:
            conditions.append(Travel.status == status)

        total = await self.db.scalar(
            select(func.count()).select_from(Travel).where(*conditions)
        )
        total = total or 0

        stmt = (
            select(Travel)
            .where(*conditions)
            .order_by(Travel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    # ---------- 公开旅程列表 ----------

    async def list_public_travels(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[Travel], int]:
        conditions = [Travel.is_public == 1]

        total = await self.db.scalar(
            select(func.count()).select_from(Travel).where(*conditions)
        )
        total = total or 0

        stmt = (
            select(Travel)
            .where(*conditions)
            .order_by(Travel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    # ---------- 获取用户当前进行中的旅程 ----------

    async def get_ongoing_travel(self, user_id: int) -> Travel | None:
        return await self.db.scalar(
            select(Travel).where(Travel.user_id == user_id, Travel.status == 1)
        )

    # ---------- 内部方法 ----------

    async def _get_own_travel(self, travel_id: int, user_id: int) -> Travel:
        travel = await self.db.get(Travel, travel_id)
        if travel is None:
            raise ValueError("旅程不存在")
        if travel.user_id != user_id:
            raise PermissionError("无权操作此旅程")
        return travel
