"""Working-time calculation against the workshop calendar.

The workshop defines weekday working intervals and yearly holiday ranges in
its settings. A repair's adjusted worked time is the sum, over its completed
work logs, of the wall-clock time that falls inside a working interval and
outside a holiday range. Datetimes are naive local wall-clock values, matching
the rest of the repair module.

The calendar is normalized once per calculation batch: weekday intervals are
merged so overlapping configured intervals cannot count the same minute twice,
and holiday ranges are kept as inclusive date pairs. Time is never
de-duplicated across logs: two operators working the same hour are two worked
hours.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def _minutes(value: str) -> int:
    hours, minutes = value.split(":")
    return int(hours) * 60 + int(minutes)


def _merge(intervals) -> tuple:
    """Union of ``(begin, end)`` minute pairs, sorted and non-overlapping."""
    merged: list[tuple[int, int]] = []
    for begin, end in sorted((b, e) for b, e in intervals if b < e):
        if merged and begin <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((begin, end))
    return tuple(merged)


def _parse_date(value):
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


@dataclass(frozen=True)
class Calendar:
    """Normalized workshop calendar: weekday minutes and holiday date ranges."""

    intervals: tuple
    holidays: tuple

    @classmethod
    def from_settings(cls, working_hours, holidays) -> "Calendar":
        by_weekday: dict[int, tuple] = {}
        if isinstance(working_hours, dict):
            for index, day in enumerate(WEEKDAYS):
                raw = working_hours.get(day, [])
                pairs = []
                if isinstance(raw, list):
                    for interval in raw:
                        if (
                            isinstance(interval, (list, tuple))
                            and len(interval) == 2
                            and isinstance(interval[0], str)
                            and isinstance(interval[1], str)
                        ):
                            try:
                                pairs.append(
                                    (_minutes(interval[0]), _minutes(interval[1]))
                                )
                            except ValueError:
                                continue
                by_weekday[index] = _merge(pairs)

        ranges: list[tuple[date, date]] = []
        if isinstance(holidays, dict):
            for year_ranges in holidays.values():
                if not isinstance(year_ranges, list):
                    continue
                for entry in year_ranges:
                    if not isinstance(entry, dict):
                        continue
                    start = _parse_date(entry.get("from"))
                    end = _parse_date(entry.get("to"))
                    if start is not None and end is not None and start <= end:
                        ranges.append((start, end))

        return cls(
            intervals=tuple(by_weekday.get(index, ()) for index in range(7)),
            holidays=tuple(ranges),
        )

    def is_holiday(self, when: date) -> bool:
        return any(start <= when <= end for start, end in self.holidays)

    def windows(self, when: date) -> tuple:
        """Working minute windows for *when*; empty on a closed or holiday day."""
        if self.is_holiday(when):
            return ()
        return self.intervals[when.weekday()]


def entry_hours(start: datetime | None, end: datetime | None, calendar: Calendar) -> float:
    """Adjusted worked hours of one completed log.

    A running, incomplete, zero-length or reversed log contributes zero.
    """
    if start is None or end is None or end <= start:
        return 0.0

    total_seconds = 0.0
    day = start.date()
    last = end.date()
    while day <= last:
        midnight = datetime.combine(day, time.min)
        for begin, finish in calendar.windows(day):
            low = max(start, midnight + timedelta(minutes=begin))
            high = min(end, midnight + timedelta(minutes=finish))
            if high > low:
                total_seconds += (high - low).total_seconds()
        day += timedelta(days=1)
    return total_seconds / 3600.0