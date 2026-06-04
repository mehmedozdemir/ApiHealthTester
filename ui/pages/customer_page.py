from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.models import Customer, Environment
from core.session_store import (
    ApiCollectionStore,
    CustomerStore,
    EnvironmentStore,
)
from ui.components.buttons import DangerButton, PrimaryButton, SecondaryButton
from ui.components.dialogs import (
    AddApiCollectionDialog,
    ConfirmDialog,
    CustomerDialog,
    EditEnvironmentDialog,
)
from ui.components.feedback import Toast
from ui.theme import (
    ACCENT,
    TEXT_DISABLED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    Spacing,
    Typography,
)

_ENV_ORDER = ["PROD", "TEST", "DEV"]


def _info_row(label: str, value: str) -> QWidget:
    w = QWidget()
    layout = QHBoxLayout(w)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(Spacing.SM)
    lbl = QLabel(f"{label}:")
    lbl.setStyleSheet(
        f"color: {TEXT_SECONDARY};"
        f"font-size: {Typography.SIZE_SM}px;"
        f"min-width: 120px;"
    )
    lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    val = QLabel(value or "—")
    val.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: {Typography.SIZE_SM}px;")
    val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    layout.addWidget(lbl)
    layout.addWidget(val, 1)
    return w


def _separator() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    return line


class _CollectionRow(QFrame):
    delete_requested = Signal(int)

    def __init__(self, collection_id: int, name: str, swagger_source: str, parent=None):
        super().__init__(parent)
        self._id = collection_id
        self.setProperty("class", "card")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.SM, Spacing.SM)
        layout.setSpacing(Spacing.SM)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(
            f"font-size: {Typography.SIZE_MD}px;"
            f"font-weight: {Typography.WEIGHT_SEMIBOLD};"
            f"color: {TEXT_PRIMARY};"
        )
        source_lbl = QLabel(swagger_source)
        source_lbl.setStyleSheet(
            f"font-size: {Typography.SIZE_SM}px; color: {TEXT_SECONDARY};"
        )
        source_lbl.setToolTip(swagger_source)

        info = QVBoxLayout()
        info.setSpacing(2)
        info.addWidget(name_lbl)
        info.addWidget(source_lbl)

        test_btn = SecondaryButton("▶  Test Et")
        test_btn.setEnabled(False)
        test_btn.setToolTip("Faz 3'te aktif olacak")

        del_btn = DangerButton("Sil")
        del_btn.setFixedWidth(60)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self._id))

        layout.addLayout(info, 1)
        layout.addWidget(test_btn)
        layout.addWidget(del_btn)


