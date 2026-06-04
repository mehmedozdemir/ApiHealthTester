from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.session_store import CustomerStore, EnvironmentStore, TestSessionStore
from ui.components.buttons import PrimaryButton
from ui.theme import (
    ACCENT,
    BG_ELEVATED,
    BG_SURFACE,
    BORDER,
    ERROR,
    SUCCESS,
    TEXT_DISABLED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING,
    Radius,
    Spacing,
    Typography,
)


def _status_color(success_count: int, total_count: int) -> str:
    if total_count == 0:
        return TEXT_DISABLED
    ratio = success_count / total_count
    if ratio == 1.0:
        return SUCCESS
    if ratio >= 0.5:
        return WARNING
    return ERROR


class _CustomerCard(QFrame):
    clicked = Signal(int)

    def __init__(self, customer_id: int, name: str, color: str,
                 prod_status: str, parent=None):
        super().__init__(parent)
        self._customer_id = customer_id
        self.setProperty("class", "card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._build(name, color, prod_status)

    def _build(self, name: str, color: str, prod_status: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        header = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color}; font-size: 10px;")
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(
            f"font-size: {Typography.SIZE_LG}px;"
            f"font-weight: {Typography.WEIGHT_SEMIBOLD};"
            f"color: {TEXT_PRIMARY};"
        )
        header.addWidget(dot)
        header.addSpacing(Spacing.XS)
        header.addWidget(name_lbl)
        header.addStretch()
        layout.addLayout(header)

        prod_row = QHBoxLayout()
        prod_lbl = QLabel("PROD ★")
        prod_lbl.setStyleSheet(
            f"font-size: {Typography.SIZE_SM}px;"
            f"font-weight: {Typography.WEIGHT_BOLD};"
            f"color: {ACCENT};"
        )
        status_lbl = QLabel(prod_status)
        status_lbl.setStyleSheet(
            f"font-size: {Typography.SIZE_SM}px;"
            f"color: {TEXT_SECONDARY};"
        )
        prod_row.addWidget(prod_lbl)
        prod_row.addSpacing(Spacing.SM)
        prod_row.addWidget(status_lbl)
        prod_row.addStretch()
        layout.addLayout(prod_row)
        layout.addStretch()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._customer_id)
        super().mousePressEvent(event)


def _empty_state() -> QWidget:
    w = QWidget()
    layout = QVBoxLayout(w)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.setSpacing(Spacing.SM)

    icon = QLabel("📭")
    icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon.setStyleSheet("font-size: 48px;")

    title = QLabel("Henüz müşteri eklenmedi")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title.setProperty("class", "empty-title")

    subtitle = QLabel('Sol paneldeki "+ Müşteri Ekle" butonunu kullanın.')
    subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
    subtitle.setWordWrap(True)
    subtitle.setProperty("class", "empty-subtitle")

    layout.addWidget(icon)
    layout.addWidget(title)
    layout.addWidget(subtitle)
    return w


class DashboardPage(QWidget):
    customer_selected = Signal(int)

    def __init__(self, db_path: str, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.LG)
        layout.addWidget(self._build_header())
        layout.addWidget(self._build_content_area(), 1)

    def _build_header(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Genel Durum")
        title.setProperty("class", "page-title")

        self._run_all_btn = PrimaryButton("▶  Tüm PROD'ları Çalıştır")
        self._run_all_btn.setEnabled(False)

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self._run_all_btn)
        return w

    def _build_content_area(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._cards_container = QWidget()
        self._cards_layout = QGridLayout(self._cards_container)
        self._cards_layout.setSpacing(Spacing.MD)
        self._cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(self._cards_container)
        return scroll

    def refresh(self) -> None:
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        c_store = CustomerStore(self.db_path)
        e_store = EnvironmentStore(self.db_path)
        session_store = TestSessionStore(self.db_path)

        customers = c_store.get_all()
        if not customers:
            self._cards_layout.addWidget(_empty_state(), 0, 0)
            return

        for i, customer in enumerate(customers):
            prod_status = self._get_prod_status(customer.id, e_store, session_store)
            card = _CustomerCard(customer.id, customer.name, customer.color, prod_status)
            card.clicked.connect(self.customer_selected)
            self._cards_layout.addWidget(card, i // 4, i % 4)

    def _get_prod_status(self, customer_id: int, e_store, session_store) -> str:
        envs = {e.env_type: e for e in e_store.get_by_customer(customer_id)}
        prod = envs.get("PROD")
        if prod is None:
            return "PROD yapılandırılmadı"
        session = session_store.get_latest(prod.id) if False else None
        # session_store.get_latest expects api_collection_id, not env_id
        # will be populated properly in Faz 3 when tests run
        return "Test bekleniyor"

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh()
