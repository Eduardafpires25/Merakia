import pytest
from uuid import uuid4
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from src.database.session import Base
from src.database.models.user import User
from src.database.models.seller_profile import SellerProfile
from src.database.models.order import Order
from src.database.models.project_iteration import ProjectIteration
from src.database.models.seller_product_spec import SellerProductSpec
from src.database.models.cart_item import CartItem
from src.database.models.enums import OrderStatus, SellerCategory


class TestUserModel:
    """Testes para o modelo User."""

    def test_create_user(self, db_session: Session):
        """Testa criação de usuário."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            email_verified=True,
            name="Test User",
            password_hash="hashed_password",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.email == "test@example.com"
        assert user.email_verified is True
        assert user.name == "Test User"

    def test_user_relationship_with_seller(self, db_session: Session, test_seller_user: User, test_seller: SellerProfile):
        """Testa relacionamento entre User e SellerProfile (1:1)."""
        db_session.refresh(test_seller_user)
        assert test_seller_user.seller_profile is not None
        assert test_seller_user.seller_profile.store_name == "Test Store"

    def test_user_relationship_with_orders(self, db_session: Session, test_user: User, test_seller_user: User):
        """Testa relacionamento entre User e Order (como cliente)."""
        order = Order(
            id=uuid4(),
            client_id=test_user.id,
            seller_id=test_seller_user.id,
            title="Test Order",
            description="Test description",
            product_type="customized",
            quantity=1,
            estimated_price=Decimal("50.00"),
            status=OrderStatus.IN_ANALYSIS,
            submitted_at=datetime.now(timezone.utc),
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(test_user)

        assert len(test_user.orders_as_client) == 1
        assert test_user.orders_as_client[0].title == "Test Order"


class TestSellerModel:
    """Testes para o modelo SellerProfile."""

    def test_create_seller(self, db_session: Session, test_seller_user: User):
        """Testa criação de seller."""
        seller = SellerProfile(
            id=uuid4(),
            user_id=test_seller_user.id,
            store_name="Test Store",
            slug="test-store",
            description="Test description",
            category=SellerCategory.MUG,
            city="São Paulo",
            state="SP",
            whatsapp="11999999999",
            instagram="test_store",
            estimated_days=7,
            accepts_custom_designs=True,
            min_order_quantity=1,
            is_open=True,
        )
        db_session.add(seller)
        db_session.commit()
        db_session.refresh(seller)

        assert seller.store_name == "Test Store"
        assert seller.slug == "test-store"
        assert seller.category == SellerCategory.MUG
        assert seller.is_open is True

    def test_seller_relationship_with_user(self, db_session: Session, test_seller: SellerProfile):
        """Testa relacionamento entre SellerProfile e User."""
        db_session.refresh(test_seller)
        assert test_seller.user.email == "seller@example.com"

    def test_seller_relationship_with_products(self, db_session: Session, test_seller: SellerProfile):
        """Testa relacionamento entre SellerProfile e SellerProductSpec."""
        product = SellerProductSpec(
            id=uuid4(),
            seller_id=test_seller.id,
            name="Test Product",
            attributes={"volume_ml": 250},
            base_price=Decimal("25.00"),
            is_customizable=True,
        )
        db_session.add(product)
        db_session.commit()
        db_session.refresh(test_seller)

        assert len(test_seller.product_specs) == 1
        assert test_seller.product_specs[0].name == "Test Product"


class TestOrderModel:
    """Testes para o modelo Order."""

    def test_create_order(self, db_session: Session, test_user: User, test_seller_user: User):
        """Testa criação de order."""
        order = Order(
            id=uuid4(),
            client_id=test_user.id,
            seller_id=test_seller_user.id,
            title="Test Order",
            description="Test description",
            product_type="customized",
            product_options={"size": "medium", "color": "blue"},
            quantity=1,
            estimated_price=Decimal("50.00"),
            status=OrderStatus.IN_ANALYSIS,
            submitted_at=datetime.now(timezone.utc),
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.title == "Test Order"
        assert order.status == OrderStatus.IN_ANALYSIS
        assert order.product_type == "customized"
        assert order.product_options == {"size": "medium", "color": "blue"}

    def test_order_relationship_with_client(self, db_session: Session, test_order: Order):
        """Testa relacionamento entre Order e User (cliente)."""
        db_session.refresh(test_order)
        assert test_order.client.email == "test@example.com"

    def test_order_relationship_with_seller(self, db_session: Session, test_order: Order):
        """Testa relacionamento entre Order e seller (User)."""
        db_session.refresh(test_order)
        assert test_order.seller is not None
        assert test_order.seller.email == "seller@example.com"

    def test_order_relationship_with_iterations(self, db_session: Session, test_order: Order):
        """Testa relacionamento entre Order e ProjectIteration."""
        iteration = ProjectIteration(
            id=uuid4(),
            order_id=test_order.id,
            version=1,
            description="Iteration description",
            image_key="test_image_key",
            prompt="Test prompt",
        )
        db_session.add(iteration)
        db_session.commit()
        db_session.refresh(test_order)

        assert len(test_order.iterations) == 1
        assert test_order.iterations[0].version == 1

    def test_order_status_transition(self, db_session: Session, test_order: Order):
        """Testa transição de status do order."""
        test_order.status = OrderStatus.APPROVED
        db_session.commit()
        db_session.refresh(test_order)

        assert test_order.status == OrderStatus.APPROVED

    def test_order_with_shipping_info(self, db_session: Session, test_user: User, test_seller_user: User):
        """Testa order com informações de envio."""
        order = Order(
            id=uuid4(),
            client_id=test_user.id,
            seller_id=test_seller_user.id,
            title="Test Order",
            description="Test description",
            product_type="regular",
            quantity=1,
            estimated_price=Decimal("50.00"),
            status=OrderStatus.PAID,
            submitted_at=datetime.now(timezone.utc),
            shipping_address="Rua Teste, 123",
            shipping_neighborhood="Centro",
            shipping_city="São Paulo",
            shipping_state="SP",
            shipping_zip_code="01234-567",
            shipping_phone="11999999999",
            image_url="https://example.com/image.jpg",
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.shipping_address == "Rua Teste, 123"
        assert order.shipping_neighborhood == "Centro"
        assert order.shipping_state == "SP"
        assert order.image_url == "https://example.com/image.jpg"


class TestIterationModel:
    """Testes para o modelo ProjectIteration."""

    def test_create_iteration(self, db_session: Session, test_order: Order):
        """Testa criação de iteration."""
        iteration = ProjectIteration(
            id=uuid4(),
            order_id=test_order.id,
            version=1,
            description="Iteration description",
            image_key="test_image_key",
            prompt="Test prompt",
        )
        db_session.add(iteration)
        db_session.commit()
        db_session.refresh(iteration)

        assert iteration.version == 1
        assert iteration.image_key == "test_image_key"
        assert iteration.prompt == "Test prompt"

    def test_iteration_relationship_with_order(self, db_session: Session, test_iteration: ProjectIteration):
        """Testa relacionamento entre ProjectIteration e Order."""
        db_session.refresh(test_iteration)
        assert test_iteration.order.title == "Test Order"


class TestProductSpecModel:
    """Testes para o modelo SellerProductSpec."""

    def test_create_product_spec(self, db_session: Session, test_seller: SellerProfile):
        """Testa criação de product spec."""
        product = SellerProductSpec(
            id=uuid4(),
            seller_id=test_seller.id,
            name="Test Product",
            description="Test product description",
            attributes={"volume_ml": 250},
            base_price=Decimal("25.00"),
            is_customizable=True,
            customization_options={"size": ["small", "medium", "large"], "color": ["blue", "red"]},
        )
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)

        assert product.name == "Test Product"
        assert product.is_customizable is True
        assert product.customization_options == {"size": ["small", "medium", "large"], "color": ["blue", "red"]}

    def test_product_spec_regular_product(self, db_session: Session, test_seller: SellerProfile):
        """Testa product spec para produto regular."""
        product = SellerProductSpec(
            id=uuid4(),
            seller_id=test_seller.id,
            name="Regular Product",
            attributes={},
            base_price=Decimal("15.00"),
            is_customizable=False,
        )
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)

        assert product.is_customizable is False


class TestCartItemModel:
    """Testes para o modelo CartItem."""

    def test_create_cart_item(
        self,
        db_session: Session,
        test_user: User,
        test_seller_user: User,
        test_product_spec: SellerProductSpec,
    ):
        """Testa criação de cart item."""
        cart_item = CartItem(
            id=uuid4(),
            user_id=test_user.id,
            seller_id=test_seller_user.id,
            product_spec_id=test_product_spec.id,
            quantity=2,
            unit_price=Decimal("25.00"),
            total_price=Decimal("50.00"),
            name="Test Product",
            selected_options='{"size": "medium"}',
        )
        db_session.add(cart_item)
        db_session.commit()
        db_session.refresh(cart_item)

        assert cart_item.quantity == 2
        assert cart_item.selected_options == '{"size": "medium"}'
        assert cart_item.unit_price == Decimal("25.00")
        assert cart_item.total_price == Decimal("50.00")

    def test_cart_item_relationship_with_product(self, db_session: Session, test_cart_item: CartItem):
        """Testa relacionamento entre CartItem e SellerProductSpec."""
        db_session.refresh(test_cart_item)
        assert test_cart_item.product_spec is not None
        assert test_cart_item.product_spec.name == "Test Product"