class _EnvTab(QWidget):
    """Tab content for a single environment (PROD/TEST/DEV)."""

    data_changed = Signal()

    def __init__(
        self,
        db_path: str,
        customer: Customer,
        env: Optional[Environment],
        env_type: str,
        parent=None,
    ):
        super().__init__(parent)
        self.db_path = db_path
        self._customer = customer
        self._env = env
        self._env_type = env_type

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._inner = QWidget()
        outer.addWidget(self._inner, 1)

        self._populate()

    # ------------------------------------------------------------------
    def _populate(self) -> None:
        new = self._make_content()
        self.layout().replaceWidget(self._inner, new)
        self._inner.deleteLater()
        self._inner = new

    def _make_content(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        if self._env is None:
            layout.addWidget(self._make_unconfigured())
            btn_row = QHBoxLayout()
            btn_row.addStretch()
            configure_btn = PrimaryButton(f"  {self._env_type} Ortamını Yapılandır")
            configure_btn.clicked.connect(self._on_configure)
            btn_row.addWidget(configure_btn)
            btn_row.addStretch()
            layout.addLayout(btn_row)
            layout.addStretch()
            return w

        layout.addWidget(self._build_env_info_card())
        layout.addWidget(_separator())
        layout.addWidget(self._build_collections_section())
        layout.addStretch()
        return w

    def _make_unconfigured(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(Spacing.SM)
        icon = QLabel("🔧")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 36px;")
        title = QLabel(f"{self._env_type} ortamı henüz yapılandırılmadı")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setProperty("class", "empty-title")
        layout.addWidget(icon)
        layout.addWidget(title)
        return w

    def _build_env_info_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.XS)

        header = QHBoxLayout()
        lbl = QLabel("Ortam Bilgisi")
        lbl.setProperty("class", "section-header")
        edit_btn = SecondaryButton("Düzenle")
        edit_btn.setFixedWidth(80)
        edit_btn.clicked.connect(self._on_edit_env)
        header.addWidget(lbl)
        header.addStretch()
        header.addWidget(edit_btn)
        layout.addLayout(header)

        auth_display = {
            "none": "Yok",
            "bearer": "Bearer Token",
            "api_key": "API Key",
        }.get(self._env.auth_type, self._env.auth_type)

        masked = self._env.auth_value[:4] + "••••" if self._env.auth_value else "—"

        layout.addWidget(_info_row("Base URL", self._env.base_url or "—"))
        layout.addWidget(_info_row("Kimlik Doğrulama", auth_display))
        if self._env.auth_type != "none":
            layout.addWidget(_info_row("Token / Key", masked))
        if self._env.auth_type == "api_key":
            layout.addWidget(_info_row("Header Adı", self._env.auth_header_name))
        return card

    def _build_collections_section(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.SM)

        header = QHBoxLayout()
        lbl = QLabel("API Koleksiyonları")
        lbl.setProperty("class", "section-header")
        add_btn = PrimaryButton("+ Ekle")
        add_btn.setFixedWidth(80)
        add_btn.clicked.connect(self._on_add_collection)
        header.addWidget(lbl)
        header.addStretch()
        header.addWidget(add_btn)
        layout.addLayout(header)

        self._cols_layout = QVBoxLayout()
        self._cols_layout.setSpacing(Spacing.SM)
        layout.addLayout(self._cols_layout)
        self._refresh_collections()
        return w

    def _refresh_collections(self) -> None:
        while self._cols_layout.count():
            item = self._cols_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cols = ApiCollectionStore(self.db_path).get_by_environment(self._env.id)
        if not cols:
            empty = QLabel("Henüz API koleksiyonu eklenmedi.")
            empty.setStyleSheet(
                f"color: {TEXT_DISABLED}; font-size: {Typography.SIZE_SM}px;"
            )
            self._cols_layout.addWidget(empty)
            return

        for col in cols:
            row = _CollectionRow(col.id, col.name, col.swagger_source)
            row.delete_requested.connect(self._on_delete_collection)
            self._cols_layout.addWidget(row)

    # ------------------------------------------------------------------
    def _on_configure(self) -> None:
        self._env = EnvironmentStore(self.db_path).create(
            self._customer.id, self._env_type
        )
        self._populate()
        self.data_changed.emit()

    def _on_edit_env(self) -> None:
        dialog = EditEnvironmentDialog(self._env, parent=self)
        if dialog.exec() == EditEnvironmentDialog.DialogCode.Accepted:
            url, auth_type, auth_value, header_name = dialog.result_data()
            self._env = EnvironmentStore(self.db_path).update(
                self._env.id, url, auth_type, auth_value, header_name
            )
            self._populate()
            self.data_changed.emit()
            Toast.show_message(self.window(), "Ortam bilgisi güncellendi.", "success")

    def _on_add_collection(self) -> None:
        dialog = AddApiCollectionDialog(parent=self)
        if dialog.exec() == AddApiCollectionDialog.DialogCode.Accepted:
            name, source_type, source = dialog.result_data()
            ApiCollectionStore(self.db_path).create(
                self._env.id, name, source_type, source
            )
            self._refresh_collections()
            self.data_changed.emit()
            Toast.show_message(self.window(), f'"{name}" eklendi.', "success")

    def _on_delete_collection(self, collection_id: int) -> None:
        dialog = ConfirmDialog(
            "Koleksiyonu Sil",
            "Bu API koleksiyonunu silmek istediğinize emin misiniz?",
            danger=True, parent=self,
        )
        if dialog.exec() == ConfirmDialog.DialogCode.Accepted:
            ApiCollectionStore(self.db_path).delete(collection_id)
            self._refresh_collections()
            self.data_changed.emit()
            Toast.show_message(self.window(), "Koleksiyon silindi.", "info")


# ======================================================================

class CustomerPage(QWidget):
    data_changed = Signal()

    def __init__(self, db_path: str, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self._customer: Optional[Customer] = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._inner = self._make_empty_widget()
        outer.addWidget(self._inner, 1)

    # ------------------------------------------------------------------
    def _swap(self, new_widget: QWidget) -> None:
        self.layout().replaceWidget(self._inner, new_widget)
        self._inner.deleteLater()
        self._inner = new_widget

    def _make_empty_widget(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel("Sol panelden bir müşteri seçin.")
        lbl.setProperty("class", "empty-title")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        return w

    def _make_customer_widget(self, active_env: str) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.LG)
        layout.addWidget(self._build_header())
        layout.addWidget(self._build_tabs(active_env), 1)
        return w

    # ------------------------------------------------------------------
    def load_customer(self, customer_id: int, active_env: str = "PROD") -> None:
        self._customer = CustomerStore(self.db_path).get_by_id(customer_id)
        if not self._customer:
            return
        self._swap(self._make_customer_widget(active_env))

    def _build_header(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {self._customer.color}; font-size: 14px;")

        title = QLabel(self._customer.name)
        title.setProperty("class", "page-title")

        edit_btn = SecondaryButton("Düzenle")
        edit_btn.clicked.connect(self._on_edit_customer)

        del_btn = DangerButton("Müşteriyi Sil")
        del_btn.clicked.connect(self._on_delete_customer)

        layout.addWidget(dot)
        layout.addSpacing(Spacing.SM)
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(edit_btn)
        layout.addSpacing(Spacing.SM)
        layout.addWidget(del_btn)
        return w

    def _build_tabs(self, active_env: str) -> QTabWidget:
        tabs = QTabWidget()
        envs = {
            e.env_type: e
            for e in EnvironmentStore(self.db_path).get_by_customer(self._customer.id)
        }
        tab_indices = {"PROD": 0, "TEST": 1, "DEV": 2}
        for env_type in _ENV_ORDER:
            label = f"★ {env_type}" if env_type == "PROD" else env_type
            tab = _EnvTab(
                self.db_path, self._customer, envs.get(env_type), env_type
            )
            tab.data_changed.connect(self.data_changed)
            tabs.addTab(tab, label)
        tabs.setCurrentIndex(tab_indices.get(active_env, 0))
        return tabs

    # ------------------------------------------------------------------
    def _on_edit_customer(self) -> None:
        dialog = CustomerDialog(self._customer, parent=self)
        if dialog.exec() == CustomerDialog.DialogCode.Accepted:
            name, color = dialog.result_data()
            CustomerStore(self.db_path).update(self._customer.id, name, color)
            self._customer = CustomerStore(self.db_path).get_by_id(self._customer.id)
            self._swap(self._make_customer_widget("PROD"))
            self.data_changed.emit()
            Toast.show_message(self.window(), "Müşteri güncellendi.", "success")

    def _on_delete_customer(self) -> None:
        dialog = ConfirmDialog(
            "Müşteriyi Sil",
            f'"{self._customer.name}" müşterisini ve tüm verilerini silmek istiyor musunuz?',
            danger=True, parent=self,
        )
        if dialog.exec() == ConfirmDialog.DialogCode.Accepted:
            CustomerStore(self.db_path).delete(self._customer.id)
            self._customer = None
            self.data_changed.emit()
            self._swap(self._make_empty_widget())
