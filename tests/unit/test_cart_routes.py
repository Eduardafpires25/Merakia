import pytest
import json
from uuid import UUID, uuid4
from decimal import Decimal
from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session
from src.database.models.user import User
from src.database.models.seller_product_spec import SellerProductSpec
from src.database.models.cart_item import CartItem
from src.database.models.seller_profile import SellerProfile
from src.database.models.order import Order
from src.database.models.enums import UserRole, OrderStatus, SellerCategory

API = "/api/v1"


class TestCartRoutes:
    """Testes para rotas de Cart (prefixo /api/v1/cart)."""

    def test_get_cart_empty(self, client: TestClient):
        """GET /cart/ retorna carrinho vazio."""
        response = client.get(f"{API}/cart/")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total_items"] == 0

    def test_get_cart_with_item(self, client: TestClient, test_cart_item: CartItem):
        """GET /cart/ retorna itens do usuário."""
        response = client.get(f"{API}/cart/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total_items"] == test_cart_item.quantity

    def test_get_cart_unauthorized(self, anon_client: TestClient):
        """Sem auth retorna 401."""
        response = anon_client.get(f"{API}/cart/")
        assert response.status_code == 401

    def test_add_to_cart(self, client: TestClient, test_product_spec: SellerProductSpec):
        """POST /cart/items adiciona produto (201)."""
        response = client.post(
            f"{API}/cart/items",
            json={
                "product_spec_id": str(test_product_spec.id),
                "quantity": 2,
                "selected_options": '{"size": "medium"}',
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["quantity"] == 2
        assert data["product_spec_id"] == str(test_product_spec.id)

    def test_add_to_cart_unauthorized(self, anon_client: TestClient, test_product_spec: SellerProductSpec):
        response = anon_client.post(
            f"{API}/cart/items",
            json={"product_spec_id": str(test_product_spec.id), "quantity": 1},
        )
        assert response.status_code == 401

    def test_add_to_cart_invalid_quantity(self, client: TestClient, test_product_spec: SellerProductSpec):
        """quantity=0 deve ser rejeitado (422)."""
        response = client.post(
            f"{API}/cart/items",
            json={"product_spec_id": str(test_product_spec.id), "quantity": 0},
        )
        assert response.status_code == 422

    def test_add_to_cart_missing_identifier(self, client: TestClient):
        """Sem product_spec_id nem order_id retorna 400."""
        response = client.post(f"{API}/cart/items", json={"quantity": 1})
        assert response.status_code == 400

    def test_update_cart_item_quantity(self, client: TestClient, test_cart_item: CartItem):
        """PATCH /cart/items/{id} atualiza quantidade."""
        response = client.patch(
            f"{API}/cart/items/{test_cart_item.id}",
            json={"quantity": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 5

    def test_update_cart_item_quantity_invalid(self, client: TestClient, test_cart_item: CartItem):
        response = client.patch(
            f"{API}/cart/items/{test_cart_item.id}",
            json={"quantity": -1},
        )
        assert response.status_code == 422

    def test_remove_cart_item(self, client: TestClient, test_cart_item: CartItem):
        """DELETE /cart/items/{id} retorna 204."""
        response = client.delete(f"{API}/cart/items/{test_cart_item.id}")
        assert response.status_code == 204

    def test_remove_cart_item_not_found(self, client: TestClient):
        response = client.delete(f"{API}/cart/items/{uuid4()}")
        assert response.status_code == 404

    def test_checkout_missing_shipping_info(self, client: TestClient, test_product_spec: SellerProductSpec):
        """Checkout sem campos de envio obrigatórios → 422."""
        response = client.post(
            f"{API}/cart/checkout",
            json={"seller_ids": [str(test_product_spec.seller_id)]},
        )
        assert response.status_code == 422

    def test_checkout_missing_seller_ids(self, client: TestClient):
        """seller_ids é obrigatório."""
        response = client.post(
            f"{API}/cart/checkout",
            json={
                "shipping_address": "Rua Teste, 123",
                "shipping_city": "São Paulo",
                "shipping_state": "SP",
                "shipping_zip_code": "01234-567",
                "shipping_phone": "11999999999",
            },
        )
        assert response.status_code == 422

    def test_add_to_cart_both_ids_error(self, client: TestClient):
        """Testa erro ao fornecer ambos product_spec_id e order_id."""
        response = client.post(
            f"{API}/cart/items",
            json={
                "product_spec_id": str(uuid4()),
                "order_id": str(uuid4()),
                "quantity": 1,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "apenas product_spec_id ou order_id" in response.json()["detail"]

    def test_add_to_cart_product_not_found(self, client: TestClient):
        """Testa erro ao adicionar produto inexistente."""
        response = client.post(
            f"{API}/cart/items",
            json={
                "product_spec_id": str(uuid4()),
                "quantity": 1,
            },
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Produto não encontrado" in response.json()["detail"]

    def test_add_to_cart_product_inactive(self, client: TestClient, db_session: Session):
        """Testa erro ao adicionar produto inativo."""
        seller = SellerProfile(
            id=uuid4(),
            user_id=uuid4(),
            store_name="Test Store",
            slug="test-store",
            description="Test description",
            category="Test",
        )
        db_session.add(seller)
        
        product = SellerProductSpec(
            id=uuid4(),
            seller_id=seller.id,
            name="Test Product",
            description="Test description",
            base_price=Decimal("100.00"),
            is_active=False,
        )
        db_session.add(product)
        db_session.commit()
        
        response = client.post(
            f"{API}/cart/items",
            json={
                "product_spec_id": str(product.id),
                "quantity": 1,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Produto não está ativo" in response.json()["detail"]

    def test_add_to_cart_product_no_price(self, client: TestClient, db_session: Session):
        """Testa erro ao adicionar produto sem preço."""
        seller = SellerProfile(
            id=uuid4(),
            user_id=uuid4(),
            store_name="Test Store",
            slug="test-store-2",
            description="Test description",
            category="Test",
        )
        db_session.add(seller)
        
        product = SellerProductSpec(
            id=uuid4(),
            seller_id=seller.id,
            name="Test Product",
            description="Test description",
            base_price=None,
            is_active=True,
        )
        db_session.add(product)
        db_session.commit()
        
        response = client.post(
            f"{API}/cart/items",
            json={
                "product_spec_id": str(product.id),
                "quantity": 1,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Produto não tem preço definido" in response.json()["detail"]

    def test_add_to_cart_order_not_found(self, client: TestClient):
        """Testa erro ao adicionar pedido inexistente."""
        response = client.post(
            f"{API}/cart/items",
            json={
                "order_id": str(uuid4()),
                "quantity": 1,
            },
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Pedido não encontrado" in response.json()["detail"]

    def test_add_to_cart_order_not_approved(self, client: TestClient, db_session: Session, test_user: User):
        """Testa erro ao adicionar pedido não aprovado."""
        seller = SellerProfile(
            id=uuid4(),
            user_id=uuid4(),
            store_name="Test Store",
            slug="test-store-3",
            description="Test description",
            category="Test",
        )
        db_session.add(seller)
        
        order = Order(
            id=uuid4(),
            client_id=test_user.id,
            seller_id=seller.user_id,
            title="Test Order",
            description="Test description",
            status=OrderStatus.DRAFT,
            estimated_price=Decimal("100.00"),
        )
        db_session.add(order)
        db_session.commit()
        
        response = client.post(
            f"{API}/cart/items",
            json={
                "order_id": str(order.id),
                "quantity": 1,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Pedido não foi aprovado" in response.json()["detail"]

    def test_update_cart_item_not_found(self, client: TestClient):
        """Testa erro ao atualizar item inexistente."""
        response = client.patch(
            f"{API}/cart/items/{uuid4()}",
            json={"quantity": 2},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Item do carrinho não encontrado" in response.json()["detail"]

    def test_update_cart_item_wrong_user(self, client: TestClient, db_session: Session):
        """Testa erro ao atualizar item de outro usuário."""
        other_user = User(
            id=uuid4(),
            email="other@example.com",
            name="Other User",
            password_hash="hash",
            role=UserRole.CLIENT,
        )
        db_session.add(other_user)
        
        seller = SellerProfile(
            id=uuid4(),
            user_id=uuid4(),
            store_name="Test Store",
            slug="test-store-4",
            description="Test description",
            category="Test",
        )
        db_session.add(seller)
        
        cart_item = CartItem(
            id=uuid4(),
            user_id=other_user.id,
            seller_id=seller.user_id,
            quantity=1,
            unit_price=Decimal("100.00"),
            total_price=Decimal("100.00"),
            name="Test Item",
        )
        db_session.add(cart_item)
        db_session.commit()
        
        response = client.patch(
            f"{API}/cart/items/{cart_item.id}",
            json={"quantity": 2},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "não tem permissão para modificar" in response.json()["detail"]

    def test_remove_cart_item_wrong_user(self, client: TestClient, db_session: Session):
        """Testa erro ao remover item de outro usuário."""
        other_user = User(
            id=uuid4(),
            email="other2@example.com",
            name="Other User 2",
            password_hash="hash",
            role=UserRole.CLIENT,
        )
        db_session.add(other_user)
        
        seller = SellerProfile(
            id=uuid4(),
            user_id=uuid4(),
            store_name="Test Store",
            slug="test-store-5",
            description="Test description",
            category="Test",
        )
        db_session.add(seller)
        
        cart_item = CartItem(
            id=uuid4(),
            user_id=other_user.id,
            seller_id=seller.user_id,
            quantity=1,
            unit_price=Decimal("100.00"),
            total_price=Decimal("100.00"),
            name="Test Item",
        )
        db_session.add(cart_item)
        db_session.commit()
        
        response = client.delete(f"{API}/cart/items/{cart_item.id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "não tem permissão para remover" in response.json()["detail"]

    def test_checkout_no_sellers(self, client: TestClient):
        """Testa erro ao fazer checkout sem sellers."""
        response = client.post(
            f"{API}/cart/checkout",
            json={"seller_ids": []},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_checkout_no_items(self, client: TestClient):
        """Testa erro ao fazer checkout sem itens."""
        response = client.post(
            f"{API}/cart/checkout",
            json={
                "seller_ids": [str(uuid4())],
                "ignore_errors": True,
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_add_to_cart_with_options(self, client: TestClient, test_product_spec: SellerProductSpec, db_session):
        """Testa adicionar item com opções personalizadas."""
        # Adicionar imagem ao produto para cobrir linha 143
        from src.database.models.seller_product_image import SellerProductImage
        image = SellerProductImage(
            id=uuid4(),
            product_spec_id=test_product_spec.id,
            image_key="test-key",
            position=0,
            is_cover=True,
        )
        db_session.add(image)
        db_session.commit()
        
        response = client.post(
            f"{API}/cart/items",
            json={
                "product_spec_id": str(test_product_spec.id),
                "quantity": 1,
                "selected_options": json.dumps({"color": "red", "size": "M"}),
            },
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_add_to_cart_order_wrong_user(self, client: TestClient, db_session: Session, test_user: User):
        """Testa erro ao adicionar pedido de outro usuário."""
        other_user = User(
            id=uuid4(),
            email="other@example.com",
            name="Other User",
            password_hash="hash",
            role=UserRole.CLIENT,
        )
        db_session.add(other_user)
        
        seller = SellerProfile(
            id=uuid4(),
            user_id=other_user.id,
            store_name="Test Store",
            slug="test-store-6",
            description="Test description",
            category="Test",
        )
        db_session.add(seller)
        
        order = Order(
            id=uuid4(),
            client_id=other_user.id,
            seller_id=seller.user_id,
            title="Test Order",
            description="Test description",
            status=OrderStatus.APPROVED,
            estimated_price=Decimal("100.00"),
        )
        db_session.add(order)
        db_session.commit()
        
        response = client.post(
            f"{API}/cart/items",
            json={
                "order_id": str(order.id),
                "quantity": 1,
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "não é o cliente deste pedido" in response.json()["detail"]

    def test_add_to_cart_order_no_price(self, client: TestClient, db_session: Session, test_user: User):
        """Testa erro ao adicionar pedido sem preço estimado."""
        seller = SellerProfile(
            id=uuid4(),
            user_id=uuid4(),
            store_name="Test Store",
            slug="test-store-7",
            description="Test description",
            category="Test",
        )
        db_session.add(seller)
        
        order = Order(
            id=uuid4(),
            client_id=test_user.id,
            seller_id=seller.user_id,
            title="Test Order",
            description="Test description",
            status=OrderStatus.APPROVED,
            estimated_price=None,
        )
        db_session.add(order)
        db_session.commit()
        
        response = client.post(
            f"{API}/cart/items",
            json={
                "order_id": str(order.id),
                "quantity": 1,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "não tem preço estimado" in response.json()["detail"]

    def test_add_to_cart_order_with_approved_iteration(self, client: TestClient, db_session: Session, test_user: User):
        """Testa adicionar pedido com iteração aprovada (cobre linha 176-177)."""
        from src.database.models.project_iteration import ProjectIteration
        from src.database.models.enums import IterationStatus
        
        seller = SellerProfile(
            id=uuid4(),
            user_id=uuid4(),
            store_name="Test Store",
            slug="test-store-8",
            description="Test description",
            category="other",
        )
        db_session.add(seller)
        
        order = Order(
            id=uuid4(),
            client_id=test_user.id,
            seller_id=seller.user_id,
            title="Test Order",
            description="Test description",
            status=OrderStatus.APPROVED,
            estimated_price=Decimal("100.00"),
        )
        db_session.add(order)
        
        iteration = ProjectIteration(
            id=uuid4(),
            order_id=order.id,
            version=1,
            status=IterationStatus.APPROVED,
            image_key="iteration-key",
            description="Test iteration",
            prompt="Test prompt",
        )
        db_session.add(iteration)
        db_session.commit()
        
        response = client.post(
            f"{API}/cart/items",
            json={
                "order_id": str(order.id),
                "quantity": 1,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_add_to_cart_updates_existing_item(self, client: TestClient, test_product_spec: SellerProductSpec):
        """Testa que adicionar item existente atualiza quantidade (cobre linhas 187-192)."""
        # Primeira adição
        response1 = client.post(
            f"{API}/cart/items",
            json={
                "product_spec_id": str(test_product_spec.id),
                "quantity": 2,
            },
        )
        assert response1.status_code == status.HTTP_201_CREATED
        data1 = response1.json()
        assert data1["quantity"] == 2
        
        # Segunda adição do mesmo item
        response2 = client.post(
            f"{API}/cart/items",
            json={
                "product_spec_id": str(test_product_spec.id),
                "quantity": 3,
            },
        )
        assert response2.status_code == status.HTTP_201_CREATED
        data2 = response2.json()
        assert data2["quantity"] == 5  # 2 + 3

    def test_checkout_with_approved_order(self, client: TestClient, db_session: Session, test_user: User):
        """Testa checkout com pedido aprovado (cobre linhas 313-320)."""
        seller = SellerProfile(
            id=uuid4(),
            user_id=uuid4(),
            store_name="Test Store",
            slug="test-store-9",
            description="Test description",
            category=SellerCategory.OTHER,
        )
        db_session.add(seller)
        
        order = Order(
            id=uuid4(),
            client_id=test_user.id,
            seller_id=seller.user_id,
            title="Test Order",
            description="Test description",
            status=OrderStatus.APPROVED,
            estimated_price=Decimal("100.00"),
        )
        db_session.add(order)
        
        cart_item = CartItem(
            id=uuid4(),
            user_id=test_user.id,
            seller_id=seller.user_id,
            order_id=order.id,
            quantity=1,
            unit_price=Decimal("100.00"),
            total_price=Decimal("100.00"),
            name="Test Item",
        )
        db_session.add(cart_item)
        db_session.commit()
        
        response = client.post(
            f"{API}/cart/checkout",
            json={
                "seller_ids": [str(seller.user_id)],
                "shipping_address": "Rua Teste",
                "shipping_neighborhood": "Bairro Nobre",
                "shipping_city": "Cidade",
                "shipping_state": "UF",
                "shipping_zip_code": "12345",
                "shipping_phone": "11999999999",
                "ignore_errors": True,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["order_ids"]) >= 1

        created_order = db_session.query(Order).filter(Order.id == UUID(data["order_ids"][0])).first()
        assert created_order is not None
        assert created_order.shipping_neighborhood == "Bairro Nobre"
