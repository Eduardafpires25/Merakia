from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.database.models.enums import OrderStatus, UserRole
from src.database.models.seller_profile import SellerProfile
from src.database.models.user import User
from src.api.dependencies.auth import get_current_active_user
from src.api.models.review import (
    ReviewCreateRequest,
    ReviewResponse,
    ReviewUpdateRequest,
    SellerReviewsListResponse,
)
from src.api.repositories.order_repository import OrderRepository
from src.api.repositories.review_repository import ReviewRepository
from src.api.repositories.seller_repository import SellerRepository

logger = logging.getLogger("MeraKia.Reviews")

router = APIRouter(tags=["reviews"])


@router.post("/orders/{order_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_order_review(
    order_id: uuid.UUID,
    body: ReviewCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Cliente cria uma avaliação para o pedido entregue ou concluído.
    Garante resiliência histórica gravando snapshots do nome e título do produto.
    """
    order_repo = OrderRepository(db)
    review_repo = ReviewRepository(db)

    order = order_repo.get_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado.",
        )

    if order.client_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o comprador pode avaliar este pedido.",
        )

    if order.status not in (OrderStatus.DELIVERED, OrderStatus.COMPLETED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você só pode avaliar o pedido após a entrega ou conclusão.",
        )

    if not order.seller_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este pedido não possui um vendedor associado.",
        )

    existing = review_repo.get_by_order_id(order_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este pedido já possui uma avaliação. Você pode editá-la se desejar.",
        )

    review = review_repo.create(
        order_id=order.id,
        seller_id=order.seller_id,
        client_id=current_user.id,
        client_name=current_user.name or "Cliente MeraKia",
        product_title=order.title,
        rating=body.rating,
        comment=body.comment,
    )

    logger.info("Avaliação criada: id=%s order=%s rating=%d", review.id, order.id, review.rating)
    return review


@router.get("/orders/{order_id}/reviews", response_model=ReviewResponse)
def get_order_review(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retorna a avaliação registrada para o pedido especificado."""
    order_repo = OrderRepository(db)
    review_repo = ReviewRepository(db)

    order = order_repo.get_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado.",
        )

    if (
        order.client_id != current_user.id
        and order.seller_id != current_user.id
        and current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para visualizar a avaliação deste pedido.",
        )

    review = review_repo.get_by_order_id(order_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma avaliação encontrada para este pedido.",
        )

    return review


@router.put("/orders/{order_id}/reviews", response_model=ReviewResponse)
def update_order_review(
    order_id: uuid.UUID,
    body: ReviewUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Cliente edita uma avaliação previamente realizada.
    Marca is_edited=True e atualiza o timestamp de alteração.
    """
    order_repo = OrderRepository(db)
    review_repo = ReviewRepository(db)

    order = order_repo.get_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado.",
        )

    if order.client_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o comprador pode editar esta avaliação.",
        )

    review = review_repo.get_by_order_id(order_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma avaliação encontrada para este pedido para editar.",
        )

    updated = review_repo.update(
        review,
        rating=body.rating,
        comment=body.comment,
    )

    logger.info("Avaliação atualizada: id=%s rating=%d (editada)", updated.id, updated.rating)
    return updated


@router.get("/sellers/{slug_or_id}/reviews", response_model=SellerReviewsListResponse)
def list_seller_reviews(
    slug_or_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Lista pública de avaliações da loja do vendedor.
    Retorna a média de estrelas, o total e os depoimentos dos clientes.
    """
    seller_repo = SellerRepository(db)
    review_repo = ReviewRepository(db)

    # Tenta por UUID ou por slug
    seller_profile: Optional[SellerProfile] = None
    try:
        seller_uuid = uuid.UUID(slug_or_id)
        seller_profile = seller_repo.get_by_user_id(seller_uuid) or db.query(SellerProfile).filter(SellerProfile.id == seller_uuid).first()
    except ValueError:
        seller_profile = seller_repo.get_by_slug(slug_or_id)

    if not seller_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendedor não encontrado.",
        )

    items, total = review_repo.list_for_seller(seller_profile.user_id, skip=skip, limit=limit)
    avg_rating, total_count, distribution = review_repo.get_seller_stats(seller_profile.user_id)

    return SellerReviewsListResponse(
        items=items,
        total=total,
        average_rating=avg_rating,
        rating_distribution=distribution,
    )
