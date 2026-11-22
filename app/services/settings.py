"""Application settings: JSON values in a name/value store.

Settings are stored as text (``SETTINGS.value``) but this service exchanges
parsed JSON, so the storage encoding never leaks into the API or the UI.
Known settings have a default (returned when never written) and a validator
enforced on write; unknown names accept any JSON value.

Every mutating function validates first and never commits: the route commits,
so a rejected write (400) leaves stored data unchanged and a bulk update is
atomic.
"""

import json
import re
from datetime import date

from app.extensions import db
from app.models import Settings
from app.services.errors import BadRequest, NotFound

WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_YEAR_RE = re.compile(r"^\d{4}$")


def _empty_working_hours() -> dict:
    day_hours = [["08:00", "12:00"], ["13:00", "16:30"]]
    return {
        "mon": day_hours,
        "tue": day_hours,
        "wed": day_hours,
        "thu": day_hours,
        "fri": day_hours,
        "sat": [["08:00", "12:00"]],
        "sun": [],
    }


# Defaults are factories so a caller can never mutate the stored default.
_DEFAULT_FACTORIES = {
    "operators": lambda: ["FABRI", "CLAUDIO", "PASQUALE", "MOHAMMED"],
    "working_hours": _empty_working_hours,
    "holidays": dict,
    "gas_types": lambda: ["R32", "R410A"],
}


# --- validators (read-only) --------------------------------------------------


def _is_time(value) -> bool:
    return isinstance(value, str) and bool(_TIME_RE.match(value))


def _validate_operators(value) -> None:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise BadRequest("operators must be a list of non-empty strings")


def _validate_gas_types(value) -> None:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise BadRequest("gas_types must be a list of non-empty strings")


def _validate_working_hours(value) -> None:
    if not isinstance(value, dict):
        raise BadRequest("working_hours must be an object keyed by weekday")
    for day, intervals in value.items():
        if day not in WEEKDAYS:
            raise BadRequest(f"working_hours has an unknown weekday {day!r}")
        if not isinstance(intervals, list):
            raise BadRequest(f"working_hours.{day} must be a list of intervals")
        for interval in intervals:
            if (
                not isinstance(interval, list)
                or len(interval) != 2
                or not _is_time(interval[0])
                or not _is_time(interval[1])
                or interval[0] >= interval[1]
            ):
                raise BadRequest(
                    f"working_hours.{day} intervals must be [HH:MM, HH:MM] "
                    "with the begin before the end"
                )


def _parse_date(value):
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _validate_holidays(value) -> None:
    if not isinstance(value, dict):
        raise BadRequest("holidays must be an object keyed by year")
    for year, ranges in value.items():
        if not isinstance(year, str) or not _YEAR_RE.match(year):
            raise BadRequest("holidays keys must be four-digit year strings")
        if not isinstance(ranges, list):
            raise BadRequest(f"holidays.{year} must be a list of ranges")
        for entry in ranges:
            if not isinstance(entry, dict):
                raise BadRequest(f"holidays.{year} ranges must be objects")
            name = entry.get("name")
            if not isinstance(name, str) or not name:
                raise BadRequest(f"holidays.{year} ranges need a non-empty name")
            start = _parse_date(entry.get("from"))
            end = _parse_date(entry.get("to"))
            if start is None or end is None:
                raise BadRequest(f"holidays.{year} ranges need ISO from/to dates")
            if start > end:
                raise BadRequest(f"holidays.{year} range from must not be after to")
            if start.year != int(year) or end.year != int(year):
                raise BadRequest(f"holidays.{year} ranges must fall within {year}")


_VALIDATORS = {
    "operators": _validate_operators,
    "working_hours": _validate_working_hours,
    "holidays": _validate_holidays,
    "gas_types": _validate_gas_types,
}


def _validate(name: str, value) -> None:
    """Validate a known setting; unknown names accept any JSON value."""
    validator = _VALIDATORS.get(name)
    if validator is not None:
        validator(value)


# --- reads -------------------------------------------------------------------

def _row(name: str):
    return db.session.get(Settings, name)


def list_settings() -> dict:
    """Every stored setting, plus defaults for known settings never written."""
    rows = db.session.execute(db.select(Settings)).scalars().all()
    result = {row.name: json.loads(row.value) for row in rows}
    for name, factory in _DEFAULT_FACTORIES.items():
        result.setdefault(name, factory())
    return result


def get_setting(name: str):
    """One setting's value; known-but-unwritten returns its default (404 else)."""
    row = _row(name)
    if row is not None:
        return json.loads(row.value)
    if name in _DEFAULT_FACTORIES:
        return _DEFAULT_FACTORIES[name]()
    raise NotFound(f"setting {name!r} not found")


# --- writes ------------------------------------------------------------------

def _upsert(name: str, value) -> None:
    encoded = json.dumps(value)
    row = _row(name)
    if row is None:
        db.session.add(Settings(name=name, value=encoded))
    else:
        row.value = encoded


def set_setting(name: str, value) -> None:
    _validate(name, value)
    _upsert(name, value)


def set_settings(mapping: dict) -> None:
    """Validate every entry first, then apply — a rejection changes nothing."""
    for name, value in mapping.items():
        _validate(name, value)
    for name, value in mapping.items():
        _upsert(name, value)


def delete_setting(name: str) -> None:
    row = _row(name)
    if row is None:
        raise NotFound(f"setting {name!r} not found")
    db.session.delete(row)
