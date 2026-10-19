"""add shipping neighborhood to orders

Revision ID: 7b8c9d0e1f2a
Revises: 9a1b2c3d4e5f
Create Date: 2026-10-17 13:46:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b8c9d0e1f2a'
down_revision: Union[str, Sequence[str], None] = '9a1b2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('shipping_neighborhood', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('orders', 'shipping_neighborhood')
