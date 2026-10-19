from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from src.database.models.order import Order
from src.database.models.order_reference_image import OrderReferenceImage
from src.database.models.order_status_history import OrderStatusHistory
from src.database.models.project_iteration import ProjectIteration
from src.database.models.enums import IterationStatus, OrderStatus


class OrderRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, order_id: uuid.UUID) -> Optional[Order]:
        return (
            self.db.query(Order)
            .options(
                selectinload(Order.iterations),
                joinedload(Order.approved_iteration),
                selectinload(Order.reference_images),
            )
            .filter(Order.id == order_id)
            .first()
        )

    def list_for_client(
        self,
        client_id: uuid.UUID,
        status: Optional[OrderStatus] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Order]:
        q = (
            self.db.query(Order)
            .filter(Order.client_id == client_id)
            .options(joinedload(Order.approved_iteration))
        )
        if status:
            q = q.filter(Order.status == status)
        return q.order_by(desc(Order.created_at)).offset(skip).limit(limit).all()

    def count_for_client(
        self,
        client_id: uuid.UUID,
        status: Optional[OrderStatus] = None,
    ) -> int:
        q = self.db.query(Order).filter(Order.client_id == client_id)
        if status:
            q = q.filter(Order.status == status)
        return q.count()

    def list_for_seller(
        self,
        seller_id: uuid.UUID,
        status: Optional[OrderStatus] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Order]:
        q = (
            self.db.query(Order)
            .filter(Order.seller_id == seller_id)
            .filter(Order.status != OrderStatus.DRAFT)
            .filter(Order.status != OrderStatus.COMPLETED)
            .filter(Order.status != OrderStatus.CANCELLED)
            .options(joinedload(Order.approved_iteration))
        )
        if status:
            q = q.filter(Order.status == status)
        return q.order_by(desc(Order.created_at)).offset(skip).limit(limit).all()

    def count_for_seller(
        self,
        seller_id: uuid.UUID,
        status: Optional[OrderStatus] = None,
    ) -> int:
        q = (
            self.db.query(func.count(Order.id))
            .filter(Order.seller_id == seller_id)
            .filter(Order.status != OrderStatus.DRAFT)
            .filter(Order.status != OrderStatus.COMPLETED)
            .filter(Order.status != OrderStatus.CANCELLED)
        )
        if status:
            q = q.filter(Order.status == status)
        return q.scalar() or 0

    def create(
        self,
        *,
        client_id: uuid.UUID,
        seller_id: uuid.UUID,
        title: str,
        description: str,
        product_type: Optional[str] = None,
        product_options: Optional[Dict[str, str]] = None,
        quantity: int = 1,
        shipping_address: Optional[str] = None,
        shipping_number: Optional[str] = None,
        shipping_complement: Optional[str] = None,
        shipping_neighborhood: Optional[str] = None,
        shipping_city: Optional[str] = None,
        shipping_state: Optional[str] = None,
        shipping_zip_code: Optional[str] = None,
        shipping_phone: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> Order:
        order = Order(
            client_id=client_id,
            seller_id=seller_id,
            title=title,
            description=description,
            product_type=product_type,
            product_options=product_options or {},
            quantity=quantity,
            status=OrderStatus.DRAFT,
            shipping_address=shipping_address,
            shipping_number=shipping_number,
            shipping_complement=shipping_complement,
            shipping_neighborhood=shipping_neighborhood,
            shipping_city=shipping_city,
            shipping_state=shipping_state,
            shipping_zip_code=shipping_zip_code,
            shipping_phone=shipping_phone,
            image_url=image_url,
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def update(self, order: Order, **kwargs) -> Order:
        for k, v in kwargs.items():
            if hasattr(order, k):
                setattr(order, k, v)
        self.db.commit()
        self.db.refresh(order)
        return order

    def change_status(
        self,
        order: Order,
        new_status: OrderStatus,
        changed_by_id: Optional[uuid.UUID] = None,
        note: Optional[str] = None,
    ) -> Order:
        """Atualiza status e registra na auditoria."""
        old = order.status
        order.status = new_status

        now = datetime.now(timezone.utc)
        if new_status == OrderStatus.IN_ANALYSIS:
            order.submitted_at = now
        elif new_status == OrderStatus.APPROVED:
            order.approved_at = now
        elif new_status == OrderStatus.COMPLETED:
            order.completed_at = now

        history = OrderStatusHistory(
            order_id=order.id,
            from_status=old,
            to_status=new_status,
            changed_by_id=changed_by_id,
            note=note,
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(order)
        return order


class IterationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, iteration_id: uuid.UUID) -> Optional[ProjectIteration]:
        return (
            self.db.query(ProjectIteration)
            .filter(ProjectIteration.id == iteration_id)
            .first()
        )

    def list_by_order(self, order_id: uuid.UUID) -> List[ProjectIteration]:
        return (
            self.db.query(ProjectIteration)
            .filter(ProjectIteration.order_id == order_id)
            .order_by(ProjectIteration.version)
            .all()
        )

    def next_version(self, order_id: uuid.UUID) -> int:
        result = (
            self.db.query(func.max(ProjectIteration.version))
            .filter(ProjectIteration.order_id == order_id)
            .scalar()
        )
        return (result or 0) + 1

    def create(
        self,
        *,
        order_id: uuid.UUID,
        description: str,
        prompt: Optional[str] = None,
        ai_model: Optional[str] = None,
        status: IterationStatus = IterationStatus.PENDING,
        image_key: Optional[str] = None,
    ) -> ProjectIteration:
        version = self.next_version(order_id)
        iteration = ProjectIteration(
            order_id=order_id,
            version=version,
            description=description,
            prompt=prompt,
            ai_model=ai_model,
            status=status,
            image_key=image_key,
        )
        self.db.add(iteration)
        self.db.commit()
        self.db.refresh(iteration)
        return iteration

    def update(self, iteration: ProjectIteration, **kwargs) -> ProjectIteration:
        for k, v in kwargs.items():
            if hasattr(iteration, k):
                setattr(iteration, k, v)
        self.db.commit()
        self.db.refresh(iteration)
        return iteration

    def mark_approved_unique(self, iteration: ProjectIteration) -> ProjectIteration:
        """Marca a iteracao como APPROVED e revoga aprovacao das outras do mesmo pedido."""
        # Reseta as outras (que estavam APPROVED) para READY
        self.db.query(ProjectIteration).filter(
            ProjectIteration.order_id == iteration.order_id,
            ProjectIteration.id != iteration.id,
            ProjectIteration.status == IterationStatus.APPROVED,
        ).update({ProjectIteration.status: IterationStatus.READY})

        iteration.status = IterationStatus.APPROVED
        self.db.commit()
        self.db.refresh(iteration)
        return iteration


class OrderReferenceImageRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, image_id: uuid.UUID) -> Optional[OrderReferenceImage]:
        return self.db.query(OrderReferenceImage).filter(OrderReferenceImage.id == image_id).first()

    def list_by_order(self, order_id: uuid.UUID) -> List[OrderReferenceImage]:
        return (
            self.db.query(OrderReferenceImage)
            .filter(OrderReferenceImage.order_id == order_id)
            .order_by(OrderReferenceImage.position, OrderReferenceImage.created_at)
            .all()
        )

    def create(
        self,
        *,
        order_id: uuid.UUID,
        image_key: str,
        caption: Optional[str] = None,
        position: int = 0,
    ) -> OrderReferenceImage:
        image = OrderReferenceImage(
            order_id=order_id,
            image_key=image_key,
            caption=caption,
            position=position,
        )
        self.db.add(image)
        self.db.commit()
        self.db.refresh(image)
        return image

    def delete(self, image: OrderReferenceImage) -> None:
        self.db.delete(image)
        self.db.commit()
