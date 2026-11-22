"""Cross-worker mutation guard for repair lifecycle and timer writes.

A single row (``TRANSACTION_GUARDS.id = 1``) is updated at the start of every
mutating request that can change a repair's archive state or an operator's
running timer. The row update takes a write lock in the current transaction, so
concurrent requests queue across processes instead of interleaving their reads
and writes. A process-local mutex would not cover multiple workers.

The guard is intentionally coarse: unrelated operators are briefly serialized.
That is the trade-off for a simple, cross-database (SQLite and SQL Server)
mechanism that also covers "no previous timer exists" races, where locking the
previous row is impossible.

Callers must not commit the guard on their own: the route commits with the
related writes, and the API error handler rolls the session back on a rejected
request so a failed validation never leaves the guard update pending.
"""

from sqlalchemy import insert, update
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import TransactionGuard

GUARD_ID = 1


def acquire() -> None:
    """Take the singleton mutation guard for the current transaction."""
    result = db.session.execute(
        update(TransactionGuard)
        .where(TransactionGuard.id == GUARD_ID)
        .values(version=TransactionGuard.version + 1)
    )
    if result.rowcount:
        return

    # Databases built from the metadata (tests, fresh dev databases) have no
    # migration-seeded row. Create it; a concurrent creator loses the race and
    # falls back to updating the row it created.
    try:
        with db.session.begin_nested():
            db.session.execute(
                insert(TransactionGuard).values(id=GUARD_ID, version=1)
            )
    except IntegrityError:
        db.session.execute(
            update(TransactionGuard)
            .where(TransactionGuard.id == GUARD_ID)
            .values(version=TransactionGuard.version + 1)
        )