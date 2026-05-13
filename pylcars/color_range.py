"""Utility: map a numeric value to a colour via a threshold list."""
from __future__ import annotations


def color_for_value(value: float, ranges: list, default: str) -> str:
    """Return a colour string based on where *value* falls in *ranges*.

    Each element of *ranges* is a ``(key, color)`` pair where *key* is either:

    * A number — the **lower bound** of this colour's interval.  The upper
      bound is the lower bound of the next entry, or +∞ for the last entry.
    * A ``(lo, hi)`` sequence — an explicit half-open interval ``[lo, hi)``.

    Entries must be in increasing order and must not overlap.  Values that
    fall below the first lower bound return *default*.

    Example::

        color_for_value(15, [(10, Colors.yellow), (20, Colors.orange), (30, Colors.rot)], Colors.blaugrau)
        # 10 <= 15 < 20  →  Colors.yellow
    """
    if not ranges:
        return default

    intervals: list[tuple[float, float, str]] = []
    for i, (key, color) in enumerate(ranges):
        if hasattr(key, "__len__"):
            lo, hi = float(key[0]), float(key[1])
        else:
            lo = float(key)
            if i + 1 < len(ranges):
                next_key = ranges[i + 1][0]
                hi = float(next_key[0]) if hasattr(next_key, "__len__") else float(next_key)
            else:
                hi = float("inf")
        intervals.append((lo, hi, color))

    for lo, hi, color in intervals:
        if lo <= value < hi:
            return color

    return default
