import pytest
from decimal import Decimal
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.services.pix_service import pix_service
from src.database.models.enums import OrderStatus, UserRole
from src.database.models.order import Order
from src.database.models.payment import Payment, PaymentStatus
from src.database.models.seller_profile import SellerProfile
from src.database.models.user import User

API = "/api/v1"


@pytest.fixture
def test_payment(
    db_session: Session,
    test_user: User,
    test_seller_user: User,
    test_order: Order,
) -> Payment:
    pix_code = pix_service.generate_pix_payload(
        amount=Decimal("150.00"),
        txid="MKTESTPAYMENT01",
        description="Teste de pagamento",
    )
    payment = Payment(
        user_id=test_user.id,
        seller_id=test_seller_user.id,
        order_id=test_order.id,
        amount=Decimal("150.00"),
        status=PaymentStatus.PENDING,
        pix_code=pix_code,
        pix_qr_code=pix_service.generate_qr_code_url(pix_code),
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment


class TestPaymentRoutes:
    def test_get_payment_by_id(self, client: TestClient, test_payment: Payment):
        response = client.get(f"{API}/payments/{test_payment.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_payment.id)
        assert data["status"] == "pending"
        assert "pix_code" in data
        assert "pix_qr_code" in data

    def test_get_payment_by_order(
        self, client: TestClient, test_payment: Payment, test_order: Order
    ):
        response = client.get(f"{API}/payments/by-order/{test_order.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_payment.id)
        assert data["order_id"] == str(test_order.id)

    def test_simulate_payment_approve(
        self, client: TestClient, test_payment: Payment, test_order: Order, db_session: Session
    ):
        # Coloca o pedido em APPROVED para testar a transição para PAID
        test_order.status = OrderStatus.APPROVED
        db_session.commit()

        response = client.post(
            f"{API}/payments/{test_payment.id}/simulate",
            json={"action": "approve"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["payment"]["status"] == "paid"
        assert data["payment"]["paid_at"] is not None

        # Confirma que o pedido associado foi para PAID
        db_session.refresh(test_order)
        assert test_order.status == OrderStatus.PAID

    def test_simulate_payment_fail(
        self, client: TestClient, test_payment: Payment, test_order: Order, db_session: Session
    ):
        test_order.status = OrderStatus.PAID
        db_session.commit()

        response = client.post(
            f"{API}/payments/{test_payment.id}/simulate",
            json={"action": "fail"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["payment"]["status"] == "failed"

        db_session.refresh(test_order)
        assert test_order.status == OrderStatus.APPROVED


    def test_release_payment_on_delivery(
        self,
        client: TestClient,
        test_payment: Payment,
        test_order: Order,
        test_seller: SellerProfile,
        db_session: Session,
    ):
        # Configura chave PIX no perfil do vendedor
        test_seller.pix_key = "vendedor@pix.com"
        test_seller.pix_key_type = "email"

        test_payment.status = PaymentStatus.PAID
        test_order.status = OrderStatus.SENT
        db_session.commit()

        # Cliente confirma entrega
        response = client.patch(f"{API}/orders/{test_order.id}/confirm-delivery")
        assert response.status_code == 200
        assert response.json()["status"] == "delivered"

        # Pagamento deve ter sido liberado para o vendedor com a chave Pix cadastrada
        db_session.refresh(test_payment)
        assert test_payment.status == PaymentStatus.RELEASED
        assert test_payment.seller_pix_key == "vendedor@pix.com"
        assert test_payment.seller_pix_key_type == "email"
        assert test_payment.released_at is not None

    def test_get_or_create_payment_for_order_success(
        self, client: TestClient, db_session: Session, test_order: Order
    ):
        """Cliente gera pagamento para pedido APPROVED com preço."""
        test_order.status = OrderStatus.APPROVED
        test_order.estimated_price = Decimal("120.00")
        test_order.quantity = 2
        db_session.commit()

        response = client.post(f"{API}/payments/for-order/{test_order.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == str(test_order.id)
        assert data["status"] == "pending"
        assert float(data["amount"]) == 240.0
        assert data["pix_code"] is not None
        assert data["pix_qr_code"] is not None

    def test_get_or_create_payment_for_order_reuses_pending(
        self, client: TestClient, db_session: Session, test_order: Order, test_payment: Payment
    ):
        """Se já existe pagamento PENDING, reutiliza a mesma transação."""
        test_order.status = OrderStatus.APPROVED
        test_order.estimated_price = Decimal("50.00")
        test_payment.order_id = test_order.id
        test_payment.status = PaymentStatus.PENDING
        db_session.commit()

        response = client.post(f"{API}/payments/for-order/{test_order.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_payment.id)
        assert data["status"] == "pending"

    def test_get_or_create_payment_for_order_retries_failed(
        self, client: TestClient, db_session: Session, test_order: Order, test_payment: Payment
    ):
        """Se o pagamento anterior falhou, gera uma nova cobrança PIX."""
        test_order.status = OrderStatus.APPROVED
        test_order.estimated_price = Decimal("85.00")
        test_payment.order_id = test_order.id
        test_payment.status = PaymentStatus.FAILED
        db_session.commit()

        response = client.post(f"{API}/payments/for-order/{test_order.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] != str(test_payment.id)
        assert data["status"] == "pending"
        assert data["order_id"] == str(test_order.id)

    def test_seller_cannot_start_production_if_payment_failed(
        self, seller_client: TestClient, db_session: Session, test_order: Order, test_payment: Payment
    ):
        """Vendedor não pode iniciar produção se o pagamento tiver falhado."""
        test_order.status = OrderStatus.PAID
        test_payment.order_id = test_order.id
        test_payment.status = PaymentStatus.FAILED
        db_session.commit()

        response = seller_client.patch(
            f"{API}/orders/{test_order.id}/status",
            json={"status": OrderStatus.IN_PRODUCTION.value},
        )
        assert response.status_code == 400
        assert "pagamento PIX em custódia ainda não foi confirmado" in response.json()["detail"]

    def test_order_reconciliation_reverts_paid_to_approved_on_failed_payment(
        self, client: TestClient, db_session: Session, test_order: Order, test_payment: Payment
    ):
        """Se o pedido ficou como PAID mas o pagamento é FAILED, GET /orders/{id} reconcilia para APPROVED."""
        test_order.status = OrderStatus.PAID
        test_payment.order_id = test_order.id
        test_payment.status = PaymentStatus.FAILED
        db_session.commit()

        response = client.get(f"{API}/orders/{test_order.id}")
        assert response.status_code == 200
        assert response.json()["status"] == OrderStatus.APPROVED.value
