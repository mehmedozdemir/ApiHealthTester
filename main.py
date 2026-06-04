import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication

load_dotenv()

from core.database import init_db
from ui.main_window import MainWindow

DB_PATH = os.getenv("DB_PATH", "./data/health_tester.db")


def main() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    init_db(DB_PATH)

    app = QApplication(sys.argv)
    app.setApplicationName("API Health Tester")

    window = MainWindow(DB_PATH)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
