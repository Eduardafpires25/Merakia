from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database.models.order_review import OrderReview


class ReviewRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, review_id: uuid.UUID) -> Optional[OrderReview]:
        return self.db.query(OrderReview).filter(OrderReview.id == review_id).first()

    def get_by_order_id(self, order_id: uuid.UUID) -> Optional[OrderReview]:
        return self.db.query(OrderReview).filter(OrderReview.order_id == order_id).first()

    def create(
        self,
        *,
        order_id: Optional[uuid.UUID],
        seller_id: uuid.UUID,
        client_id: Optional[uuid.UUID],
        client_name: str,
        product_title: Optional[str] = None,
        rating: int,
        comment: Optional[str] = None,
    ) -> OrderReview:
        review = OrderReview(
            order_id=order_id,
            seller_id=seller_id,
            client_id=client_id,
            client_name=client_name,
            product_title=product_title,
            rating=rating,
            comment=comment,
            is_edited=False,
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def update(
        self,
        review: OrderReview,
        *,
        rating: int,
        comment: Optional[str] = None,
    ) -> OrderReview:
        review.rating = rating
        review.comment = comment
        review.is_edited = True
        review.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(review)
        return review

    def list_for_seller(
        self,
        seller_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[OrderReview], int]:
        query = self.db.query(OrderReview).filter(OrderReview.seller_id == seller_id)
        total = query.count()
        items = query.order_by(OrderReview.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_seller_stats(self, seller_id: uuid.UUID) -> Tuple[float, int, Dict[int, int]]:
        """Retorna média de avaliação, total de avaliações e distribuição de estrelas (1 a 5)."""
        reviews = self.db.query(OrderReview.rating).filter(OrderReview.seller_id == seller_id).all()
        total = len(reviews)
        if total == 0:
            return 0.0, 0, {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        avg = sum(r[0] for r in reviews) / total
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for r in reviews:
            score = r[0]
            if score in distribution:
                distribution[score] += 1

        return round(float(avg), 1), total, distribution
