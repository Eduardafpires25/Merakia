from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.database.models.user import User
from src.database.models.seller_product_spec import SellerProductSpec
from src.database.models.order import Order
from src.database.models.enums import OrderStatus
from src.api.dependencies.auth import get_current_active_user
from src.api.repositories.cart_repository import CartRepository
from src.api.repositories.auth_repository import UserRepository
from src.api.repositories.order_repository import OrderRepository
from src.api.models.cart import (
    CartItemCreateRequest,
    CartItemUpdateRequest,
    CartItemResponse,
    CartResponse,
    CartCheckoutRequest,
    CartCheckoutResponse,
)
from src.storage import image_service
from src.api.services.pix_service import pix_service
from src.api.repositories.payment_repository import PaymentRepository
from src.database.models.payment import PaymentStatus
from config.logger import logger
from config.settings import settings

router = APIRouter(prefix="/cart", tags=["cart"])


def _cart_item_to_response(item) -> CartItemResponse:
    """Converte um CartItem para CartItemResponse."""
    return CartItemResponse(
        id=item.id,
        user_id=item.user_id,
        seller_id=item.seller_id,
        product_spec_id=item.product_spec_id,
        order_id=item.order_id,
        selected_options=item.selected_options,
        quantity=item.quantity,
        unit_price=item.unit_price,
        total_price=item.total_price,
        name=item.name,
        description=item.description,
        image_url=item.image_url,
        created_at=item.created_at.isoformat(),
        updated_at=item.updated_at.isoformat(),
    )


@router.get("/", response_model=CartResponse)
def get_cart(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retorna o carrinho do usuário atual."""
    repo = CartRepository(db)
    items = repo.list_for_user(current_user.id)
    total = repo.get_cart_total(current_user.id)
    total_items = repo.count_for_user(current_user.id)
    
    # Agrupa por seller
    grouped: dict[str, list[CartItemResponse]] = {}
    for item in items:
        seller_id_str = str(item.seller_id)
        if seller_id_str not in grouped:
            grouped[seller_id_str] = []
        grouped[seller_id_str].append(_cart_item_to_response(item))
    
    return CartResponse(
        items=[_cart_item_to_response(item) for item in items],
        total=total,
        total_items=total_items,
        grouped_by_seller=grouped,
    )


@router.post("/items", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_cart(
    body: CartItemCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Adiciona um item ao carrinho.
    
    Para produtos não personalizáveis: forneça product_spec_id
    Para pedidos personalizáveis aceitos: forneça order_id
    """
    # Validação: deve fornecer product_spec_id ou order_id, mas não ambos
    if body.product_spec_id and body.order_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Forneça apenas product_spec_id ou order_id, não ambos.",
        )
    if not body.product_spec_id and not body.order_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Forneça product_spec_id ou order_id.",
        )
    
    repo = CartRepository(db)
    user_repo = UserRepository(db)
    
    seller_id: uuid.UUID
    unit_price: Decimal
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    
    if body.product_spec_id:
        # Produto não personalizável
        product_repo = db.query(SellerProductSpec).filter(
            SellerProductSpec.id == body.product_spec_id
        ).first()
        if not product_repo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto não encontrado.",
            )
        if not product_repo.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Produto não está ativo.",
            )
        if not product_repo.base_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Produto não tem preço definido.",
            )
        
        seller_profile = product_repo.seller
        seller_id = seller_profile.user_id
        unit_price = Decimal(str(product_repo.base_price))
        name = product_repo.name
        description = product_repo.description
        # Pega a primeira imagem se existir
        image_url = None
        if product_repo.images:
            image_url = image_service.get_url(product_repo.images[0].image_key)
        
    else:
        # Pedido personalizável aceito
        order_repo = OrderRepository(db)
        order = order_repo.get_by_id(body.order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido não encontrado.",
            )
        if order.client_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não é o cliente deste pedido.",
            )
        if order.status != OrderStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pedido não foi aprovado pelo seller.",
            )
        if not order.estimated_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pedido não tem preço estimado definido.",
            )
        
        seller_id = order.seller_id
        unit_price = Decimal(str(order.estimated_price))
        name = order.title
        description = order.description
        # Pega a imagem da iteração aprovada se existir
        image_url = None
        if order.approved_iteration and order.approved_iteration.image_key:
            image_url = image_service.get_url(order.approved_iteration.image_key)
    
    # Verifica se já existe item idêntico no carrinho
    existing = repo.find_existing_item(
        user_id=current_user.id,
        product_spec_id=body.product_spec_id,
        order_id=body.order_id,
        selected_options=body.selected_options,
    )
    
    if existing:
        # Atualiza quantidade do item existente
        new_quantity = existing.quantity + body.quantity
        updated = repo.update_quantity(existing, new_quantity)
        logger.info("Item atualizado no carrinho: %s (nova quantidade: %d)", updated.id, new_quantity)
        return _cart_item_to_response(updated)
    
    # Cria novo item no carrinho
    new_item = repo.create(
        user_id=current_user.id,
        seller_id=seller_id,
        quantity=body.quantity,
        unit_price=unit_price,
        name=name,
        description=description,
        image_url=image_url,
        selected_options=body.selected_options,
        product_spec_id=body.product_spec_id,
        order_id=body.order_id,
    )
    logger.info("Item adicionado ao carrinho: %s", new_item.id)
    return _cart_item_to_response(new_item)


