"""power features: folders, link_rules, link folder/archived/max_clicks

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'folders',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_folders_workspace_id', 'folders', ['workspace_id'])
    op.create_table(
        'link_rules',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('link_id', sa.String(length=36), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('match_value', sa.String(length=255), nullable=False),
        sa.Column('destination_url', sa.Text(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['link_id'], ['links.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_link_rules_link_id', 'link_rules', ['link_id'])
    # Add columns to links
    op.add_column('links', sa.Column('folder_id', sa.String(length=36), nullable=True))
    op.add_column('links', sa.Column('is_archived', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('links', sa.Column('max_clicks', sa.Integer(), nullable=True))
    op.create_index('ix_links_folder_id', 'links', ['folder_id'])
    op.create_foreign_key('fk_links_folder_id', 'links', 'folders', ['folder_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('fk_links_folder_id', 'links', type_='foreignkey')
    op.drop_index('ix_links_folder_id', table_name='links')
    op.drop_column('links', 'max_clicks')
    op.drop_column('links', 'is_archived')
    op.drop_column('links', 'folder_id')
    op.drop_index('ix_link_rules_link_id', table_name='link_rules')
    op.drop_table('link_rules')
    op.drop_index('ix_folders_workspace_id', table_name='folders')
    op.drop_table('folders')
