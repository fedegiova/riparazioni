"""add refills and cylinder archive

Revision ID: b7c2e9f14a06
Revises: 75d9543863f9
Create Date: 2026-11-21 16:40:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b7c2e9f14a06'
down_revision = '75d9543863f9'
branch_labels = None
depends_on = None


def upgrade():
    # Refills are owned by a cylinder and record when it went out and came
    # back full. The amount added is implicit (full - remaining before).
    op.create_table(
        'REFILLS',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('gas_cylinder_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('reference', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['gas_cylinder_id'], ['GAS_CYLINDERS.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # Reversible retire flag. A server default keeps the NOT NULL column
    # addable on both SQLite and MSSQL.
    op.add_column(
        'GAS_CYLINDERS',
        sa.Column('archived', sa.Boolean(), nullable=False, server_default=sa.text('0')),
    )

    # The database is empty, so no backfill is needed. Batch mode emits the
    # SQLite table rebuild while remaining a passthrough on MSSQL.
    with op.batch_alter_table('GAS_CYLINDERS') as batch_op:
        batch_op.alter_column(
            'full_weight', existing_type=sa.Float(), nullable=False
        )


def downgrade():
    with op.batch_alter_table('GAS_CYLINDERS') as batch_op:
        batch_op.alter_column(
            'full_weight', existing_type=sa.Float(), nullable=True
        )
        batch_op.drop_column('archived')
    op.drop_table('REFILLS')
