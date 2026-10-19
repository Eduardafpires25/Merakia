from __future__ import annotations

import re
import unicodedata
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.database.models.enums import SellerCategory


def slugify(value: str) -> str:
    """Gera slug a partir de uma string."""
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower())
    value = re.sub(r"[-\s]+", "-", value).strip("-")
    return value


# =============================================================================
# Seller Profile Models
# =============================================================================

class SellerProfileBase(BaseModel):
    store_name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = Field(None, max_length=2000)
    category: SellerCategory
    whatsapp: Optional[str] = Field(None, max_length=30)
    instagram: Optional[str] = Field(None, max_length=60)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    accepts_custom_designs: bool = True
    min_order_quantity: int = Field(default=1, ge=1)
    estimated_days: Optional[int] = Field(None, ge=1, le=365)
    pix_key: Optional[str] = Field(None, max_length=100)
    pix_key_type: Optional[str] = Field(None, max_length=30)


class SellerProfileCreate(SellerProfileBase):
    """Modelo para criar perfil de seller."""
    slug: Optional[str] = Field(
        None,
        min_length=2,
        max_length=160,
        description="Slug da loja (gerado automaticamente se não fornecido)",
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        slug = slugify(v)
        if not slug:
            raise ValueError("Slug inválido.")
        return slug


class SellerProfileUpdate(BaseModel):
    """Modelo para atualizar perfil de seller (todos campos opcionais)."""
    store_name: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[SellerCategory] = None
    whatsapp: Optional[str] = Field(None, max_length=30)
    instagram: Optional[str] = Field(None, max_length=60)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    accepts_custom_designs: Optional[bool] = None
    min_order_quantity: Optional[int] = Field(None, ge=1)
    estimated_days: Optional[int] = Field(None, ge=1, le=365)
    is_open: Optional[bool] = None
    pix_key: Optional[str] = Field(None, max_length=100)
    pix_key_type: Optional[str] = Field(None, max_length=30)


class SellerProfileResponse(BaseModel):
    """Resposta completa do perfil de seller."""
    id: uuid.UUID
    user_id: uuid.UUID
    store_name: str
    slug: str
    description: Optional[str] = None
    category: SellerCategory
    whatsapp: Optional[str] = None
    instagram: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    accepts_custom_designs: bool
    min_order_quantity: int
    estimated_days: Optional[int] = None
    is_open: bool
    pix_key: Optional[str] = None
    pix_key_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # URLs de imagens (geradas dinamicamente)
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    # Dados do usuário (agregados)
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_avatar_url: Optional[str] = None
    # Reputação e avaliações da loja
    average_rating: Optional[float] = None
    total_reviews: int = 0

    model_config = ConfigDict(from_attributes=True)


class SellerProfileListItem(BaseModel):
    """Item simplificado para listagem pública de sellers."""
    id: uuid.UUID
    store_name: str
    slug: str
    description: Optional[str] = None
    category: SellerCategory
    whatsapp: Optional[str] = None
    instagram: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    accepts_custom_designs: bool = False
    min_order_quantity: int
    estimated_days: Optional[int] = None
    is_open: bool = True
    user_name: Optional[str] = None
    logo_url: Optional[str] = None
    average_rating: Optional[float] = None
    total_reviews: int = 0

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Seller Product Spec Models
# =============================================================================

class ProductSpecBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = Field(None, max_length=2000)
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Atributos livres (ex.: {'volume_ml': 250, 'color': 'white'})",
    )
    is_customizable: bool = Field(default=False, description="Se o produto permite personalização via IA")
    customization_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Opções de personalização (obrigatório quando is_customizable=True, ex.: {'sizes': ['250ml', '300ml', '500ml'], 'materials': ['ceramic', 'glass']})",
    )
    base_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)

    @field_validator("customization_options")
    @classmethod
    def validate_customization_options(cls, v: Optional[Dict[str, Any]], info) -> Optional[Dict[str, Any]]:
        if info.data.get("is_customizable") is True and (v is None or v == {}):
            raise ValueError("customization_options é obrigatório quando is_customizable=True")
        return v


class ProductSpecCreate(ProductSpecBase):
    """Modelo para criar especificação de produto."""
    pass


class ProductSpecUpdate(BaseModel):
    """Modelo para atualizar especificação (todos campos opcionais)."""
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = Field(None, max_length=2000)
    attributes: Optional[Dict[str, Any]] = None
    is_customizable: Optional[bool] = None
    customization_options: Optional[Dict[str, Any]] = None
    base_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    is_active: Optional[bool] = None


class ProductSpecResponse(BaseModel):
    """Resposta completa da especificação de produto."""
    id: uuid.UUID
    seller_id: uuid.UUID
    name: str
    description: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    is_customizable: bool = False
    customization_options: Optional[Dict[str, Any]] = None
    base_price: Optional[Decimal] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    images: List["ProductImageResponse"] = Field(default_factory=list)
    cover_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductSpecListItem(BaseModel):
    """Item simplificado para listagem de produtos."""
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_customizable: bool = False
    customization_options: Optional[Dict[str, Any]] = None
    base_price: Optional[Decimal] = None
    is_active: bool
    cover_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Product Image Models
# =============================================================================

class ProductImageResponse(BaseModel):
    """Imagem de um produto."""
    id: uuid.UUID
    product_spec_id: uuid.UUID
    url: str
    alt_text: Optional[str] = None
    position: int
    is_cover: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductImageUpdate(BaseModel):
    """Atualizar metadados de imagem (sem trocar arquivo)."""
    alt_text: Optional[str] = Field(None, max_length=255)
    position: Optional[int] = Field(None, ge=0)
    is_cover: Optional[bool] = None


# =============================================================================
# List Response Models (with pagination)
# =============================================================================

class PaginatedResponse(BaseModel):
    """Modelo base para respostas paginadas."""
    total: int
    skip: int
    limit: int


class SellerListResponse(PaginatedResponse):
    """Resposta paginada de sellers."""
    items: List[SellerProfileListItem]


class ProductSpecListResponse(PaginatedResponse):
    """Resposta paginada de especificações de produtos."""
    items: List[ProductSpecListItem]


# =============================================================================
# Seller Detail (with products)
# =============================================================================

class SellerDetailResponse(SellerProfileResponse):
    """Resposta detalhada do seller incluindo produtos."""
    products: List[ProductSpecListItem] = Field(default_factory=list)
