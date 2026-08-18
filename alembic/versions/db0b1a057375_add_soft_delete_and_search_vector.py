"""add_soft_delete_and_search_vector

Revision ID: db0b1a057375
Revises: b4a2d6c00e20
Create Date: 2026-08-18 21:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = 'db0b1a057375'
down_revision: Union[str, None] = 'b4a2d6c00e20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('messages')]

    if 'updated_at' not in columns:
        op.add_column('messages', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    if 'deleted_at' not in columns:
        op.add_column('messages', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    if 'search_vector' not in columns:
        op.add_column('messages', sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True))
        # Only run the update if we added the column
        op.execute("""
            UPDATE messages SET search_vector = 
            setweight(to_tsvector('english', coalesce(content, '')), 'A') ||
            setweight(to_tsvector('english', coalesce((SELECT username FROM users WHERE users.id = messages.user_id), '')), 'B')
        """)
        op.create_index('idx_message_search_vector', 'messages', ['search_vector'], postgresql_using='gin')
    else:
        # If search_vector exists, ensure index exists
        indexes = [idx['name'] for idx in inspector.get_indexes('messages')]
        if 'idx_message_search_vector' not in indexes:
            op.create_index('idx_message_search_vector', 'messages', ['search_vector'], postgresql_using='gin')