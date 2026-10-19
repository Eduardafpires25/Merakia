from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Enum as SAEnum, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base
from src.database.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from src.database.models.enums import UserRole

if TYPE_CHECKING:
    from src.database.models.order import Order
    from src.database.models.token import Token
    from src.database.models.seller_profile import SellerProfile


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", native_enum=False, length=20),
        nullable=False,
        default=UserRole.CLIENT,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_verification_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Avatar (chave interna do storage; URL gerada dinamicamente via image_service)
    avatar_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Endereço de entrega padrão do usuário
    zip_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    complement: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    neighborhood: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Pedidos feitos por este usuario (quando role=client)
    orders_as_client: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="client",
        foreign_keys="Order.client_id",
        cascade="all, delete-orphan",
    )
    # Pedidos atendidos por este usuario (quando role=seller)
    orders_as_seller: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="seller",
        foreign_keys="Order.seller_id",
    )
    tokens: Mapped[List["Token"]] = relationship(
        "Token",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    # Perfil de loja (so existe quando role=SELLER)
    seller_profile: Mapped[Optional["SellerProfile"]] = relationship(
        "SellerProfile",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email} role={self.role}>"
