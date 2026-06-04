from PySide6.QtWidgets import QComboBox, QLineEdit, QTextEdit


class StyledLineEdit(QLineEdit):
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        if placeholder:
            self.setPlaceholderText(placeholder)
        self.setMinimumHeight(36)

    def set_error(self, has_error: bool) -> None:
        self.setProperty("error", "true" if has_error else "false")
        self.style().unpolish(self)
        self.style().polish(self)


class StyledTextEdit(QTextEdit):
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        if placeholder:
            self.setPlaceholderText(placeholder)


class StyledComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(36)
