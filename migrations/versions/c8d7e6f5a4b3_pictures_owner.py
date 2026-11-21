"""pictures owner columns, drop picture_ref

Revision ID: c8d7e6f5a4b3
Revises: b7c2e9f14a06
Create Date: 2026-11-21 18:30:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c8d7e6f5a4b3'
down_revision = 'b7c2e9f14a06'
branch_labels = None
depends_on = None


def _drop_foreign_key_on(table: str, column: str) -> None:
    """Drop the FK on *column* when the backend names it (MSSQL).

    SQLite does not name foreign keys; there the batch table rebuild below
    removes the constraint along with the column.
    """
    inspector = sa.inspect(op.get_bind())
    for fk in inspector.get_foreign_keys(table):
        if column in fk["constrained_columns"] and fk.get("name"):
            op.drop_constraint(fk["name"], table, type_="foreignkey")


def upgrade():
    # A picture now belongs to exactly one owner. The table is empty, so the
    # NOT NULL columns need no backfill; batch mode rebuilds on SQLite and is a
    # passthrough on MSSQL.
    with op.batch_alter_table('PICTURES') as batch_op:
        batch_op.add_column(sa.Column('owner_type', sa.String(length=16), nullable=False))
        batch_op.add_column(sa.Column('owner_id', sa.Integer(), nullable=False))
        batch_op.create_unique_constraint('uq_pictures_path', ['path'])

    # The single picture_ref link is replaced by the owner columns on PICTURES.
    for table in ('GAS_CYLINDERS', 'SERVICE_PARTS'):
        _drop_foreign_key_on(table, 'picture_ref')
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_column('picture_ref')


def downgrade():
    with op.batch_alter_table('PICTURES') as batch_op:
        batch_op.drop_constraint('uq_pictures_path', type_='unique')
        batch_op.drop_column('owner_id')
        batch_op.drop_column('owner_type')

    for table in ('GAS_CYLINDERS', 'SERVICE_PARTS'):
        with op.batch_alter_table(table) as batch_op:
            batch_op.add_column(sa.Column('picture_ref', sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                f'fk_{table.lower()}_picture', 'PICTURES', ['picture_ref'], ['id']
            )
