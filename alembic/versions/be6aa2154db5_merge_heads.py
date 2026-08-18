"""merge heads

Revision ID: be6aa2154db5
Revises: b6ad257c0892, db0b1a057375
Create Date: 2026-08-18 21:53:34.366968

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be6aa2154db5'
down_revision: Union[str, None] = ('b6ad257c0892', 'db0b1a057375')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
