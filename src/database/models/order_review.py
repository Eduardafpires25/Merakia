from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base
from src.database.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.database.models.user import User
    from src.database.models.order import Order


class OrderReview(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Avaliação de pedido entregue / concluído.
    
    Resiliência:
    Mantém snapshots (`client_name`, `product_title`) para que a reputação e o histórico
    da loja persistam mesmo se o pedido, o produto ou o usuário forem posteriormente excluídos.
    """
    __tablename__ = "order_reviews"

    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        index=True,
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Snapshots para resiliência histórica
    client_name: Mapped[str] = mapped_column(String(150), nullable=False, default="Cliente")
    product_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Avaliação (1 a 5 estrelas)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Flag e rastreamento de edição
    is_edited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    order: Mapped[Optional["Order"]] = relationship("Order", foreign_keys=[order_id], back_populates="review")
    seller: Mapped["User"] = relationship("User", foreign_keys=[seller_id])
    client: Mapped[Optional["User"]] = relationship("User", foreign_keys=[client_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<OrderReview id={self.id} order_id={self.order_id} rating={self.rating}>"
