from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from src.database.models.payment import Payment, PaymentStatus


class PaymentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, payment_id: uuid.UUID) -> Optional[Payment]:
        return self.db.query(Payment).filter(Payment.id == payment_id).first()

    def get_by_order_id(self, order_id: uuid.UUID) -> Optional[Payment]:
        return (
            self.db.query(Payment)
            .filter(Payment.order_id == order_id)
            .order_by(Payment.created_at.desc())
            .first()
        )

    def list_for_user(self, user_id: uuid.UUID) -> List[Payment]:
        return (
            self.db.query(Payment)
            .filter(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .all()
        )

    def create(
        self,
        *,
        user_id: uuid.UUID,
        seller_id: uuid.UUID,
        amount: Decimal,
        pix_code: str,
        pix_qr_code: Optional[str] = None,
        order_id: Optional[uuid.UUID] = None,
        seller_pix_key: Optional[str] = None,
        seller_pix_key_type: Optional[str] = None,
        status: PaymentStatus = PaymentStatus.PENDING,
    ) -> Payment:
        payment = Payment(
            user_id=user_id,
            seller_id=seller_id,
            amount=amount,
            pix_code=pix_code,
            pix_qr_code=pix_qr_code,
            order_id=order_id,
            seller_pix_key=seller_pix_key,
            seller_pix_key_type=seller_pix_key_type,
            status=status,
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def mark_as_paid(self, payment: Payment) -> Payment:
        payment.status = PaymentStatus.PAID
        payment.paid_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def mark_as_failed(self, payment: Payment) -> Payment:
        payment.status = PaymentStatus.FAILED
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def release_to_seller(
        self,
        payment: Payment,
        seller_pix_key: Optional[str] = None,
        seller_pix_key_type: Optional[str] = None,
    ) -> Payment:
        payment.status = PaymentStatus.RELEASED
        payment.released_at = datetime.now(timezone.utc)
        if seller_pix_key:
            payment.seller_pix_key = seller_pix_key
        if seller_pix_key_type:
            payment.seller_pix_key_type = seller_pix_key_type
        self.db.commit()
        self.db.refresh(payment)
        return payment
