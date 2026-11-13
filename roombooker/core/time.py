"""The only place that converts between UTC and UK time (AD-5).

Services work in aware UTC datetimes; the database holds UTC text
`YYYY-MM-DDTHH:MM:00Z`; the web layer turns UK dates and clock times into UTC with
`uk_to_utc` and back for display with the Jinja filters `clock` and `day`.
"""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

UK = ZoneInfo("Europe/London")
UTC_FORMAT = "%Y-%m-%dT%H:%M:00Z"


def utc_now() -> datetime:
    """Now, in UTC. Tests replace this to fix the clock."""
    return datetime.now(UTC)


def to_text(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime(UTC_FORMAT)


def ical_utc(moment: datetime) -> str:
    """`20261117T100000Z`: an iCalendar UTC date-time (RFC 5545 form 2)."""
    return moment.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def from_text(text: str) -> datetime:
    return datetime.strptime(text, UTC_FORMAT).replace(tzinfo=UTC)


def uk_now() -> datetime:
    return utc_now().astimezone(UK)


def parse_date(text: str) -> date | None:
    try:
        return date.fromisoformat(text.strip())
    except ValueError:
        return None


def parse_clock(text: str) -> time | None:
    text = text.strip()
    if len(text) != 5 or text[2] != ":":
        return None
    try:
        return time.fromisoformat(text)
    except ValueError:
        return None


def uk_to_utc(day: date, clock: time) -> datetime | None:
    """The UTC moment of a UK date and clock time, or None when the clocks skip it.

    In the autumn hour that happens twice, the first (summer time) one is meant.
    """
    local = datetime.combine(day, clock).replace(tzinfo=UK, fold=0)
    moment = local.astimezone(UTC)
    if moment.astimezone(UK).replace(tzinfo=None) != local.replace(tzinfo=None):
        return None
    return moment


def utc_to_uk(moment: datetime) -> tuple[date, str]:
    """The UK date and `HH:MM` clock time of a UTC moment; the inverse of `uk_to_utc`."""
    local = moment.astimezone(UK)
    return local.date(), local.strftime("%H:%M")


def uk_midnight(day: date) -> datetime:
    """The UTC moment a UK day starts. UK clocks change at 01:00 or 02:00, so midnight
    always exists and happens once."""
    return datetime.combine(day, time()).replace(tzinfo=UK).astimezone(UTC)


def week_start(day: date) -> date:
    """The Monday of `day`'s week."""
    return day - timedelta(days=day.weekday())


def next_quarter_hour(moment: datetime) -> datetime:
    """`moment` rounded up to a quarter hour (unchanged when it is on one)."""
    moment = moment.replace(second=0, microsecond=0) + (
        timedelta(minutes=1) if moment.second or moment.microsecond else timedelta()
    )
    return moment + timedelta(minutes=-moment.minute % 15)


def clock(moment: datetime) -> str:
    """`14:00`, in UK time."""
    return moment.astimezone(UK).strftime("%H:%M")


def day(moment: datetime) -> str:
    """`Tue 17 Nov`, in UK time."""
    local = moment.astimezone(UK)
    return f"{local:%a} {local.day} {local:%b}"


def short_date(moment: datetime) -> str:
    """`13 Nov`, in UK time."""
    local = moment.astimezone(UK)
    return f"{local.day} {local:%b}"


def length_label(minutes: int) -> str:
    """`15 min`, `1 h`, `1 h 45 min`."""
    hours, rest = divmod(minutes, 60)
    parts = ([f"{hours} h"] if hours else []) + ([f"{rest} min"] if rest else [])
    return " ".join(parts)
