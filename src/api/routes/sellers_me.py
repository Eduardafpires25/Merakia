from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.database.models.user import User
from src.database.models.seller_profile import SellerProfile
from src.database.models.seller_product_spec import SellerProductSpec
from src.database.models.seller_product_image import SellerProductImage
from src.api.dependencies.auth import require_seller, require_seller_email_verified
from src.api.models.seller import (
    SellerProfileCreate,
    SellerProfileUpdate,
    SellerProfileResponse,
    ProductSpecCreate,
    ProductSpecUpdate,
    ProductSpecResponse,
    ProductSpecListItem,
    ProductSpecListResponse,
    ProductImageResponse,
    ProductImageUpdate,
    slugify,
)
from src.api.repositories.seller_repository import (
    SellerRepository,
    SellerProductSpecRepository,
)
from src.api.repositories.product_image_repository import SellerProductImageRepository
from src.storage import image_service
from config.logger import logger

router = APIRouter(prefix="/sellers/me", tags=["sellers-me"])


# =============================================================================
# Helpers de conversao (ORM -> Pydantic) com URLs
# =============================================================================

def _url(key: Optional[str]) -> Optional[str]:
    return image_service.get_url(key) if key else None


def _seller_to_response(seller: SellerProfile) -> SellerProfileResponse:
    return SellerProfileResponse(
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
        pix_key=seller.pix_key,
        pix_key_type=seller.pix_key_type,
        created_at=seller.created_at,
        updated_at=seller.updated_at,
        logo_url=_url(seller.logo_key),
        banner_url=_url(seller.banner_key),
        user_name=seller.user.name if seller.user else None,
        user_email=seller.user.email if seller.user else None,
        user_avatar_url=_url(seller.user.avatar_key) if seller.user else None,
        email_verified=seller.user.email_verified if seller.user else None,
    )


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


def _product_to_response(spec: SellerProductSpec) -> ProductSpecResponse:
    images = list(spec.images) if spec.images is not None else []
    cover = next((i for i in images if i.is_cover), images[0] if images else None)
    return ProductSpecResponse(
        id=spec.id,
        seller_id=spec.seller_id,
        name=spec.name,
        description=spec.description,
        attributes=spec.attributes or {},
        is_customizable=spec.is_customizable,
        customization_options=spec.customization_options or {},
        base_price=spec.base_price,
        is_active=spec.is_active,
        created_at=spec.created_at,
        updated_at=spec.updated_at,
        images=[_image_to_response(i) for i in sorted(images, key=lambda x: x.position)],
        cover_url=_url(cover.image_key) if cover else None,
    )


def _product_to_list_item(spec: SellerProductSpec) -> ProductSpecListItem:
    images = list(spec.images) if spec.images is not None else []
    cover = next((i for i in images if i.is_cover), images[0] if images else None)
    return ProductSpecListItem(
        id=spec.id,
        name=spec.name,
        description=spec.description,
        is_customizable=spec.is_customizable,
        customization_options=spec.customization_options or {},
        base_price=spec.base_price,
        is_active=spec.is_active,
        cover_url=_url(cover.image_key) if cover else None,
    )


def _get_my_seller(db: Session, user_id: uuid.UUID) -> SellerProfile:
    seller = SellerRepository(db).get_by_user_id(user_id)
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de seller nao encontrado. Crie um primeiro em POST /sellers/me/profile.",
        )
    return seller


def _generate_unique_slug(seller_repo: SellerRepository, base: str) -> str:
    slug = slugify(base) or "loja"
    candidate = slug
    counter = 2
    while seller_repo.slug_exists(candidate):
        candidate = f"{slug}-{counter}"
        counter += 1
    return candidate


# =============================================================================
# Profile Management
# =============================================================================

