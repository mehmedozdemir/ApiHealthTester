from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton


def _refresh(btn: QPushButton) -> None:
    btn.style().unpolish(btn)
    btn.style().polish(btn)


class PrimaryButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setProperty("variant", "primary")
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class SecondaryButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setProperty("variant", "secondary")
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class DangerButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setProperty("variant", "danger")
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class IconButton(QPushButton):
    def __init__(self, label: str = "", tooltip: str = "", parent=None):
        super().__init__(label, parent)
        self.setProperty("variant", "ghost")
        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if tooltip:
            self.setToolTip(tooltip)
