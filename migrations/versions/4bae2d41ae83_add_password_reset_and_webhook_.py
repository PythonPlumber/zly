"""add_password_reset_and_webhook_deliveries

Revision ID: 4bae2d41ae83
Revises: a1b2c3d4e5f6
Create Date: 2026-05-26 23:27:55.563152

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4bae2d41ae83'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('password_reset_token', sa.String(length=64), nullable=True))
    op.add_column('users', sa.Column('password_reset_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        'webhook_deliveries',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('webhook_id', sa.String(length=36), sa.ForeignKey('webhooks.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('event', sa.String(length=50), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default=sa.text('pending')),
        sa.Column('response_code', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('attempt', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column('webhooks', sa.Column('max_retries', sa.Integer(), nullable=False, server_default=sa.text('5')))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('webhooks', 'max_retries')
    op.drop_table('webhook_deliveries')
    op.drop_column('users', 'password_reset_expires_at')
    op.drop_column('users', 'password_reset_token')
