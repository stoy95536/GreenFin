"""
Shared date parsing and comparison helpers.

Why this module exists:
  Three services (verification, anomaly detection, data health) each had their own
  private _parse_date() copy, and they were NOT equivalent — data health accepted
  fewer formats than the others. A value normalised as "2026.03.15" was therefore
  treated as expired-checkable by anomaly detection but invisible to the Data Health
  expiry check, producing different verdicts for the same record depending on which
  service looked at it.

  All date interpretation now goes through this single implementation so that a date
  is either understood everywhere or nowhere.
"""

from datetime import date, datetime, timedelta
from typing import Optional

# Accepted input formats, in priority order.
# ISO first because normalization emits ISO 8601.
SUPPORTED_DATE_FORMATS: tuple[str, ...] = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y.%m.%d",
)


def parse_date(value: Optional[str]) -> Optional[date]:
    """
    Parse a date string using every supported format.

    Returns None when the value is empty or matches no supported format.
    Callers treat None as "unparseable" (e.g. INVALID_FORMAT anomaly).
    """
    if not value:
        return None

    text = str(value).strip()
    if not text:
        return None

    # Tolerate full ISO 8601 timestamps by taking the date component.
    if "T" in text:
        text = text.split("T", 1)[0]

    for fmt in SUPPORTED_DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def is_expired(value: Optional[str], today: Optional[date] = None) -> bool:
    """
    True when the value is a parseable date strictly before today.

    Unparseable or missing values are NOT expired — that is a separate concern
    (INVALID_FORMAT / MISSING_REQUIRED_FIELD), and conflating them would let a
    typo silently look like an expiry.
    """
    parsed = parse_date(value)
    if parsed is None:
        return False
    reference = today or date.today()
    return parsed < reference


def expires_within(
    value: Optional[str],
    days: int,
    today: Optional[date] = None,
) -> bool:
    """
    True when the value is a parseable date falling between today and today + days
    (inclusive). Already-expired dates return False — use is_expired() for those,
    so "expiring soon" (YELLOW) and "expired" (RED) stay distinguishable.
    """
    parsed = parse_date(value)
    if parsed is None:
        return False
    reference = today or date.today()
    return reference <= parsed <= reference + timedelta(days=days)


def years_from_now(value: Optional[str], today: Optional[date] = None) -> Optional[float]:
    """
    Approximate signed year offset of a date from today.

    Positive = future. Returns None when unparseable.
    """
    parsed = parse_date(value)
    if parsed is None:
        return None
    reference = today or date.today()
    return (parsed - reference).days / 365.0
