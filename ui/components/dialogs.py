from typing import Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.models import ApiCollection, Customer, Environment
from ui.components.buttons import DangerButton, PrimaryButton, SecondaryButton
from ui.components.inputs import StyledComboBox, StyledLineEdit
from ui.theme import (
    ACCENT,
    BG_ELEVATED,
    BG_SURFACE,
    BORDER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    Radius,
    Spacing,
    Typography,
)


def _make_separator() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    return line


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color: {TEXT_SECONDARY};"
        f"font-size: {Typography.SIZE_SM}px;"
        f"font-weight: {Typography.WEIGHT_SEMIBOLD};"
    )
    return lbl


class ConfirmDialog(QDialog):
    def __init__(self, title: str, message: str, danger: bool = False, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setModal(True)
        self._build(message, danger)

    def _build(self, message: str, danger: bool) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        msg = QLabel(message)
        msg.setWordWrap(True)
        msg.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: {Typography.SIZE_MD}px;")
        layout.addWidget(msg)

        layout.addSpacing(Spacing.SM)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel = SecondaryButton("İptal")
        cancel.clicked.connect(self.reject)

        confirm = DangerButton("Sil") if danger else PrimaryButton("Onayla")
        confirm.clicked.connect(self.accept)

        btn_row.addWidget(cancel)
        btn_row.addSpacing(Spacing.SM)
        btn_row.addWidget(confirm)
        layout.addLayout(btn_row)


class CustomerDialog(QDialog):
    """Add or edit a customer. Pass `customer` to pre-fill for editing."""

    def __init__(self, customer: Optional[Customer] = None, parent=None):
        super().__init__(parent)
        self._editing = customer is not None
        self.setWindowTitle("Müşteriyi Düzenle" if self._editing else "Müşteri Ekle")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._color = customer.color if customer else "#5B8AF0"
        self._build(customer)

    def _build(self, customer: Optional[Customer]) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        form = QFormLayout()
        form.setSpacing(Spacing.SM)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._name_input = StyledLineEdit("Müşteri adı")
        if customer:
            self._name_input.setText(customer.name)

        form.addRow(_section_label("Müşteri Adı *"), self._name_input)

        color_row = QHBoxLayout()
        self._color_preview = QLabel()
        self._color_preview.setFixedSize(36, 36)
        self._update_color_preview()

        color_btn = SecondaryButton("Renk Seç")
        color_btn.clicked.connect(self._pick_color)

        color_row.addWidget(self._color_preview)
        color_row.addSpacing(Spacing.SM)
        color_row.addWidget(color_btn)
        color_row.addStretch()

        color_widget = QWidget()
        color_widget.setLayout(color_row)
        form.addRow(_section_label("Renk"), color_widget)

        layout.addLayout(form)
        layout.addSpacing(Spacing.SM)
        layout.addWidget(_make_separator())
        layout.addSpacing(Spacing.SM)

        self._error_label = QLabel()
        self._error_label.setStyleSheet(f"color: #E05C6A; font-size: {Typography.SIZE_SM}px;")
        self._error_label.hide()
        layout.addWidget(self._error_label)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel = SecondaryButton("İptal")
        cancel.clicked.connect(self.reject)

        save = PrimaryButton("Kaydet")
        save.clicked.connect(self._on_save)

        btn_row.addWidget(cancel)
        btn_row.addSpacing(Spacing.SM)
        btn_row.addWidget(save)
        layout.addLayout(btn_row)

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(QColor(self._color), self, "Renk Seç")
        if color.isValid():
            self._color = color.name()
            self._update_color_preview()

    def _update_color_preview(self) -> None:
        self._color_preview.setStyleSheet(
            f"background-color: {self._color};"
            f"border-radius: {Radius.SM}px;"
            f"border: 1px solid {BORDER};"
        )

    def _on_save(self) -> None:
        name = self._name_input.text().strip()
        if not name:
            self._name_input.set_error(True)
            self._error_label.setText("Müşteri adı boş bırakılamaz.")
            self._error_label.show()
            return
        self.accept()

    def result_data(self) -> Tuple[str, str]:
        return self._name_input.text().strip(), self._color


class EditEnvironmentDialog(QDialog):
    def __init__(self, environment: Environment, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ortam Düzenle")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build(environment)

    def _build(self, env: Environment) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        form = QFormLayout()
        form.setSpacing(Spacing.SM)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._url_input = StyledLineEdit("https://api.example.com")
        self._url_input.setText(env.base_url)
        form.addRow(_section_label("Base URL"), self._url_input)

        self._auth_combo = StyledComboBox()
        self._auth_combo.addItem("Kimlik doğrulama yok", "none")
        self._auth_combo.addItem("Bearer Token", "bearer")
        self._auth_combo.addItem("API Key", "api_key")
        idx = {"none": 0, "bearer": 1, "api_key": 2}.get(env.auth_type, 0)
        self._auth_combo.setCurrentIndex(idx)
        self._auth_combo.currentIndexChanged.connect(self._on_auth_changed)
        form.addRow(_section_label("Kimlik Doğrulama"), self._auth_combo)

        self._token_label = _section_label("Token / Değer")
        self._token_input = StyledLineEdit("Token veya anahtar değeri")
        self._token_input.setText(env.auth_value)
        form.addRow(self._token_label, self._token_input)

        self._header_label = _section_label("Header Adı")
        self._header_input = StyledLineEdit("X-Api-Key")
        self._header_input.setText(env.auth_header_name)
        form.addRow(self._header_label, self._header_input)

        layout.addLayout(form)
        layout.addSpacing(Spacing.SM)
        layout.addWidget(_make_separator())
        layout.addSpacing(Spacing.SM)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = SecondaryButton("İptal")
        cancel.clicked.connect(self.reject)
        save = PrimaryButton("Kaydet")
        save.clicked.connect(self.accept)
        btn_row.addWidget(cancel)
        btn_row.addSpacing(Spacing.SM)
        btn_row.addWidget(save)
        layout.addLayout(btn_row)

        self._on_auth_changed()

    def _on_auth_changed(self) -> None:
        auth_type = self._auth_combo.currentData()
        is_none = auth_type == "none"
        is_api_key = auth_type == "api_key"

        self._token_label.setVisible(not is_none)
        self._token_input.setVisible(not is_none)
        self._header_label.setVisible(is_api_key)
        self._header_input.setVisible(is_api_key)

    def result_data(self) -> Tuple[str, str, str, str]:
        return (
            self._url_input.text().strip(),
            self._auth_combo.currentData(),
            self._token_input.text().strip(),
            self._header_input.text().strip() or "X-Api-Key",
        )


class AddApiCollectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Koleksiyonu Ekle")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        form = QFormLayout()
        form.setSpacing(Spacing.SM)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._name_input = StyledLineEdit("UserService, OrderService…")
        form.addRow(_section_label("Koleksiyon Adı *"), self._name_input)

        self._source_combo = StyledComboBox()
        self._source_combo.addItem("URL", "url")
        self._source_combo.addItem("Dosya", "file")
        self._source_combo.currentIndexChanged.connect(self._on_source_changed)
        form.addRow(_section_label("Swagger Kaynağı"), self._source_combo)

        self._url_input = StyledLineEdit("https://api.example.com/swagger.json")
        form.addRow(_section_label("Swagger URL *"), self._url_input)

        file_row = QHBoxLayout()
        self._file_input = StyledLineEdit("Dosya seçin…")
        self._file_input.setReadOnly(True)
        file_btn = SecondaryButton("Gözat")
        file_btn.clicked.connect(self._browse_file)
        file_row.addWidget(self._file_input, 1)
        file_row.addWidget(file_btn)
        file_widget = QWidget()
        file_widget.setLayout(file_row)

        self._file_label = _section_label("Swagger Dosyası *")
        form.addRow(self._file_label, file_widget)

        layout.addLayout(form)

        self._error_label = QLabel()
        self._error_label.setStyleSheet(f"color: #E05C6A; font-size: {Typography.SIZE_SM}px;")
        self._error_label.hide()
        layout.addWidget(self._error_label)

        layout.addSpacing(Spacing.SM)
        layout.addWidget(_make_separator())
        layout.addSpacing(Spacing.SM)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = SecondaryButton("İptal")
        cancel.clicked.connect(self.reject)
        save = PrimaryButton("Ekle")
        save.clicked.connect(self._on_save)
        btn_row.addWidget(cancel)
        btn_row.addSpacing(Spacing.SM)
        btn_row.addWidget(save)
        layout.addLayout(btn_row)

        self._on_source_changed()

    def _on_source_changed(self) -> None:
        is_url = self._source_combo.currentData() == "url"
        self._url_input.setVisible(is_url)
        self._file_label.setVisible(not is_url)
        # file_widget is the widget at the same form row
        # find it by parent traversal - simpler: store reference
        self._file_input.parentWidget().setVisible(not is_url)

    def _browse_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Swagger Dosyası Seç", "",
            "OpenAPI Files (*.json *.yaml *.yml);;All Files (*)"
        )
        if path:
            self._file_input.setText(path)

    def _on_save(self) -> None:
        name = self._name_input.text().strip()
        source_type = self._source_combo.currentData()
        source = (
            self._url_input.text().strip()
            if source_type == "url"
            else self._file_input.text().strip()
        )
        if not name:
            self._name_input.set_error(True)
            self._error_label.setText("Koleksiyon adı boş bırakılamaz.")
            self._error_label.show()
            return
        if not source:
            self._error_label.setText("Swagger kaynağı boş bırakılamaz.")
            self._error_label.show()
            return
        self.accept()

    def result_data(self) -> Tuple[str, str, str]:
        source_type = self._source_combo.currentData()
        source = (
            self._url_input.text().strip()
            if source_type == "url"
            else self._file_input.text().strip()
        )
        return self._name_input.text().strip(), source_type, source
