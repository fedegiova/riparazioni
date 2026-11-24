"""finalize repair working time

Adds the frozen archive total, the work-log description, and the singleton
transaction guard. Existing archived repairs are backfilled with the elapsed
work-log total they reported before this migration (the raw sum, not the new
calendar-adjusted calculation), so their displayed figures do not change.

Revision ID: b2c4d6e8f0a1
Revises: a3f1c7e29b04
Create Date: 2026-11-22 16:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b2c4d6e8f0a1'
down_revision = 'a3f1c7e29b04'
branch_labels = None
depends_on = None


REPAIRS = sa.table(
    'REPAIRS',
    sa.column('id', sa.Integer),
    sa.column('end_data', sa.DateTime),
    sa.column('archived_total_hours', sa.Float),
)
WORK_LOG = sa.table(
    'REPAIR_WORK_LOG',
    sa.column('id_repairs', sa.Integer),
    sa.column('start_time', sa.DateTime),
    sa.column('end_time', sa.DateTime),
)


def _backfill_archived_totals() -> None:
    """Freeze the pre-change totals of repairs that are already archived.

    The old application computed a repair's total as the sum of its work-log
    (end - start) durations, contributing zero for entries missing a bound.
    Reproducing exactly that keeps historical figures unchanged; the new
    calendar-aware calculation applies only to live reads and new archives.
    """
    conn = op.get_bind()
    repair_ids = conn.execute(
        sa.select(REPAIRS.c.id).where(REPAIRS.c.end_data.is_not(None))
    ).scalars().all()
    for repair_id in repair_ids:
        rows = conn.execute(
            sa.select(WORK_LOG.c.start_time, WORK_LOG.c.end_time).where(
                WORK_LOG.c.id_repairs == repair_id
            )
        ).all()
        total = 0.0
        for start, end in rows:
            if start is not None and end is not None:
                total += (end - start).total_seconds() / 3600.0
        conn.execute(
            sa.update(REPAIRS)
            .where(REPAIRS.c.id == repair_id)
            .values(archived_total_hours=total)
        )


def upgrade():
    op.add_column(
        'REPAIRS',
        sa.Column('archived_total_hours', sa.Float(), nullable=True),
    )
    op.add_column(
        'REPAIR_WORK_LOG',
        sa.Column('description', sa.String(length=4000), nullable=True),
    )
    op.create_table(
        'TRANSACTION_GUARDS',
        # Fixed singleton key (id = 1): autoincrement=False keeps it a plain
        # INT instead of an IDENTITY column, so the seed insert below works on
        # SQL Server without IDENTITY_INSERT.
        sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    # Keyed singleton: the guard row every mutating repair request updates.
    op.execute(sa.text("INSERT INTO TRANSACTION_GUARDS (id, version) VALUES (1, 0)"))
    _backfill_archived_totals()


def downgrade():
    with op.batch_alter_table('REPAIR_WORK_LOG', schema=None) as batch_op:
        batch_op.drop_column('description')
    with op.batch_alter_table('REPAIRS', schema=None) as batch_op:
        batch_op.drop_column('archived_total_hours')
    op.drop_table('TRANSACTION_GUARDS')