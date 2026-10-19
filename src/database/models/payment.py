from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base
from src.database.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.database.models.user import User
    from src.database.models.order import Order


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"          # PIX gerado para a plataforma, aguardando pagamento
    PAID = "paid"                # Pago pelo cliente, retido em custódia na plataforma
    FAILED = "failed"            # Falha ou expiração no pagamento
    RELEASED = "released"        # Liberado e repassado para a chave PIX do vendedor
    REFUNDED = "refunded"        # Estornado ao cliente


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Registro de pagamento intermediado em custódia (escrow) pela plataforma.
    O valor fica retido até que o cliente confirme a entrega do pedido.
    """
    __tablename__ = "payments"

    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status", native_enum=False, length=30),
        nullable=False,
        default=PaymentStatus.PENDING,
        index=True,
    )

    # Dados do PIX para a plataforma
    pix_code: Mapped[str] = mapped_column(Text, nullable=False)
    pix_qr_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Imagem ou SVG/Base64

    # Dados do repasse para o vendedor
    seller_pix_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    seller_pix_key_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    seller: Mapped["User"] = relationship("User", foreign_keys=[seller_id])
    order: Mapped[Optional["Order"]] = relationship("Order", foreign_keys=[order_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Payment id={self.id} amount={self.amount} status={self.status}>"
