"""add address fields to users

Revision ID: 5e6f7a8b9c0d
Revises: 4c5d6e7f8a9b
Create Date: 2026-10-18 14:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e6f7a8b9c0d'
down_revision: Union[str, None] = '4c5d6e7f8a9b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('zip_code', sa.String(length=10), nullable=True))
    op.add_column('users', sa.Column('address', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('number', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('complement', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('neighborhood', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('city', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('state', sa.String(length=10), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'state')
    op.drop_column('users', 'city')
    op.drop_column('users', 'neighborhood')
    op.drop_column('users', 'complement')
    op.drop_column('users', 'number')
    op.drop_column('users', 'address')
    op.drop_column('users', 'zip_code')
