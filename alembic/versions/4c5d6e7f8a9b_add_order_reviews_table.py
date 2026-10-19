"""add order reviews table

Revision ID: 4c5d6e7f8a9b
Revises: 7b8c9d0e1f2a
Create Date: 2026-10-18 14:27:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4c5d6e7f8a9b'
down_revision: Union[str, Sequence[str], None] = '7b8c9d0e1f2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'order_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('orders.id', ondelete='SET NULL'), nullable=True),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('client_name', sa.String(length=150), nullable=False, server_default='Cliente'),
        sa.Column('product_title', sa.String(length=200), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('is_edited', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_order_reviews_order_id', 'order_reviews', ['order_id'], unique=True)
    op.create_index('ix_order_reviews_seller_id', 'order_reviews', ['seller_id'])
    op.create_index('ix_order_reviews_client_id', 'order_reviews', ['client_id'])


def downgrade() -> None:
    op.drop_index('ix_order_reviews_client_id', table_name='order_reviews')
    op.drop_index('ix_order_reviews_seller_id', table_name='order_reviews')
    op.drop_index('ix_order_reviews_order_id', table_name='order_reviews')
    op.drop_table('order_reviews')
