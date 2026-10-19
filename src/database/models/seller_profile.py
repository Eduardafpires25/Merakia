from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base
from src.database.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from src.database.models.enums import SellerCategory

if TYPE_CHECKING:
    from src.database.models.user import User
    from src.database.models.seller_product_spec import SellerProductSpec


class SellerProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Perfil estendido para usuarios com role=SELLER.
    Guarda informacoes especificas da loja e suas regras de producao.
    """

    __tablename__ = "seller_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Identidade da loja
    store_name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Segmento principal (caneca, camiseta, etc)
    category: Mapped[SellerCategory] = mapped_column(
        SAEnum(SellerCategory, name="seller_category", native_enum=False, length=30),
        nullable=False,
        default=SellerCategory.OTHER,
    )

    # Contato e localizacao basica (opcional)
    whatsapp: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    instagram: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Politica de produção
    accepts_custom_designs: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    min_order_quantity: Mapped[int] = mapped_column(default=1, nullable=False)
    estimated_days: Mapped[Optional[int]] = mapped_column(nullable=True)

    is_open: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Imagens (chaves internas do storage; URLs geradas via image_service)
    logo_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    banner_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Dados de recebimento via PIX
    pix_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pix_key_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="seller_profile")
    product_specs: Mapped[List["SellerProductSpec"]] = relationship(
        "SellerProductSpec",
        back_populates="seller",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SellerProfile id={self.id} store={self.store_name} category={self.category}>"
