from __future__ import annotations

from decimal import Decimal
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.api.dependencies.auth import get_current_active_user
from src.api.models.payment import PaymentResponse, PaymentSimulateRequest, PaymentSimulateResponse
from src.api.repositories.order_repository import OrderRepository
from src.api.repositories.payment_repository import PaymentRepository
from src.api.services.pix_service import pix_service
from src.database.models.enums import OrderStatus, UserRole
from src.database.models.payment import Payment, PaymentStatus
from src.database.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])


def _to_payment_response(payment: Payment, current_user: User) -> PaymentResponse:
    # Apenas o vendedor destinatário ou admin podem visualizar a chave PIX do vendedor
    is_seller_or_admin = (
        payment.seller_id == current_user.id or current_user.role == UserRole.ADMIN
    )
    return PaymentResponse(
        id=payment.id,
        order_id=payment.order_id,
        user_id=payment.user_id,
        seller_id=payment.seller_id,
        amount=payment.amount,
        status=payment.status,
        pix_code=payment.pix_code,
        pix_qr_code=payment.pix_qr_code,
        seller_pix_key=payment.seller_pix_key if is_seller_or_admin else None,
        seller_pix_key_type=payment.seller_pix_key_type if is_seller_or_admin else None,
        paid_at=payment.paid_at,
        released_at=payment.released_at,
        created_at=payment.created_at,
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retorna os detalhes de uma transação de pagamento."""
    repo = PaymentRepository(db)
    payment = repo.get_by_id(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pagamento não encontrado.",
        )

    # Apenas o pagador, o vendedor ou um admin podem consultar
    if (
        payment.user_id != current_user.id
        and payment.seller_id != current_user.id
        and current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para visualizar este pagamento.",
        )

    return _to_payment_response(payment, current_user)


@router.get("/by-order/{order_id}", response_model=PaymentResponse)
def get_payment_by_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retorna o pagamento mais recente associado a um pedido."""
    repo = PaymentRepository(db)
    payment = repo.get_by_order_id(order_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum pagamento encontrado para este pedido.",
        )

    if (
        payment.user_id != current_user.id
        and payment.seller_id != current_user.id
        and current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para visualizar este pagamento.",
        )

    return _to_payment_response(payment, current_user)


@router.post("/for-order/{order_id}", response_model=PaymentResponse)
def get_or_create_payment_for_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Retorna o pagamento ativo (PENDING/PAID/RELEASED) associado ao pedido ou gera uma
    nova cobrança PIX caso ainda não exista ou caso o pagamento anterior tenha falhado/expirado.
    Permitido apenas para o cliente comprador do pedido (ou admin).
    """
    order_repo = OrderRepository(db)
    order = order_repo.get_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado.",
        )

    if order.client_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para gerar pagamento para este pedido.",
        )

    if order.status not in (OrderStatus.APPROVED, OrderStatus.DRAFT):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Não é possível gerar pagamento para pedido no status atual ({order.status.value}).",
        )

    payment_repo = PaymentRepository(db)
    existing_payment = payment_repo.get_by_order_id(order_id)

    # Se já existir um pagamento PENDING ou PAID/RELEASED, retorna ele
    if existing_payment and existing_payment.status in (
        PaymentStatus.PENDING,
        PaymentStatus.PAID,
        PaymentStatus.RELEASED,
    ):
        return _to_payment_response(existing_payment, current_user)

    # Valida preço estimado do pedido
    if not order.estimated_price or order.estimated_price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O pedido ainda não possui valor definido pelo vendedor.",
        )

    qty = Decimal(str(order.quantity or 1))
    total_amount = (
        existing_payment.amount
        if existing_payment and existing_payment.amount
        else Decimal(str(order.estimated_price)) * qty
    )

    txid = f"MK{uuid.uuid4().hex[:16].upper()}"
    pix_code = pix_service.generate_pix_payload(
        amount=float(total_amount),
        txid=txid,
        description=f"Pedido MeraKia {order.id}",
    )
    pix_qr = pix_service.generate_qr_code_url(pix_code)

    payment = payment_repo.create(
        user_id=current_user.id,
        seller_id=order.seller_id or current_user.id,
        amount=total_amount,
        pix_code=pix_code,
        pix_qr_code=pix_qr,
        order_id=order.id,
        status=PaymentStatus.PENDING,
    )

    logger.info(
        "Cobrança PIX %s gerada diretamente para o pedido %s (R$ %s)",
        payment.id,
        order.id,
        total_amount,
    )
    return _to_payment_response(payment, current_user)


@router.post("/{payment_id}/simulate", response_model=PaymentSimulateResponse)
def simulate_payment(
    payment_id: uuid.UUID,
    body: PaymentSimulateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Simulação didática de pagamento PIX para plataforma intermediária (MeraKia).
    - 'approve': Simula recebimento de PIX pela plataforma (status PAID / Custódia).
    - 'fail': Simula falha ou cancelamento do pagamento (status FAILED).
    """
    payment_repo = PaymentRepository(db)
    payment = payment_repo.get_by_id(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pagamento não encontrado.",
        )

    if (
        payment.user_id != current_user.id
        and current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o cliente responsável pelo pedido pode simular o pagamento.",
        )

    order_repo = OrderRepository(db)

    if body.action == "approve":
        payment = payment_repo.mark_as_paid(payment)
        
        # Se houver pedido vinculado, atualiza status para PAID
        if payment.order_id:
            order = order_repo.get_by_id(payment.order_id)
            if order and order.status in (OrderStatus.APPROVED, OrderStatus.DRAFT):
                order_repo.change_status(
                    order,
                    OrderStatus.PAID,
                    changed_by_id=current_user.id,
                    note="Pagamento PIX intermediado e aprovado com sucesso (custódia MeraKia)",
                )
                logger.info(
                    "Pedido %s atualizado para PAID após simulação de pagamento %s",
                    order.id,
                    payment.id,
                )

        message = (
            "Pagamento PIX confirmado com sucesso! O valor está retido com segurança "
            "na custódia da plataforma MeraKia e será liberado ao vendedor assim que você "
            "confirmar o recebimento do pedido."
        )
    else:
        payment = payment_repo.mark_as_failed(payment)

        # Se houver pedido vinculado e ele estiver em PAID, reverte para APPROVED
        if payment.order_id:
            order = order_repo.get_by_id(payment.order_id)
            if order and order.status == OrderStatus.PAID:
                order_repo.change_status(
                    order,
                    OrderStatus.APPROVED,
                    changed_by_id=current_user.id,
                    note="Pagamento PIX falhou ou foi cancelado. Aguardando novo pagamento.",
                )
                logger.info(
                    "Pedido %s revertido para APPROVED após falha na simulação de pagamento %s",
                    order.id,
                    payment.id,
                )

        message = "O pagamento foi marcado como com falha ou expirado. Tente novamente gerar um novo pagamento."

    return PaymentSimulateResponse(

        payment=_to_payment_response(payment, current_user),
        message=message,
    )
