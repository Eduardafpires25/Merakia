from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.database.models.payment import PaymentStatus


class PaymentResponse(BaseModel):
    id: uuid.UUID
    order_id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    seller_id: uuid.UUID
    amount: Decimal
    status: PaymentStatus
    pix_code: str
    pix_qr_code: Optional[str] = None
    seller_pix_key: Optional[str] = None
    seller_pix_key_type: Optional[str] = None
    paid_at: Optional[datetime] = None
    released_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentSimulateRequest(BaseModel):
    action: str = Field(..., pattern="^(approve|fail)$", description="'approve' para simular pagamento com sucesso ou 'fail' para simular falha")


class PaymentSimulateResponse(BaseModel):
    payment: PaymentResponse
    message: str
