"""add_job_title_and_url

Revision ID: 229a36116fce
Revises: 2ea79be9c026
Create Date: 2026-01-10 06:11:18.582337

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '229a36116fce'
down_revision: Union[str, Sequence[str], None] = '2ea79be9c026'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('print_jobs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('title', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('url', sa.String(length=1000), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('print_jobs', schema=None) as batch_op:
        batch_op.drop_column('url')
        batch_op.drop_column('title')
