from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.components.navigation import Sidebar
from ui.pages.customer_page import CustomerPage
from ui.pages.dashboard_page import DashboardPage
from ui.stylesheets import get_global_stylesheet
from ui.theme import TEXT_SECONDARY, Spacing, Typography


def _placeholder_page(text: str) -> QWidget:
    w = QWidget()
    layout = QVBoxLayout(w)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl = QLabel(text)
    lbl.setProperty("class", "empty-title")
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(lbl)
    return w


class MainWindow(QMainWindow):
    def __init__(self, db_path: str):
        super().__init__()
        self.db_path = db_path
        self.setWindowTitle("API Health Tester")
        self.setMinimumSize(1280, 800)
        self.setStyleSheet(get_global_stylesheet())
        self._build()
        self._connect_signals()

    def _build(self) -> None:
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._sidebar = Sidebar(self.db_path)

        self._stack = QStackedWidget()
        self._dashboard = DashboardPage(self.db_path)
        self._customer_page = CustomerPage(self.db_path)

        self._stack.addWidget(self._dashboard)         # 0
        self._stack.addWidget(self._customer_page)     # 1
        self._stack.addWidget(                         # 2
            _placeholder_page("Test Runner — Faz 3'te gelecek")
        )
        self._stack.addWidget(                         # 3
            _placeholder_page("Geçmiş — Faz 4'te gelecek")
        )

        root_layout.addWidget(self._sidebar)
        root_layout.addWidget(self._stack, 1)
        self.setCentralWidget(root)

        self._dashboard.refresh()

    def _connect_signals(self) -> None:
        self._sidebar.dashboard_requested.connect(self._show_dashboard)
        self._sidebar.history_requested.connect(lambda: self._stack.setCurrentIndex(3))
        self._sidebar.customer_selected.connect(self._on_customer_selected)
        self._sidebar.env_selected.connect(self._on_env_selected)
        self._sidebar.data_changed.connect(self._on_data_changed)

        self._dashboard.customer_selected.connect(self._on_customer_selected)
        self._customer_page.data_changed.connect(self._on_data_changed)

    def _show_dashboard(self) -> None:
        self._dashboard.refresh()
        self._stack.setCurrentIndex(0)

    def _on_customer_selected(self, customer_id: int) -> None:
        self._customer_page.load_customer(customer_id)
        self._stack.setCurrentIndex(1)

    def _on_env_selected(self, customer_id: int, env_type: str) -> None:
        self._customer_page.load_customer(customer_id, active_env=env_type)
        self._stack.setCurrentIndex(1)

    def _on_data_changed(self) -> None:
        self._sidebar.refresh()
        self._dashboard.refresh()
