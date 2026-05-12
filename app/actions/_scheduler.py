from __future__ import annotations

from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

DEFAULT_SCHEDULE = {
    "start_at": None,
    "end_at": None,
    "timezone": "Europe/Paris",
    "distribution": "linear",
    "batch_frequency": {"every": 1, "unit": "minute"},
    "batch_size": 50,
    "allowed_windows": [{"days": ["mon", "tue", "wed", "thu", "fri"], "start_hour": 9, "end_hour": 18}],
    "throttle": {"max_per_minute": 30, "max_per_hour": 500, "max_per_day": 5000},
    "paused": False,
    "runtime_state": {"lots_sent_today": 0, "lots_deferred": 0, "throttled_count": 0},
}

DAY_INDEX = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


def is_allowed_now(schedule: dict, now: datetime | None = None) -> bool:
    if schedule.get("paused"):
        return False
    current = now or datetime.now(UTC)
    tz = ZoneInfo(schedule.get("timezone") or "Europe/Paris")
    local = current.astimezone(tz)
    for window in schedule.get("allowed_windows", []):
        days = {DAY_INDEX[d] for d in window.get("days", []) if d in DAY_INDEX}
        if local.weekday() in days and time(window.get("start_hour", 0)) <= local.time() < time(window.get("end_hour", 24) % 24):
            return True
    return False


def batch_size_for(schedule: dict, remaining: int) -> int:
    size = int(schedule.get("batch_size") or 50)
    return max(0, min(size, remaining))
