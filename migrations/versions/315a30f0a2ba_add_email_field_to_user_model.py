"""Add email field to User model

Revision ID: 315a30f0a2ba
Revises: 5a1e4981a780
Create Date: 2024-05-10 19:44:56.333574

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '315a30f0a2ba'
down_revision: Union[str, None] = '5a1e4981a780'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