@router.patch("/items/{item_id}", response_model=CartItemResponse)
def update_cart_item(
    item_id: uuid.UUID,
    body: CartItemUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Atualiza a quantidade de um item no carrinho."""
    repo = CartRepository(db)
    item = repo.get_by_id(item_id)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item do carrinho não encontrado.",
        )
    
    if item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para modificar este item.",
        )
    
    updated = repo.update_quantity(item, body.quantity)
    logger.info("Item do carrinho atualizado: %s (nova quantidade: %d)", updated.id, body.quantity)
    return _cart_item_to_response(updated)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_cart_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Remove um item do carrinho."""
    repo = CartRepository(db)
    item = repo.get_by_id(item_id)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item do carrinho não encontrado.",
        )
    
    if item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para remover este item.",
        )
    
    repo.delete(item)
    logger.info("Item removido do carrinho: %s", item_id)


@router.post("/checkout", response_model=CartCheckoutResponse)
def checkout_cart(
    body: CartCheckoutRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Faz checkout dos itens do carrinho para os sellers especificados.
    
    Para itens com order_id (pedidos personalizados aprovados): muda status para PAID.
    Para itens com product_spec_id (produtos regulares): cria novos pedidos (TODO).
    """
    repo = CartRepository(db)
    from src.api.repositories.order_repository import OrderRepository
    from src.database.models.enums import OrderStatus
    order_repo = OrderRepository(db)
    
    # Valida se forneceu sellers
    if not body.seller_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Forneça pelo menos um seller_id para checkout.",
        )
    
    # Busca itens do carrinho para os sellers especificados
    items = repo.list_for_user(current_user.id)
    filtered_items = [item for item in items if item.seller_id in body.seller_ids]
    
    if not filtered_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum item encontrado no carrinho para os sellers especificados.",
        )
    
    # Calcula total
    total_amount = sum(item.total_price for item in filtered_items)
    
    # Processa itens: para pedidos personalizados, muda status para PAID
    # Para produtos regulares, cria novos pedidos
    order_ids_updated = []
    for item in filtered_items:
        if item.order_id:
            # É um pedido personalizado aprovado - atualiza endereço e mantém APPROVED aguardando pagamento
            try:
                order = order_repo.get_by_id(item.order_id)
                if order and order.status in (OrderStatus.APPROVED, OrderStatus.DRAFT):
                    order_repo.update(
                        order,
                        shipping_address=body.shipping_address,
                        shipping_number=body.shipping_number,
                        shipping_complement=body.shipping_complement,
                        shipping_neighborhood=body.shipping_neighborhood,
                        shipping_city=body.shipping_city,
                        shipping_state=body.shipping_state,
                        shipping_zip_code=body.shipping_zip_code,
                        shipping_phone=body.shipping_phone,
                    )
                    order_ids_updated.append(str(item.order_id))
                    logger.info(f"Pedido {item.order_id} preparado para pagamento (aguardando confirmação PIX)")
            except Exception as e:
                if body.ignore_errors and settings.DEV_MODE:
                    logger.warning(f"DEV_MODE (ignore_errors=True): Erro ignorado no checkout do pedido {item.order_id}: {e}")
                    order_ids_updated.append(str(item.order_id))
                else:
                    raise
        elif item.product_spec_id:
            # É um produto regular - cria novo pedido em status APPROVED (aguardando pagamento)
            try:
                product_options = {}
                if item.selected_options:
                    try:
                        import json
                        product_options = json.loads(item.selected_options)
                    except json.JSONDecodeError:
                        product_options = {}
                
                # Cria novo pedido
                new_order = order_repo.create(
                    client_id=current_user.id,
                    seller_id=item.seller_id,
                    title=item.name,
                    description=item.description or "",
                    product_type=None,
                    product_options=product_options,
                    quantity=item.quantity,
                    shipping_address=body.shipping_address,
                    shipping_number=body.shipping_number,
                    shipping_complement=body.shipping_complement,
                    shipping_neighborhood=body.shipping_neighborhood,
                    shipping_city=body.shipping_city,
                    shipping_state=body.shipping_state,
                    shipping_zip_code=body.shipping_zip_code,
                    shipping_phone=body.shipping_phone,
                    image_url=item.image_url,
                )
                order_repo.update(new_order, estimated_price=item.total_price)
                order_repo.change_status(new_order, OrderStatus.APPROVED, changed_by_id=current_user.id, note="Pedido criado via carrinho (aguardando pagamento)")
                order_ids_updated.append(str(new_order.id))
                logger.info(f"Novo pedido {new_order.id} criado para produto regular {item.product_spec_id} em APPROVED")
            except Exception as e:
                if body.ignore_errors and settings.DEV_MODE:
                    logger.warning(f"DEV_MODE (ignore_errors=True): Erro ignorado ao criar pedido para produto {item.product_spec_id}: {e}")
                else:
                    raise

    
    # Remove os itens do carrinho após checkout
    for item in filtered_items:
        repo.delete(item)

    # Geração didática de cobrança PIX para plataforma intermediária (MeraKia)
    payment_repo = PaymentRepository(db)
    primary_order_id = uuid.UUID(order_ids_updated[0]) if order_ids_updated else None
    txid = f"MK{uuid.uuid4().hex[:16].upper()}"
    pix_code = pix_service.generate_pix_payload(
        amount=total_amount,
        txid=txid,
        description=f"Pedido MeraKia {order_ids_updated[0] if order_ids_updated else ''}",
    )
    pix_qr = pix_service.generate_qr_code_url(pix_code)

    payment = payment_repo.create(
        user_id=current_user.id,
        seller_id=filtered_items[0].seller_id,
        amount=total_amount,
        pix_code=pix_code,
        pix_qr_code=pix_qr,
        order_id=primary_order_id,
        status=PaymentStatus.PENDING,
    )

    # Salvar endereço no perfil do usuário se solicitado
    if getattr(body, "save_address_to_profile", True):
        try:
            from src.api.repositories.auth_repository import UserRepository
            user_repo = UserRepository(db)
            user_repo.update(
                current_user,
                zip_code=body.shipping_zip_code,
                address=body.shipping_address,
                number=body.shipping_number,
                complement=body.shipping_complement,
                neighborhood=body.shipping_neighborhood,
                city=body.shipping_city,
                state=body.shipping_state,
                phone=body.shipping_phone,
            )
            logger.info("Endereço salvo no perfil do usuário: %s", current_user.email)
        except Exception as e:
            logger.warning("Falha ao salvar endereço no perfil do usuário: %s", e)

    return CartCheckoutResponse(

        order_ids=[uuid.UUID(oid) for oid in order_ids_updated],
        total_amount=total_amount,
        message="Checkout realizado com sucesso! Cobrança PIX gerada pela plataforma MeraKia.",
        payment_id=payment.id,
        pix_code=payment.pix_code,
        pix_qr_code=payment.pix_qr_code,
        payment_status=payment.status.value,
    )
