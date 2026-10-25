import os
from datetime import UTC, date, datetime, tzinfo

from utils.runtime import demo_mode

DEFAULT_DEMO_AS_OF = "2026-01-29T12:00:00+00:00"


def now(timezone: tzinfo | None = None) -> datetime:
    return business_now(datetime, timezone)


def business_today(clock: type[date]) -> date:
    if demo_mode():
        return now().date()
    return clock.today()


def business_now(clock: type[datetime], timezone: tzinfo | None = None) -> datetime:
    value = os.environ.get("BURNDOWN_AS_OF") if demo_mode() else None
    if value is None:
        return clock.now(timezone) if timezone is not None else clock.now()
    reference = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if reference.tzinfo is None:
        raise ValueError("BURNDOWN_AS_OF must include a timezone")
    if timezone is None:
        return reference.astimezone(UTC).replace(tzinfo=None)
    return reference.astimezone(timezone)
