"""add last_notified_at and token_version

Revision ID: a1b2c3d4e5f6
Revises: 8ce3d23c8840
Create Date: 2026-05-21 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '8ce3d23c8840'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('links', sa.Column('last_notified_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('token_version', sa.Integer(), nullable=False, server_default=sa.text('0')))


def downgrade() -> None:
    op.drop_column('users', 'token_version')
    op.drop_column('links', 'last_notified_at')
