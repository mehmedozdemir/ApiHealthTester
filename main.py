import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

load_dotenv()

from core.database import init_db
from ui.theme import BG_BASE, BG_SURFACE, TEXT_PRIMARY, TEXT_SECONDARY, Typography

DB_PATH = os.getenv("DB_PATH", "./data/health_tester.db")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("API Health Tester")
        self.setMinimumSize(1280, 800)
        self._apply_base_style()
        self._build_placeholder()

    def _apply_base_style(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {BG_BASE};
                color: {TEXT_PRIMARY};
                font-family: {Typography.FONT_FAMILY};
                font-size: {Typography.SIZE_MD}px;
            }}
        """)

    def _build_placeholder(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        title = QLabel("API Health Tester")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"font-size: {Typography.SIZE_2XL}px;"
            f"font-weight: {Typography.WEIGHT_BOLD};"
            f"color: {TEXT_PRIMARY};"
        )

        subtitle = QLabel("Uygulama başlatılıyor…")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(
            f"font-size: {Typography.SIZE_MD}px;"
            f"color: {TEXT_SECONDARY};"
        )

        layout.addWidget(title)
        layout.addWidget(subtitle)
        self.setCentralWidget(container)


def main():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    init_db(DB_PATH)

    app = QApplication(sys.argv)
    app.setApplicationName("API Health Tester")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
