"""Calendar-adjusted working-time unit tests (task 2.1)."""

from datetime import datetime

from app.services.working_time import Calendar, entry_hours

WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def _schedule(intervals_per_day):
    """Working hours with the same intervals every day."""
    return {day: intervals_per_day for day in WEEKDAYS}


def _at(value: str) -> datetime:
    return datetime.fromisoformat(value)


DEFAULT_HOURS = {
    "mon": [["08:00", "12:00"], ["13:00", "16:30"]],
    "tue": [["08:00", "12:00"], ["13:00", "16:30"]],
    "wed": [["08:00", "12:00"], ["13:00", "16:30"]],
    "thu": [["08:00", "12:00"], ["13:00", "16:30"]],
    "fri": [["08:00", "12:00"], ["13:00", "16:30"]],
    "sat": [["08:00", "12:00"]],
    "sun": [],
}


class TestEntryHours:
    def test_lunch_break_and_time_after_closing_do_not_count(self):
        calendar = Calendar.from_settings(DEFAULT_HOURS, {})
        # Thursday 11:30-17:00: 30m before lunch + 3h30 after it = 4h.
        assert entry_hours(
            _at("2026-01-01T11:30:00"), _at("2026-01-01T17:00:00"), calendar
        ) == 4.0

    def test_overlapping_configured_intervals_count_once(self):
        calendar = Calendar.from_settings(
            _schedule([["08:00", "12:00"], ["11:00", "13:00"]]), {}
        )
        assert entry_hours(
            _at("2026-01-01T08:00:00"), _at("2026-01-01T13:00:00"), calendar
        ) == 5.0

    def test_closed_weekday_contributes_zero(self):
        calendar = Calendar.from_settings(DEFAULT_HOURS, {})
        # 2026-01-04 is a Sunday (closed in the default schedule).
        assert entry_hours(
            _at("2026-01-04T08:00:00"), _at("2026-01-04T12:00:00"), calendar
        ) == 0.0

    def test_multi_day_log_skips_closed_days_and_inclusive_vacations(self):
        calendar = Calendar.from_settings(
            _schedule([["08:00", "12:00"]]),
            {
                "2026": [{"from": "2026-12-30", "to": "2026-12-31", "name": "Chiusura"}],
                "2027": [{"from": "2027-01-01", "to": "2027-01-02", "name": "Chiusura"}],
            },
        )
        # 2026-12-28..2027-01-03: only the 28th, 29th and 3rd are worked.
        assert entry_hours(
            _at("2026-12-28T08:00:00"), _at("2027-01-03T12:00:00"), calendar
        ) == 12.0

    def test_single_vacation_day_is_excluded(self):
        calendar = Calendar.from_settings(
            DEFAULT_HOURS,
            {"2026": [{"from": "2026-01-01", "to": "2026-01-01", "name": "Festa"}]},
        )
        assert entry_hours(
            _at("2026-01-01T08:00:00"), _at("2026-01-01T12:00:00"), calendar
        ) == 0.0

    def test_incomplete_or_invalid_logs_contribute_zero(self):
        calendar = Calendar.from_settings(DEFAULT_HOURS, {})
        assert entry_hours(None, _at("2026-01-01T12:00:00"), calendar) == 0.0
        assert entry_hours(_at("2026-01-01T08:00:00"), None, calendar) == 0.0
        assert entry_hours(
            _at("2026-01-01T12:00:00"), _at("2026-01-01T08:00:00"), calendar
        ) == 0.0
        assert entry_hours(
            _at("2026-01-01T08:00:00"), _at("2026-01-01T08:00:00"), calendar
        ) == 0.0

    def test_absent_weekday_keys_are_closed(self):
        calendar = Calendar.from_settings({"mon": [["08:00", "12:00"]]}, {})
        # Tuesday is absent from the explicitly saved schedule.
        assert entry_hours(
            _at("2026-01-06T08:00:00"), _at("2026-01-06T12:00:00"), calendar
        ) == 0.0

    def test_partial_window_edges_count_exactly(self):
        calendar = Calendar.from_settings(
            _schedule([["08:00", "12:00"]]), {}
        )
        assert entry_hours(
            _at("2026-01-01T07:00:00"), _at("2026-01-01T09:15:00"), calendar
        ) == 1.25
        assert entry_hours(
            _at("2026-01-01T11:30:00"), _at("2026-01-01T14:00:00"), calendar
        ) == 0.5