from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.database.models.seller_profile import SellerProfile
from src.database.models.seller_product_spec import SellerProductSpec
from src.database.models.seller_product_image import SellerProductImage
from src.database.models.enums import SellerCategory
from src.api.models.seller import (
    SellerListResponse,
    SellerProfileListItem,
    SellerDetailResponse,
    ProductSpecListItem,
    ProductImageResponse,
)
from src.api.repositories.seller_repository import (
    SellerRepository,
    SellerProductSpecRepository,
)
from src.api.repositories.product_image_repository import SellerProductImageRepository
from src.api.repositories.review_repository import ReviewRepository
from src.storage import image_service

router = APIRouter(prefix="/sellers", tags=["sellers-public"])


def _url(key: Optional[str]) -> Optional[str]:
    return image_service.get_url(key) if key else None


def _image_to_response(img: SellerProductImage) -> ProductImageResponse:
    return ProductImageResponse(
        id=img.id,
        product_spec_id=img.product_spec_id,
        url=_url(img.image_key) or "",
        alt_text=img.alt_text,
        position=img.position,
        is_cover=img.is_cover,
        created_at=img.created_at,
    )


def _seller_to_list_item(seller: SellerProfile, db: Optional[Session] = None) -> SellerProfileListItem:
    avg_rating = None
    total_reviews = 0
    if db:
        review_repo = ReviewRepository(db)
        avg, count, _ = review_repo.get_seller_stats(seller.user_id)
        if count > 0:
            avg_rating = avg
            total_reviews = count

    return SellerProfileListItem(
        id=seller.id,
        store_name=seller.store_name,
        slug=seller.slug,
        description=seller.description,
        category=seller.category,
        whatsapp=seller.whatsapp,
        instagram=seller.instagram,
        city=seller.city,
        state=seller.state,
        accepts_custom_designs=seller.accepts_custom_designs,
        min_order_quantity=seller.min_order_quantity,
        estimated_days=seller.estimated_days,
        is_open=seller.is_open,
        user_name=seller.user.name if seller.user else None,
        logo_url=_url(seller.logo_key),
        average_rating=avg_rating,
        total_reviews=total_reviews,
    )


def _product_to_list_item(spec: SellerProductSpec) -> ProductSpecListItem:
    images = list(spec.images) if spec.images is not None else []
    cover = next((i for i in images if i.is_cover), images[0] if images else None)
    return ProductSpecListItem(
        id=spec.id,
        name=spec.name,
        description=spec.description,
        is_customizable=spec.is_customizable,
        customization_options=spec.customization_options,
        base_price=spec.base_price,
        is_active=spec.is_active,
        cover_url=_url(cover.image_key) if cover else None,
    )


def _seller_to_detail(
    seller: SellerProfile,
    products: List[SellerProductSpec],
    db: Optional[Session] = None,
) -> SellerDetailResponse:
    avg_rating = None
    total_reviews = 0
    if db:
        review_repo = ReviewRepository(db)
        avg, count, _ = review_repo.get_seller_stats(seller.user_id)
        if count > 0:
            avg_rating = avg
            total_reviews = count

    return SellerDetailResponse(
        id=seller.id,
        user_id=seller.user_id,
        store_name=seller.store_name,
        slug=seller.slug,
        description=seller.description,
        category=seller.category,
        whatsapp=seller.whatsapp,
        instagram=seller.instagram,
        city=seller.city,
        state=seller.state,
        accepts_custom_designs=seller.accepts_custom_designs,
        min_order_quantity=seller.min_order_quantity,
        estimated_days=seller.estimated_days,
        is_open=seller.is_open,
        created_at=seller.created_at,
        updated_at=seller.updated_at,
        logo_url=_url(seller.logo_key),
        banner_url=_url(seller.banner_key),
        user_name=seller.user.name if seller.user else None,
        user_email=seller.user.email if seller.user else None,
        user_avatar_url=_url(seller.user.avatar_key) if seller.user else None,
        email_verified=seller.user.email_verified if seller.user else None,
        products=[_product_to_list_item(p) for p in products],
        average_rating=avg_rating,
        total_reviews=total_reviews,
    )


@router.get("/", response_model=SellerListResponse)
def list_sellers(
    category: Optional[SellerCategory] = None,
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lista lojas abertas. Publico."""
    seller_repo = SellerRepository(db)
    sellers = seller_repo.list_active(category=category, search=search, skip=skip, limit=limit)
    total = seller_repo.count_active(category=category, search=search)
    return SellerListResponse(
        items=[_seller_to_list_item(s, db=db) for s in sellers],
        total=total, skip=skip, limit=limit,
    )


@router.get("/categories", response_model=List[str])
def list_categories():
    return [c.value for c in SellerCategory]


@router.get("/by-slug/{slug}", response_model=SellerDetailResponse)
def get_seller_by_slug(slug: str, db: Session = Depends(get_db)):
    seller_repo = SellerRepository(db)
    product_repo = SellerProductSpecRepository(db)

    seller = seller_repo.get_by_slug(slug)
    if not seller or not seller.is_open:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loja nao encontrada.")
    products = product_repo.list_by_seller(seller.id, active_only=True)
    return _seller_to_detail(seller, products, db=db)


@router.get("/{seller_id}", response_model=SellerDetailResponse)
def get_seller_detail(seller_id: uuid.UUID, db: Session = Depends(get_db)):
    seller_repo = SellerRepository(db)
    product_repo = SellerProductSpecRepository(db)

    seller = seller_repo.get_by_id(seller_id)
    if not seller or not seller.is_open:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loja nao encontrada.")
    products = product_repo.list_by_seller(seller_id, active_only=True)
    return _seller_to_detail(seller, products, db=db)


@router.get("/{seller_id}/products", response_model=List[ProductSpecListItem])
def list_seller_products(
    seller_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    seller_repo = SellerRepository(db)
    product_repo = SellerProductSpecRepository(db)

    seller = seller_repo.get_by_id(seller_id)
    if not seller or not seller.is_open:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loja nao encontrada.")
    products = product_repo.list_by_seller(seller_id, active_only=True, skip=skip, limit=limit)
    return [_product_to_list_item(p) for p in products]


@router.get("/products/{product_id}", response_model=ProductSpecListItem)
def get_product_detail(product_id: uuid.UUID, db: Session = Depends(get_db)):
    product_repo = SellerProductSpecRepository(db)
    product = product_repo.get_by_id(product_id)
    if not product or not product.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado.")
    if not product.seller or not product.seller.is_open:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado.")
    return _product_to_list_item(product)


@router.get("/products/{product_id}/images", response_model=List[ProductImageResponse])
def list_product_images_public(product_id: uuid.UUID, db: Session = Depends(get_db)):
    """Lista imagens publicas de um produto."""
    product_repo = SellerProductSpecRepository(db)
    image_repo = SellerProductImageRepository(db)

    product = product_repo.get_by_id(product_id)
    if not product or not product.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado.")
    if not product.seller or not product.seller.is_open:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado.")

    images = image_repo.list_by_product(product.id)
    return [_image_to_response(i) for i in images]
