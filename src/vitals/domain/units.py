"""The units of the values that vitals reads, one NewType each."""

from typing import NewType

Percent = NewType("Percent", float)
"""A share from 0 to 100."""

Celsius = NewType("Celsius", float)
"""A temperature in degrees Celsius."""

Bytes = NewType("Bytes", int)
"""An amount of memory or storage in bytes."""

Watts = NewType("Watts", float)
"""A power draw in watts."""

Megahertz = NewType("Megahertz", float)
"""A clock frequency in megahertz."""

Seconds = NewType("Seconds", float)
"""A duration in seconds."""


def percent_of(part: Bytes, whole: Bytes) -> Percent:
    """Return the share of `part` in `whole`, and 0 for an empty whole."""
    if whole <= 0:
        return Percent(0.0)
    return Percent(100.0 * part / whole)
