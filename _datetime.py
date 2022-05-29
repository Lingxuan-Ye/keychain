from datetime import datetime, timezone
from typing import Optional


def timestamp(datetime_: Optional[datetime] = None) -> float:
    if datetime_ is None:
        return datetime.now().timestamp()
    if not isinstance(datetime_, datetime):
        raise TypeError
    return datetime_.timestamp()


def fromtimestamp(timestamp: float, local: bool = True) -> datetime:
    if local:
        return datetime.fromtimestamp(timestamp, tz=None)
    else:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def isoformat(datetime_: datetime) -> str:
    if not isinstance(datetime_, datetime):
        raise TypeError
    return datetime_.isoformat(sep=" ")


def fromisoformat(time_str: str) -> datetime:
    return datetime.fromisoformat(time_str)
