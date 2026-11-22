"""track refrigerant service

Adds the refrigerator installation link and gas type, the repair gas-equipment
lock, and the new work-log gas-operation columns. The obsolete state/weight
columns are intentionally left in place and unused: the deployed schema may or
may not carry them, and this migration must not require them. No existing
work-log row, cylinder balance, or repair link is rewritten.

Revision ID: e4a1c9d27f30
Revises: b2c4d6e8f0a1
Create Date: 2026-11-23 10:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e4a1c9d27f30'
down_revision = 'b2c4d6e8f0a1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'REFRIGERATORS',
        sa.Column('allestimento_id', sa.Integer(), nullable=True),
    )
    op.add_column(
        'REFRIGERATORS',
        sa.Column('gas_kind', sa.String(length=32), nullable=True),
    )
    # At most one installed unit per allestimento. Filtered to non-NULL links so
    # any number of uninstalled units may coexist (SQLite and MSSQL both support
    # the filtered form; MSSQL rejects a plain unique index over many NULLs).
    op.create_index(
        'uq_refrigerators_allestimento',
        'REFRIGERATORS',
        ['allestimento_id'],
        unique=True,
        sqlite_where=sa.text('allestimento_id IS NOT NULL'),
        mssql_where=sa.text('allestimento_id IS NOT NULL'),
    )

    # Server default keeps the NOT NULL column addable on SQLite and MSSQL; the
    # check constraint is not needed because the service sets the value.
    op.add_column(
        'REPAIRS',
        sa.Column(
            'gas_equipment_locked',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('0'),
        ),
    )

    op.add_column(
        'REPAIR_WORK_LOG',
        sa.Column('gas_operation', sa.String(length=20), nullable=True),
    )
    op.add_column(
        'REPAIR_WORK_LOG',
        sa.Column('gas_measured_kg', sa.Float(), nullable=True),
    )
    op.add_column(
        'REPAIR_WORK_LOG',
        sa.Column('gas_nameplate_kg', sa.Float(), nullable=True),
    )


def downgrade():
    with op.batch_alter_table('REPAIR_WORK_LOG') as batch_op:
        batch_op.drop_column('gas_nameplate_kg')
        batch_op.drop_column('gas_measured_kg')
        batch_op.drop_column('gas_operation')

    with op.batch_alter_table('REPAIRS') as batch_op:
        batch_op.drop_column('gas_equipment_locked')

    op.drop_index('uq_refrigerators_allestimento', table_name='REFRIGERATORS')
    with op.batch_alter_table('REFRIGERATORS') as batch_op:
        batch_op.drop_column('gas_kind')
        batch_op.drop_column('allestimento_id')
