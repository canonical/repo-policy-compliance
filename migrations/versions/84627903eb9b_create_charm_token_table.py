"""create charm token table

Revision ID: 84627903eb9b
Revises:
Create Date: 2024-04-19 00:36:09.331819

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "84627903eb9b"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("one_time_token", sa.Column("value", sa.String, primary_key=True))


def downgrade() -> None:
    op.drop_table("one_time_token")
