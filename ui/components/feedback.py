from PySide6.QtCore import QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from ui.theme import (
    ACCENT_MUTED,
    ERROR,
    ERROR_MUTED,
    INFO,
    SUCCESS,
    SUCCESS_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING,
    WARNING_MUTED,
    Radius,
    Spacing,
    Typography,
)

_LEVEL_COLORS = {
    "success": (SUCCESS, SUCCESS_MUTED),
    "error": (ERROR, ERROR_MUTED),
    "warning": (WARNING, WARNING_MUTED),
    "info": (INFO, ACCENT_MUTED),
}
_LEVEL_ICONS = {
    "success": "✓",
    "error": "✕",
    "warning": "⚠",
    "info": "ℹ",
}


class Toast(QFrame):
    def __init__(self, message: str, level: str = "info", parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        text_color, bg_color = _LEVEL_COLORS.get(level, _LEVEL_COLORS["info"])
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {text_color};
                border-radius: {Radius.MD}px;
            }}
        """)
        self.setFixedWidth(320)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.SM, Spacing.SM)
        layout.setSpacing(Spacing.SM)

        icon = QLabel(_LEVEL_ICONS.get(level, "ℹ"))
        icon.setStyleSheet(f"color: {text_color}; font-size: {Typography.SIZE_LG}px;")

        msg = QLabel(message)
        msg.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: {Typography.SIZE_MD}px;")
        msg.setWordWrap(True)

        close = QPushButton("×")
        close.setFixedSize(24, 24)
        close.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_SECONDARY};
                border: none;
                font-size: 18px;
                font-weight: bold;
                padding: 0;
            }}
            QPushButton:hover {{ color: {TEXT_PRIMARY}; }}
        """)
        close.clicked.connect(self.deleteLater)

        layout.addWidget(icon)
        layout.addWidget(msg, 1)
        layout.addWidget(close)

    def show(self) -> None:
        self.adjustSize()
        if self.parent():
            p = self.parent()
            self.move(
                p.width() - self.width() - Spacing.LG,
                p.height() - self.height() - Spacing.LG,
            )
        super().show()
        self.raise_()
        QTimer.singleShot(4000, self._dismiss)

    def _dismiss(self) -> None:
        if not self.isVisible():
            return
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(300)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.finished.connect(self.deleteLater)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    @staticmethod
    def show_message(parent: QWidget, message: str, level: str = "info") -> None:
        Toast(message, level, parent).show()


class Spinner(QWidget):
    def __init__(self, size: int = 28, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def _tick(self) -> None:
        self._angle = (self._angle + 8) % 360
        self.update()

    def paintEvent(self, _) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        size = self.width()
        pad = 3
        rect_size = size - pad * 2
        from PySide6.QtCore import QRectF
        rect = QRectF(pad, pad, rect_size, rect_size)
        pen = QPen(QColor("#5B8AF0"))
        pen.setWidth(3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, self._angle * 16, 270 * 16)

    def stop(self) -> None:
        self._timer.stop()
