from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.database.models.enums import IterationStatus, OrderStatus


# =============================================================================
# Iteration
# =============================================================================

class IterationCreateRequest(BaseModel):
    """Cliente cria nova iteracao com descricao customizada."""
    description: str = Field(..., min_length=5, max_length=2000)


class IterationResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    version: int
    description: str
    prompt: Optional[str] = None
    image_url: Optional[str] = None
    image_key: Optional[str] = None
    ai_model: Optional[str] = None
    status: IterationStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Order
# =============================================================================

class OrderCreateRequest(BaseModel):
    """Cliente cria pedido (draft) destinado a um seller."""
    seller_id: uuid.UUID = Field(..., description="ID do User com role=seller")
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5, max_length=2000)
    product_type: Optional[str] = Field(None, max_length=80, description="Ex.: 'caneca 250ml branca'")
    product_options: Optional[Dict[str, str]] = Field(None, description="Opções selecionadas do produto personalizável (ex.: {'size': '250ml', 'material': 'ceramic'})")
    quantity: int = Field(1, ge=1, le=10000)


class OrderUpdateRequest(BaseModel):
    """Cliente atualiza dados do pedido (apenas em DRAFT)."""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=5, max_length=2000)
    product_type: Optional[str] = Field(None, max_length=80)
    quantity: Optional[int] = Field(None, ge=1, le=10000)


class StatusHistoryItem(BaseModel):
    id: uuid.UUID
    from_status: Optional[OrderStatus] = None
    to_status: OrderStatus
    note: Optional[str] = None
    changed_by_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderReferenceImageResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    image_key: str
    image_url: Optional[str] = None
    caption: Optional[str] = None
    position: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    product_type: Optional[str] = None
    product_options: Dict[str, Any] = Field(default_factory=dict)
    quantity: int
    estimated_price: Optional[Decimal] = None
    status: OrderStatus

    client_id: uuid.UUID
    seller_id: Optional[uuid.UUID] = None
    approved_iteration_id: Optional[uuid.UUID] = None

    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Informações de envio
    shipping_address: Optional[str] = None
    shipping_number: Optional[str] = None
    shipping_complement: Optional[str] = None
    shipping_neighborhood: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_zip_code: Optional[str] = None
    shipping_phone: Optional[str] = None

    # Imagem do produto (para produtos regulares)
    image_url: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    iterations: List[IterationResponse] = Field(default_factory=list)
    approved_iteration: Optional[IterationResponse] = None
    reference_images: List[OrderReferenceImageResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class OrderListItem(BaseModel):
    """Item simplificado para listagem."""
    id: uuid.UUID
    title: str
    product_type: Optional[str] = None
    quantity: int
    status: OrderStatus
    seller_id: Optional[uuid.UUID] = None
    client_id: uuid.UUID
    cover_url: Optional[str] = None  # URL da iteracao aprovada (se houver)
    submitted_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    items: List[OrderListItem]
    total: int
    skip: int
    limit: int


# =============================================================================
# Seller actions
# =============================================================================

class SellerDecisionRequest(BaseModel):
    """Seller aceita ou rejeita pedido em IN_ANALYSIS."""
    accept: bool
    note: Optional[str] = Field(None, max_length=500)
    estimated_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)


class StatusUpdateRequest(BaseModel):
    """Seller atualiza status (APPROVED -> IN_PRODUCTION -> COMPLETED)."""
    status: OrderStatus
    note: Optional[str] = Field(None, max_length=500)


class CancelRequest(BaseModel):
    """Cliente cancela pedido (apenas em DRAFT ou IN_ANALYSIS)."""
    note: Optional[str] = Field(None, max_length=500)


class MessageResponse(BaseModel):
    detail: str
