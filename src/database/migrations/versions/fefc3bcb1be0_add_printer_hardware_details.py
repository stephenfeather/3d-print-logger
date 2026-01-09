"""add_printer_hardware_details

Revision ID: fefc3bcb1be0
Revises: ypdqxrr704l1
Create Date: 2026-01-09 15:35:24.984380

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fefc3bcb1be0'
down_revision: Union[str, Sequence[str], None] = 'ypdqxrr704l1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add printer hardware details columns
    op.add_column('printers', sa.Column('printer_type', sa.String(length=50), nullable=True))
    op.add_column('printers', sa.Column('make', sa.String(length=100), nullable=True))
    op.add_column('printers', sa.Column('model', sa.String(length=100), nullable=True))
    op.add_column('printers', sa.Column('description', sa.String(length=500), nullable=True))

    # Add printer specifications
    op.add_column('printers', sa.Column('filament_diameter', sa.Float(), nullable=True, server_default='1.75'))
    op.add_column('printers', sa.Column('nozzle_diameter', sa.Float(), nullable=True))
    op.add_column('printers', sa.Column('bed_x', sa.Float(), nullable=True))
    op.add_column('printers', sa.Column('bed_y', sa.Float(), nullable=True))
    op.add_column('printers', sa.Column('bed_z', sa.Float(), nullable=True))
    op.add_column('printers', sa.Column('has_heated_bed', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('printers', sa.Column('has_heated_chamber', sa.Boolean(), nullable=False, server_default='0'))

    # Add material tracking
    op.add_column('printers', sa.Column('loaded_materials', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove columns in reverse order
    op.drop_column('printers', 'loaded_materials')
    op.drop_column('printers', 'has_heated_chamber')
    op.drop_column('printers', 'has_heated_bed')
    op.drop_column('printers', 'bed_z')
    op.drop_column('printers', 'bed_y')
    op.drop_column('printers', 'bed_x')
    op.drop_column('printers', 'nozzle_diameter')
    op.drop_column('printers', 'filament_diameter')
    op.drop_column('printers', 'description')
    op.drop_column('printers', 'model')
    op.drop_column('printers', 'make')
    op.drop_column('printers', 'printer_type')
