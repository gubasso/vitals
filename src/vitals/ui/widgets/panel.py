"""A titled panel that shows its values, or the failure of its source."""

from textual.containers import Vertical
from textual.widgets import Label

from vitals.ui.format import failure
lazy from vitals.domain.errors import CollectorError


class Panel(Vertical):
    """A container with a border title. A failed source replaces its body with the error."""

    def __init__(self, title: str, *, panel_id: str) -> None:
        """Create a panel with its border title."""
        super().__init__(id=panel_id, classes="panel")
        self.border_title = title

    def show_failure(self, error: CollectorError) -> None:
        """Hide the values, and show the error kind and its detail."""
        self.add_class("-failed")
        self.query_one(".panel-error", Label).update(failure(error))

    def show_values(self) -> None:
        """Show the values again after a failure."""
        self.remove_class("-failed")
