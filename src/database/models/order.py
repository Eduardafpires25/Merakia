from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base
from src.database.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from src.database.models.enums import OrderStatus

if TYPE_CHECKING:
    from src.database.models.user import User
    from src.database.models.project_iteration import ProjectIteration
    from src.database.models.order_status_history import OrderStatusHistory
    from src.database.models.order_reference_image import OrderReferenceImage
    from src.database.models.order_review import OrderReview


class Order(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orders"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    product_type: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    product_options: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict, server_default=text("'{}'"))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    estimated_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status", native_enum=False, length=30),
        nullable=False,
        default=OrderStatus.DRAFT,
        index=True,
    )

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seller_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    approved_iteration_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_iterations.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
    )

    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Informações de envio
    shipping_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    shipping_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    shipping_complement: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    shipping_neighborhood: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    shipping_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    shipping_state: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    shipping_zip_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    shipping_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    client: Mapped["User"] = relationship(
        "User", back_populates="orders_as_client", foreign_keys=[client_id]
    )
    seller: Mapped[Optional["User"]] = relationship(
        "User", back_populates="orders_as_seller", foreign_keys=[seller_id]
    )
    iterations: Mapped[List["ProjectIteration"]] = relationship(
        "ProjectIteration",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="ProjectIteration.version",
        foreign_keys="ProjectIteration.order_id",
    )
    approved_iteration: Mapped[Optional["ProjectIteration"]] = relationship(
        "ProjectIteration",
        foreign_keys=[approved_iteration_id],
        post_update=True,
    )
    status_history: Mapped[List["OrderStatusHistory"]] = relationship(
        "OrderStatusHistory",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderStatusHistory.created_at",
    )
    reference_images: Mapped[List["OrderReferenceImage"]] = relationship(
        "OrderReferenceImage",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderReferenceImage.position",
    )
    review: Mapped[Optional["OrderReview"]] = relationship(
        "OrderReview",
        uselist=False,
        back_populates="order",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Order id={self.id} status={self.status} client_id={self.client_id}>"
