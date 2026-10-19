import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.database.models.enums import OrderStatus, UserRole
from src.database.models.order import Order
from src.database.models.order_review import OrderReview
from src.database.models.seller_profile import SellerProfile
from src.database.models.user import User

API = "/api/v1"


class TestReviewRoutes:
    def test_create_review_success(
        self,
        client: TestClient,
        test_order: Order,
        test_user: User,
        test_seller_user: User,
        db_session: Session,
    ):
        # Pedido precisa estar entregue ou concluído para ser avaliado
        test_order.status = OrderStatus.DELIVERED
        test_order.title = "Caneca Artesanal Personalizada"
        test_user.name = "Felipe Cliente"
        db_session.commit()

        payload = {
            "rating": 5,
            "comment": "Trabalho impecável, muito bem embalado e entrega rápida!",
        }

        response = client.post(f"{API}/orders/{test_order.id}/reviews", json=payload)
        assert response.status_code == 201
        data = response.json()

        assert data["rating"] == 5
        assert data["comment"] == payload["comment"]
        assert data["is_edited"] is False
        assert data["client_name"] == "Felipe Cliente"
        assert data["product_title"] == "Caneca Artesanal Personalizada"
        assert data["order_id"] == str(test_order.id)
        assert data["seller_id"] == str(test_seller_user.id)

    def test_create_review_before_delivery_fails(
        self,
        client: TestClient,
        test_order: Order,
        db_session: Session,
    ):
        # Pedido ainda em produção
        test_order.status = OrderStatus.IN_PRODUCTION
        db_session.commit()

        response = client.post(
            f"{API}/orders/{test_order.id}/reviews",
            json={"rating": 5, "comment": "Tentando avaliar antes de receber"},
        )
        assert response.status_code == 400
        assert "após a entrega ou conclusão" in response.json()["detail"]

    def test_duplicate_review_fails(
        self,
        client: TestClient,
        test_order: Order,
        db_session: Session,
    ):
        test_order.status = OrderStatus.COMPLETED
        db_session.commit()

        # Primeira avaliação
        res1 = client.post(
            f"{API}/orders/{test_order.id}/reviews",
            json={"rating": 5, "comment": "Primeira avaliação"},
        )
        assert res1.status_code == 201

        # Segunda avaliação deve falhar com 409 Conflict
        res2 = client.post(
            f"{API}/orders/{test_order.id}/reviews",
            json={"rating": 4, "comment": "Segunda avaliação"},
        )
        assert res2.status_code == 409
        assert "já possui uma avaliação" in res2.json()["detail"]


    def test_update_review_marks_is_edited(
        self,
        client: TestClient,
        test_order: Order,
        db_session: Session,
    ):
        test_order.status = OrderStatus.DELIVERED
        db_session.commit()

        # Cria avaliação inicial
        client.post(
            f"{API}/orders/{test_order.id}/reviews",
            json={"rating": 5, "comment": "Tudo ótimo inicialmente"},
        )

        # Edita avaliação
        update_payload = {
            "rating": 4,
            "comment": "Reavaliando após 1 semana de uso, ainda muito bom mas dou 4 estrelas.",
        }
        res_update = client.put(
            f"{API}/orders/{test_order.id}/reviews",
            json=update_payload,
        )
        assert res_update.status_code == 200
        data = res_update.json()

        assert data["rating"] == 4
        assert data["comment"] == update_payload["comment"]
        assert data["is_edited"] is True
        assert data["updated_at"] is not None

    def test_get_order_review(
        self,
        client: TestClient,
        test_order: Order,
        db_session: Session,
    ):
        test_order.status = OrderStatus.DELIVERED
        db_session.commit()

        client.post(
            f"{API}/orders/{test_order.id}/reviews",
            json={"rating": 5, "comment": "Excelente!"},
        )

        res = client.get(f"{API}/orders/{test_order.id}/reviews")
        assert res.status_code == 200
        assert res.json()["rating"] == 5

    def test_list_seller_public_reviews(
        self,
        client: TestClient,
        test_order: Order,
        test_seller: SellerProfile,
        db_session: Session,
    ):
        test_order.status = OrderStatus.DELIVERED
        db_session.commit()

        # Envia avaliação
        client.post(
            f"{API}/orders/{test_order.id}/reviews",
            json={"rating": 5, "comment": "Adorei a loja e o artesanato!"},
        )

        # Consulta rota pública de reviews do vendedor por slug
        res = client.get(f"{API}/sellers/{test_seller.slug}/reviews")
        assert res.status_code == 200
        data = res.json()

        assert data["total"] >= 1
        assert data["average_rating"] == 5.0
        assert "5" in data["rating_distribution"]
        assert len(data["items"]) >= 1
        assert data["items"][0]["comment"] == "Adorei a loja e o artesanato!"
