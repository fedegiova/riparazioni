"""pictures thumbnail_path

Revision ID: a3f1c7e29b04
Revises: c8d7e6f5a4b3
Create Date: 2026-11-21 19:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a3f1c7e29b04'
down_revision = 'c8d7e6f5a4b3'
branch_labels = None
depends_on = None


def upgrade():
    # Nullable: pictures stored before the minified derivative existed have no
    # path until the service generates one on first read.
    op.add_column(
        'PICTURES',
        sa.Column('thumbnail_path', sa.String(length=1024), nullable=True),
    )
    # Partial unique index: several rows may have a NULL derivative, so a plain
    # unique constraint would reject all but one of them on MSSQL. SQLite and
    # MSSQL both support the filtered form.
    op.create_index(
        'uq_pictures_thumbnail_path',
        'PICTURES',
        ['thumbnail_path'],
        unique=True,
        sqlite_where=sa.text('thumbnail_path IS NOT NULL'),
        mssql_where=sa.text('thumbnail_path IS NOT NULL'),
    )


def downgrade():
    op.drop_index('uq_pictures_thumbnail_path', table_name='PICTURES')
    with op.batch_alter_table('PICTURES') as batch_op:
        batch_op.drop_column('thumbnail_path')
