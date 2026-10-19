from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreateRequest(BaseModel):
    """Request para criar avaliação do pedido."""
    rating: int = Field(..., ge=1, le=5, description="Nota de 1 a 5 estrelas")
    comment: Optional[str] = Field(None, max_length=1500, description="Comentário sobre o produto e atendimento")


class ReviewUpdateRequest(BaseModel):
    """Request para editar avaliação existente."""
    rating: int = Field(..., ge=1, le=5, description="Nota de 1 a 5 estrelas")
    comment: Optional[str] = Field(None, max_length=1500, description="Comentário atualizado")


class ReviewResponse(BaseModel):
    """Resposta com dados completos de uma avaliação."""
    id: uuid.UUID
    order_id: Optional[uuid.UUID] = None
    seller_id: uuid.UUID
    client_id: Optional[uuid.UUID] = None
    client_name: str
    product_title: Optional[str] = None
    rating: int
    comment: Optional[str] = None
    is_edited: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SellerReviewsListResponse(BaseModel):
    """Resposta paginada de avaliações da loja do vendedor."""
    items: List[ReviewResponse]
    total: int
    average_rating: float
    rating_distribution: dict[int, int] = Field(default_factory=dict)
