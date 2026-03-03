from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    String,
    Text,
    Integer,
    SmallInteger,
    DateTime,
    Numeric,
    ForeignKey,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Footprint(Base):
    __tablename__ = "footprint"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    travel_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("travel.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )

    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    location_name: Mapped[str] = mapped_column(String(255), default="")
    address: Mapped[str] = mapped_column(String(500), default="")
    district: Mapped[str] = mapped_column(String(100), default="")
    city_name: Mapped[str] = mapped_column(String(100), default="")
    province_name: Mapped[str] = mapped_column(String(100), default="")
    country_name: Mapped[str] = mapped_column(String(100), default="")
    location_adjusted: Mapped[bool] = mapped_column(SmallInteger, default=0)

    description: Mapped[str | None] = mapped_column(Text, default=None)
    cover_thumbnail_url: Mapped[str] = mapped_column(String(500), default="")
    image_count: Mapped[int] = mapped_column(Integer, default=0)

    travel_time: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    travel = relationship("Travel", backref="footprints", lazy="selectin")
    owner = relationship("User", backref="footprints", lazy="selectin")
    images = relationship(
        "FootprintImage",
        back_populates="footprint",
        order_by="FootprintImage.sort_order",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class FootprintImage(Base):
    __tablename__ = "footprint_image"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    footprint_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("footprint.id", ondelete="CASCADE"), nullable=False
    )
    original_url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[str] = mapped_column(String(500), nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, default=None)
    height: Mapped[int | None] = mapped_column(Integer, default=None)
    size_kb: Mapped[int | None] = mapped_column(Integer, default=None)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    footprint = relationship("Footprint", back_populates="images")
