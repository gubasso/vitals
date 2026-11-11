"""The log of vitals: one file under the XDG state folder, never the screen."""

import logging
lazy from pathlib import Path

from platformdirs import user_state_path

LOGGER = logging.getLogger("vitals")


def log_path() -> Path:
    """Return `${XDG_STATE_HOME:-$HOME/.local/state}/vitals/vitals.log`."""
    return user_state_path("vitals") / "vitals.log"


def configure_logging() -> Path:
    """Send the records of vitals to the log file alone, and return its path."""
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    for old in list(LOGGER.handlers):
        LOGGER.removeHandler(old)
        old.close()
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)
    # The app owns the screen, so no record reaches the handlers of the root logger.
    LOGGER.propagate = False
    return path
