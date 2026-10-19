from __future__ import annotations

from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CartItemCreateRequest(BaseModel):
    """Request para adicionar um item ao carrinho."""
    
    # Para produtos não personalizáveis
    product_spec_id: Optional[UUID] = None
    
    # Para pedidos personalizáveis aceitos
    order_id: Optional[UUID] = None
    
    # Opções de personalização escolhidas (JSON string)
    selected_options: Optional[str] = None
    
    # Quantidade (default 1)
    quantity: int = Field(default=1, ge=1, le=100)


class CartItemUpdateRequest(BaseModel):
    """Request para atualizar um item do carrinho."""
    
    quantity: int = Field(..., ge=1, le=100)


class CartItemResponse(BaseModel):
    """Response de um item do carrinho."""
    
    id: UUID
    user_id: UUID
    seller_id: UUID
    product_spec_id: Optional[UUID] = None
    order_id: Optional[UUID] = None
    selected_options: Optional[str] = None
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    """Response do carrinho completo do usuário."""
    
    items: list[CartItemResponse]
    total: Decimal
    total_items: int
    
    # Itens agrupados por seller para facilitar checkout por loja
    grouped_by_seller: dict[str, list[CartItemResponse]]


class CartCheckoutRequest(BaseModel):
    """Request para fazer checkout do carrinho."""
    
    # IDs dos sellers para os quais fazer checkout (pode ser um subset do carrinho)
    seller_ids: list[UUID]
    
    # Endereço de entrega
    shipping_address: str
    shipping_number: Optional[str] = None
    shipping_complement: Optional[str] = None
    shipping_neighborhood: Optional[str] = None
    shipping_city: str
    shipping_state: str
    shipping_zip_code: str
    shipping_phone: str

    @field_validator("shipping_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Valida formato de telefone internacional."""
        # Remove caracteres não numéricos (incluindo o +)
        numbers_only = "".join(filter(str.isdigit, v))
        # Valida telefone: mínimo 10 dígitos (DDD + número), máximo 15 (código internacional + DDD + número)
        if len(numbers_only) < 10 or len(numbers_only) > 15:
            raise ValueError("Telefone deve ter entre 10 e 15 dígitos (incluindo código internacional).")
        return numbers_only
    
    # Observações para o pedido
    notes: Optional[str] = None
    
    # Salvar este endereço no perfil do usuário para próximas compras
    save_address_to_profile: Optional[bool] = True

    # Ignorar erros durante o checkout (só funciona quando DEV_MODE=True)
    ignore_errors: Optional[bool] = False



class CartCheckoutResponse(BaseModel):
    """Response do checkout do carrinho."""
    
    # IDs dos pedidos criados (um por seller)
    order_ids: list[UUID]
    
    # Valor total do checkout
    total_amount: Decimal
    
    # Mensagem de confirmação
    message: str

    # Dados de pagamento PIX em custódia
    payment_id: Optional[UUID] = None
    pix_code: Optional[str] = None
    pix_qr_code: Optional[str] = None
    payment_status: Optional[str] = None
