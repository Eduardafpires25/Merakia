"""ORM models for MeraKia.

Importing this package registers all models on the shared `Base.metadata`,
which is required for Alembic autogenerate to detect them.
"""
from src.database.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from src.database.models.enums import (
    UserRole,
    OrderStatus,
    IterationStatus,
    SellerCategory,
)
from src.database.models.user import User
from src.database.models.order import Order
from src.database.models.token import Token
from src.database.models.project_iteration import ProjectIteration
from src.database.models.order_status_history import OrderStatusHistory
from src.database.models.ai_generation import AIGeneration
from src.database.models.seller_profile import SellerProfile
from src.database.models.seller_product_spec import SellerProductSpec
from src.database.models.seller_product_image import SellerProductImage
from src.database.models.order_reference_image import OrderReferenceImage
from src.database.models.cart_item import CartItem
from src.database.models.payment import Payment, PaymentStatus
from src.database.models.order_review import OrderReview

__all__ = [
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "UserRole",
    "OrderStatus",
    "IterationStatus",
    "SellerCategory",
    "PaymentStatus",
    "User",
    "Order",
    "Token",
    "ProjectIteration",
    "OrderStatusHistory",
    "AIGeneration",
    "SellerProfile",
    "SellerProductSpec",
    "SellerProductImage",
    "OrderReferenceImage",
    "CartItem",
    "Payment",
    "OrderReview",
]