@router.get("/profile", response_model=SellerProfileResponse)
def get_my_profile(
    current_user: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    """Retorna o perfil do seller logado."""
    return _seller_to_response(_get_my_seller(db, current_user.id))


@router.post("/profile", response_model=SellerProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    body: SellerProfileCreate,
    current_user: User = Depends(require_seller_email_verified),
    db: Session = Depends(get_db),
):
    """Cria perfil de seller. Requer email verificado."""
    seller_repo = SellerRepository(db)

    if seller_repo.get_by_user_id(current_user.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Perfil ja existe.")

    if body.slug and seller_repo.slug_exists(body.slug):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Slug '{body.slug}' ja em uso.")

    final_slug = body.slug or _generate_unique_slug(seller_repo, body.store_name)

    seller = seller_repo.create(
        user_id=current_user.id,
        store_name=body.store_name,
        slug=final_slug,
        description=body.description,
        category=body.category,
        whatsapp=body.whatsapp,
        instagram=body.instagram,
        city=body.city,
        state=body.state,
        accepts_custom_designs=body.accepts_custom_designs,
        min_order_quantity=body.min_order_quantity,
        estimated_days=body.estimated_days,
        pix_key=body.pix_key,
        pix_key_type=body.pix_key_type,
    )
    logger.info("Perfil criado: %s (slug=%s)", seller.store_name, seller.slug)
    return _seller_to_response(seller_repo.get_by_id(seller.id))


@router.patch("/profile", response_model=SellerProfileResponse)
def update_profile(
    body: SellerProfileUpdate,
    current_user: User = Depends(require_seller_email_verified),
    db: Session = Depends(get_db),
):
    seller_repo = SellerRepository(db)
    seller = _get_my_seller(db, current_user.id)

    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nada para atualizar.")

    seller = seller_repo.update(seller, **update_data)
    return _seller_to_response(seller)


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
def close_my_shop(
    current_user: User = Depends(require_seller_email_verified),
    db: Session = Depends(get_db),
):
    seller_repo = SellerRepository(db)
    seller = _get_my_seller(db, current_user.id)
    seller_repo.close_shop(seller)


# =============================================================================
# Profile Images: Logo & Banner
# =============================================================================

@router.post("/profile/logo", response_model=SellerProfileResponse)
def upload_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(require_seller_email_verified),
    db: Session = Depends(get_db),
):
    """Upload do logo da loja. Substitui o anterior se existir."""
    seller_repo = SellerRepository(db)
    seller = _get_my_seller(db, current_user.id)

    # Remove logo antigo
    if seller.logo_key:
        try:
            image_service.delete(seller.logo_key)
        except Exception as e:
            logger.warning("Erro ao remover logo antigo: %s", e)

    try:
        stored = image_service.upload_seller_logo(
            seller_id=str(seller.id),
            file=file.file,
            filename=file.filename or "logo.png",
            content_type=file.content_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    seller_repo.update(seller, logo_key=stored.key)
    return _seller_to_response(seller)


@router.delete("/profile/logo", status_code=status.HTTP_204_NO_CONTENT)
def delete_logo(
    current_user: User = Depends(require_seller_email_verified),
    db: Session = Depends(get_db),
):
    seller_repo = SellerRepository(db)
    seller = _get_my_seller(db, current_user.id)
    if not seller.logo_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Logo nao encontrado.")

    try:
        image_service.delete(seller.logo_key)
    except Exception as e:
        logger.warning("Erro ao remover logo: %s", e)
    seller_repo.update(seller, logo_key=None)


@router.post("/profile/banner", response_model=SellerProfileResponse)
def upload_banner(
    file: UploadFile = File(...),
    current_user: User = Depends(require_seller_email_verified),
    db: Session = Depends(get_db),
):
    """Upload do banner da loja."""
    seller_repo = SellerRepository(db)
    seller = _get_my_seller(db, current_user.id)

    if seller.banner_key:
        try:
            image_service.delete(seller.banner_key)
        except Exception as e:
            logger.warning("Erro ao remover banner antigo: %s", e)

    try:
        stored = image_service.upload_seller_banner(
            seller_id=str(seller.id),
            file=file.file,
            filename=file.filename or "banner.png",
            content_type=file.content_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    seller_repo.update(seller, banner_key=stored.key)
    return _seller_to_response(seller)


@router.delete("/profile/banner", status_code=status.HTTP_204_NO_CONTENT)
def delete_banner(
    current_user: User = Depends(require_seller_email_verified),
    db: Session = Depends(get_db),
):
    seller_repo = SellerRepository(db)
    seller = _get_my_seller(db, current_user.id)
    if not seller.banner_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Banner nao encontrado.")

    try:
        image_service.delete(seller.banner_key)
    except Exception as e:
        logger.warning("Erro ao remover banner: %s", e)
    seller_repo.update(seller, banner_key=None)


# =============================================================================
# Product Spec Management
# =============================================================================

@router.get("/products", response_model=ProductSpecListResponse)
def list_my_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    include_inactive: bool = False,
    current_user: User = Depends(require_seller_email_verified),
    db: Session = Depends(get_db),
):
    product_repo = SellerProductSpecRepository(db)
    seller = _get_my_seller(db, current_user.id)

    products = product_repo.list_by_seller(
        seller.id, active_only=not include_inactive, skip=skip, limit=limit
    )
    total = product_repo.count_by_seller(seller.id, active_only=not include_inactive)

    return ProductSpecListResponse(
        items=[_product_to_list_item(p) for p in products],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("/products", response_model=ProductSpecResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    body: ProductSpecCreate,
    current_user: User = Depends(require_seller_email_verified),
    db: Session = Depends(get_db),
):
    product_repo = SellerProductSpecRepository(db)
    seller = _get_my_seller(db, current_user.id)

    if product_repo.name_exists_for_seller(seller.id, body.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Produto '{body.name}' ja existe.",
        )

    spec = product_repo.create(
        seller_id=seller.id,
        name=body.name,
        description=body.description,
        attributes=body.attributes,
        is_customizable=body.is_customizable,
        customization_options=body.customization_options,
        base_price=body.base_price,
    )
    logger.info("Produto criado: %s", spec.name)
    return _product_to_response(spec)


@router.get("/products/{product_id}", response_model=ProductSpecResponse)
def get_my_product(
    product_id: uuid.UUID,
    current_user: User = Depends(require_seller_email_verified),
    db: Session = Depends(get_db),
):
    product_repo = SellerProductSpecRepository(db)
    seller = _get_my_seller(db, current_user.id)

    product = product_repo.get_by_id(product_id)
    if not product or product.seller_id != seller.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado.")

    return _product_to_response(product)


@router.patch("/products/{product_id}", response_model=ProductSpecResponse)
def update_product(
    product_id: uuid.UUID,
    body: ProductSpecUpdate,
    current_user: User = Depends(require_seller_email_verified),
    db: Session = Depends(get_db),
):
    product_repo = SellerProductSpecRepository(db)
    seller = _get_my_seller(db, current_user.id)

    product = product_repo.get_by_id(product_id)
    if not product or product.seller_id != seller.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado.")

    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nada para atualizar.")

    new_name = update_data.get("name")
    if new_name and product_repo.name_exists_for_seller(seller.id, new_name, exclude_id=product.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ja existe outro produto com o nome '{new_name}'.",
        )

    product = product_repo.update(product, **update_data)
    return _product_to_response(product)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_product(
    product_id: uuid.UUID,
    current_user: User = Depends(require_seller_email_verified),
    db: Session = Depends(get_db),
):
    product_repo = SellerProductSpecRepository(db)
    seller = _get_my_seller(db, current_user.id)

    product = product_repo.get_by_id(product_id)
    if not product or product.seller_id != seller.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado.")

    product_repo.deactivate(product)


# =============================================================================
# Product Images
# =============================================================================

MAX_IMAGES_PER_PRODUCT = 10


def _get_my_product(db: Session, user_id: uuid.UUID, product_id: uuid.UUID) -> SellerProductSpec:
    """Retorna produto do seller logado ou 404."""
    product_repo = SellerProductSpecRepository(db)
    seller = _get_my_seller(db, user_id)
    product = product_repo.get_by_id(product_id)
    if not product or product.seller_id != seller.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado.")
    return product


@router.get("/products/{product_id}/images", response_model=List[ProductImageResponse])
def list_product_images(
    product_id: uuid.UUID,
    current_user: User = Depends(require_seller_email_verified),
    db: Session = Depends(get_db),
):
    """Lista imagens de um produto."""
    product = _get_my_product(db, current_user.id, product_id)
    image_repo = SellerProductImageRepository(db)
    images = image_repo.list_by_product(product.id)
    return [_image_to_response(i) for i in images]


@router.post(
    "/products/{product_id}/images",
    response_model=ProductImageResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_product_image(
    product_id: uuid.UUID,
    file: UploadFile = File(...),
    alt_text: Optional[str] = Form(None),
    is_cover: bool = Form(False),
    current_user: User = Depends(require_seller_email_verified),
    db: Session = Depends(get_db),
):
    """
    Adiciona uma imagem ao produto.
    A primeira imagem vira capa automaticamente.
    """
    product = _get_my_product(db, current_user.id, product_id)
    image_repo = SellerProductImageRepository(db)

    if image_repo.count_by_product(product.id) >= MAX_IMAGES_PER_PRODUCT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Limite de {MAX_IMAGES_PER_PRODUCT} imagens por produto atingido.",
        )

    try:
        stored = image_service.upload_product_image(
            product_id=str(product.id),
            file=file.file,
            filename=file.filename or "image.png",
            content_type=file.content_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    img = image_repo.create(
        product_spec_id=product.id,
        image_key=stored.key,
        alt_text=alt_text,
        is_cover=is_cover,
    )
    logger.info("Imagem adicionada ao produto %s: %s", product.name, stored.key)
    return _image_to_response(img)


@router.patch(
    "/products/{product_id}/images/{image_id}",
    response_model=ProductImageResponse,
)
def update_product_image(
    product_id: uuid.UUID,
    image_id: uuid.UUID,
    body: ProductImageUpdate,
    current_user: User = Depends(require_seller_email_verified),
    db: Session = Depends(get_db),
):
    """Atualiza metadados (alt_text, position, is_cover) sem trocar arquivo."""
    product = _get_my_product(db, current_user.id, product_id)
    image_repo = SellerProductImageRepository(db)

    img = image_repo.get_by_id(image_id)
    if not img or img.product_spec_id != product.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagem nao encontrada.")

    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nada para atualizar.")

    img = image_repo.update(img, **update_data)
    return _image_to_response(img)


@router.delete(
    "/products/{product_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_product_image(
    product_id: uuid.UUID,
    image_id: uuid.UUID,
    current_user: User = Depends(require_seller_email_verified),
    db: Session = Depends(get_db),
):
    """Remove imagem do produto (banco + storage)."""
    product = _get_my_product(db, current_user.id, product_id)
    image_repo = SellerProductImageRepository(db)

    img = image_repo.get_by_id(image_id)
    if not img or img.product_spec_id != product.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagem nao encontrada.")

    key = image_repo.delete(img)
    try:
        image_service.delete(key)
    except Exception as e:
        logger.warning("Erro ao remover imagem do storage: %s", e)
