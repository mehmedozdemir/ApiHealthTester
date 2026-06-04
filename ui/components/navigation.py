from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.session_store import ApiCollectionStore, CustomerStore, EnvironmentStore
from ui.components.buttons import PrimaryButton, SecondaryButton
from ui.components.dialogs import ConfirmDialog, CustomerDialog
from ui.theme import (
    ACCENT,
    BG_SURFACE,
    BORDER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    Spacing,
    Typography,
)

_ROLE_TYPE = Qt.ItemDataRole.UserRole
_ROLE_ID = Qt.ItemDataRole.UserRole + 1
_ROLE_ENV_TYPE = Qt.ItemDataRole.UserRole + 2

_NODE_CUSTOMER = "customer"
_NODE_ENV = "env"
_NODE_COLLECTION = "collection"

_ENV_ORDER = ["PROD", "TEST", "DEV"]


def _color_icon(hex_color: str, size: int = 10) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(hex_color))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, size, size)
    painter.end()
    return QIcon(pixmap)


class Sidebar(QWidget):
    dashboard_requested = Signal()
    history_requested = Signal()
    customer_selected = Signal(int)
    env_selected = Signal(int, str)
    api_collection_selected = Signal(int, int)  # (api_collection_id, environment_id)
    data_changed = Signal()

    def __init__(self, db_path: str, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.setFixedWidth(240)
        self.setObjectName("sidebar")
        self.setStyleSheet(f"QWidget#sidebar {{ background-color: {BG_SURFACE}; }}")
        self._build()
        self._connect_signals()
        self.refresh()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_header())
        layout.addWidget(self._build_nav_buttons())
        layout.addWidget(self._build_separator())
        layout.addWidget(self._build_tree_section(), 1)
        layout.addWidget(self._build_separator())
        layout.addWidget(self._build_footer())

    def _build_header(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background-color: {BG_SURFACE};")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(Spacing.MD, Spacing.LG, Spacing.MD, Spacing.MD)

        icon = QLabel("⚡")
        icon.setStyleSheet(f"font-size: 20px; color: {ACCENT};")

        title = QLabel("API Health Tester")
        title.setStyleSheet(
            f"font-size: {Typography.SIZE_MD}px;"
            f"font-weight: {Typography.WEIGHT_BOLD};"
            f"color: {TEXT_PRIMARY};"
        )
        layout.addWidget(icon)
        layout.addSpacing(Spacing.SM)
        layout.addWidget(title)
        layout.addStretch()
        return w

    def _build_nav_buttons(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        layout.setSpacing(Spacing.XS)

        self._dashboard_btn = self._nav_btn("🏠  Dashboard")
        self._history_btn = self._nav_btn("📋  Geçmiş")

        layout.addWidget(self._dashboard_btn)
        layout.addWidget(self._history_btn)
        return w

    def _nav_btn(self, text: str) -> PrimaryButton:
        btn = PrimaryButton(text)
        btn.setProperty("variant", "ghost")
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        btn.setStyleSheet(btn.styleSheet() + f"""
            QPushButton {{
                text-align: left;
                padding-left: {Spacing.MD}px;
                font-size: {Typography.SIZE_MD}px;
                border-radius: {6}px;
            }}
        """)
        return btn

    def _build_separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {BORDER}; max-height: 1px; border: none;")
        return line

    def _build_tree_section(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        layout.setSpacing(Spacing.XS)

        customers_lbl = QLabel("MÜŞTERİLER")
        customers_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY};"
            f"font-size: {Typography.SIZE_XS}px;"
            f"font-weight: {Typography.WEIGHT_BOLD};"
            f"padding-left: {Spacing.SM}px;"
        )
        layout.addWidget(customers_lbl)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(16)
        self._tree.setAnimated(True)
        self._tree.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self._tree, 1)
        return w

    def _build_footer(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.MD)

        self._add_customer_btn = SecondaryButton("+ Müşteri Ekle")
        self._add_customer_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout.addWidget(self._add_customer_btn)
        return w

    def _connect_signals(self) -> None:
        self._dashboard_btn.clicked.connect(self.dashboard_requested)
        self._history_btn.clicked.connect(self.history_requested)
        self._add_customer_btn.clicked.connect(self._on_add_customer)
        self._tree.itemClicked.connect(self._on_item_clicked)

    def refresh(self) -> None:
        self._tree.clear()
        c_store = CustomerStore(self.db_path)
        e_store = EnvironmentStore(self.db_path)
        col_store = ApiCollectionStore(self.db_path)

        for customer in c_store.get_all():
            c_item = QTreeWidgetItem([customer.name])
            c_item.setIcon(0, _color_icon(customer.color))
            c_item.setData(0, _ROLE_TYPE, _NODE_CUSTOMER)
            c_item.setData(0, _ROLE_ID, customer.id)
            self._tree.addTopLevelItem(c_item)

            envs = {e.env_type: e for e in e_store.get_by_customer(customer.id)}
            for env_type in _ENV_ORDER:
                env = envs.get(env_type)
                if env is None:
                    continue
                label = f"★ {env_type}" if env_type == "PROD" else env_type
                e_item = QTreeWidgetItem(c_item, [label])
                if env_type == "PROD":
                    font = e_item.font(0)
                    font.setBold(True)
                    e_item.setFont(0, font)
                e_item.setData(0, _ROLE_TYPE, _NODE_ENV)
                e_item.setData(0, _ROLE_ID, env.id)
                e_item.setData(0, _ROLE_ENV_TYPE, env_type)
                e_item.setForeground(
                    0,
                    QColor(ACCENT) if env_type == "PROD" else QColor(TEXT_SECONDARY),
                )

                for col in col_store.get_by_environment(env.id):
                    col_item = QTreeWidgetItem(e_item, [f"  {col.name}"])
                    col_item.setData(0, _ROLE_TYPE, _NODE_COLLECTION)
                    col_item.setData(0, _ROLE_ID, col.id)
                    col_item.setData(0, _ROLE_ENV_TYPE, env.id)  # Environment ID'yi sakla
                    col_item.setForeground(0, QColor(TEXT_SECONDARY))

            c_item.setExpanded(True)

    def _on_item_clicked(self, item: QTreeWidgetItem, _column: int) -> None:
        node_type = item.data(0, _ROLE_TYPE)
        node_id = item.data(0, _ROLE_ID)

        if node_type == _NODE_CUSTOMER:
            self.customer_selected.emit(node_id)
        elif node_type == _NODE_ENV:
            env_type = item.data(0, _ROLE_ENV_TYPE)
            customer_id = item.parent().data(0, _ROLE_ID)
            self.env_selected.emit(customer_id, env_type)
        elif node_type == _NODE_COLLECTION:
            # API koleksiyonu seçildi — collection_id ve environment_id gönder
            environment_id = item.data(0, _ROLE_ENV_TYPE)
            self.api_collection_selected.emit(node_id, environment_id)

    def _on_add_customer(self) -> None:
        dialog = CustomerDialog(parent=self)
        if dialog.exec() == CustomerDialog.DialogCode.Accepted:
            name, color = dialog.result_data()
            CustomerStore(self.db_path).create(name, color)
            self.refresh()
            self.data_changed.emit()
