from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from src.database.models.seller_profile import SellerProfile
from src.database.models.seller_product_spec import SellerProductSpec
from src.database.models.enums import SellerCategory


class SellerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, seller_id: uuid.UUID) -> Optional[SellerProfile]:
        """Busca seller por ID com usuário carregado."""
        return (
            self.db.query(SellerProfile)
            .options(joinedload(SellerProfile.user))
            .filter(SellerProfile.id == seller_id)
            .first()
        )

    def get_by_user_id(self, user_id: uuid.UUID) -> Optional[SellerProfile]:
        """Busca seller pelo ID do usuário."""
        return (
            self.db.query(SellerProfile)
            .options(joinedload(SellerProfile.user))
            .filter(SellerProfile.user_id == user_id)
            .first()
        )

    def get_by_slug(self, slug: str) -> Optional[SellerProfile]:
        """Busca seller pelo slug."""
        return (
            self.db.query(SellerProfile)
            .options(joinedload(SellerProfile.user))
            .filter(SellerProfile.slug == slug)
            .first()
        )

    def _base_list_query(
        self,
        category: Optional[SellerCategory] = None,
        search: Optional[str] = None,
    ):
        """Query base para listagem de sellers ativos (lojas abertas)."""
        query = self.db.query(SellerProfile).filter(SellerProfile.is_open == True)

        if category:
            query = query.filter(SellerProfile.category == category)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    SellerProfile.store_name.ilike(search_term),
                    SellerProfile.description.ilike(search_term),
                    SellerProfile.city.ilike(search_term),
                )
            )
        return query

    def list_active(
        self,
        category: Optional[SellerCategory] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[SellerProfile]:
        """Lista sellers com lojas abertas (is_open=True)."""
        return (
            self._base_list_query(category, search)
            .options(joinedload(SellerProfile.user))
            .order_by(SellerProfile.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_active(
        self,
        category: Optional[SellerCategory] = None,
        search: Optional[str] = None,
    ) -> int:
        """Conta sellers ativos."""
        return self._base_list_query(category, search).count()

    def create(
        self,
        *,
        user_id: uuid.UUID,
        store_name: str,
        slug: str,
        category: SellerCategory,
        description: Optional[str] = None,
        whatsapp: Optional[str] = None,
        instagram: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        accepts_custom_designs: bool = True,
        min_order_quantity: int = 1,
        estimated_days: Optional[int] = None,
        pix_key: Optional[str] = None,
        pix_key_type: Optional[str] = None,
    ) -> SellerProfile:
        """Cria perfil de seller."""
        seller = SellerProfile(
            user_id=user_id,
            store_name=store_name,
            slug=slug,
            description=description,
            category=category,
            whatsapp=whatsapp,
            instagram=instagram,
            city=city,
            state=state,
            accepts_custom_designs=accepts_custom_designs,
            min_order_quantity=min_order_quantity,
            estimated_days=estimated_days,
            is_open=True,
            pix_key=pix_key,
            pix_key_type=pix_key_type,
        )
        self.db.add(seller)
        self.db.commit()
        self.db.refresh(seller)
        return seller

    def update(self, seller: SellerProfile, **kwargs) -> SellerProfile:
        """Atualiza campos do seller."""
        for key, value in kwargs.items():
            if hasattr(seller, key):
                setattr(seller, key, value)
        self.db.commit()
        self.db.refresh(seller)
        return seller

    def close_shop(self, seller: SellerProfile) -> SellerProfile:
        """Fecha a loja (is_open=False)."""
        seller.is_open = False
        self.db.commit()
        self.db.refresh(seller)
        return seller

    def slug_exists(self, slug: str, exclude_id: Optional[uuid.UUID] = None) -> bool:
        """Verifica se slug já está em uso."""
        query = self.db.query(SellerProfile).filter(SellerProfile.slug == slug)
        if exclude_id:
            query = query.filter(SellerProfile.id != exclude_id)
        return query.first() is not None


class SellerProductSpecRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, spec_id: uuid.UUID) -> Optional[SellerProductSpec]:
        """Busca especificação por ID com seller carregado."""
        return (
            self.db.query(SellerProductSpec)
            .options(joinedload(SellerProductSpec.seller))
            .filter(SellerProductSpec.id == spec_id)
            .first()
        )

    def list_by_seller(
        self,
        seller_id: uuid.UUID,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> List[SellerProductSpec]:
        """Lista especificações de produtos de um seller."""
        query = self.db.query(SellerProductSpec).filter(
            SellerProductSpec.seller_id == seller_id
        )

        if active_only:
            query = query.filter(SellerProductSpec.is_active == True)

        return (
            query.order_by(SellerProductSpec.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_by_seller(self, seller_id: uuid.UUID, active_only: bool = True) -> int:
        """Conta especificações de um seller."""
        query = self.db.query(SellerProductSpec).filter(
            SellerProductSpec.seller_id == seller_id
        )
        if active_only:
            query = query.filter(SellerProductSpec.is_active == True)
        return query.count()

    def name_exists_for_seller(
        self,
        seller_id: uuid.UUID,
        name: str,
        exclude_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """Verifica se já existe produto com mesmo nome para o seller."""
        query = self.db.query(SellerProductSpec).filter(
            SellerProductSpec.seller_id == seller_id,
            SellerProductSpec.name.ilike(name),
        )
        if exclude_id:
            query = query.filter(SellerProductSpec.id != exclude_id)
        return query.first() is not None

    def create(
        self,
        *,
        seller_id: uuid.UUID,
        name: str,
        description: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
        is_customizable: bool = False,
        customization_options: Optional[Dict[str, Any]] = None,
        base_price: Optional[Decimal] = None,
    ) -> SellerProductSpec:
        """Cria especificação de produto."""
        spec = SellerProductSpec(
            seller_id=seller_id,
            name=name,
            description=description,
            attributes=attributes or {},
            is_customizable=is_customizable,
            customization_options=customization_options or {},
            base_price=base_price,
            is_active=True,
        )
        self.db.add(spec)
        self.db.commit()
        self.db.refresh(spec)
        return spec

    def update(self, spec: SellerProductSpec, **kwargs) -> SellerProductSpec:
        """Atualiza campos da especificação."""
        for key, value in kwargs.items():
            if hasattr(spec, key):
                setattr(spec, key, value)
        self.db.commit()
        self.db.refresh(spec)
        return spec

    def deactivate(self, spec: SellerProductSpec) -> SellerProductSpec:
        """Desativa a especificação (soft delete)."""
        spec.is_active = False
        self.db.commit()
        self.db.refresh(spec)
        return spec
