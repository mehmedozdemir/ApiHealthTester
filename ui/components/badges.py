"""
Badge bileşenleri.
"""
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

from ui.theme import Colors


class StatusBadge(QLabel):
    """
    HTTP status code veya durum göstergesi badge.

    Renk kodları:
    - 2xx → SUCCESS
    - 3xx → INFO
    - 4xx → WARNING
    - 5xx → ERROR
    - Bağlantı hatası → ERROR, "ERR" yazar
    """

    def __init__(self, status_code: int = None, error: bool = False, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.update_status(status_code, error)

    def update_status(self, status_code: int = None, error: bool = False):
        """Badge durumunu günceller."""
        if error or status_code is None:
            # Bağlantı hatası
            self.setText("ERR")
            bg_color = Colors.ERROR
            text_color = Colors.TEXT_PRIMARY
        elif 200 <= status_code < 300:
            self.setText(str(status_code))
            bg_color = Colors.SUCCESS
            text_color = Colors.TEXT_PRIMARY
        elif 300 <= status_code < 400:
            self.setText(str(status_code))
            bg_color = Colors.ACCENT
            text_color = Colors.TEXT_PRIMARY
        elif 400 <= status_code < 500:
            self.setText(str(status_code))
            bg_color = Colors.WARNING
            text_color = Colors.BG_BASE
        else:  # 5xx
            self.setText(str(status_code))
            bg_color = Colors.ERROR
            text_color = Colors.TEXT_PRIMARY

        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                padding: 4px 12px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 12px;
                min-width: 40px;
            }}
        """)


class EnvironmentBadge(QLabel):
    """
    Ortam tipi badge (PROD/TEST/DEV).
    PROD kalın ve yıldızlı.
    """

    def __init__(self, env_type: str, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.set_env_type(env_type)

    def set_env_type(self, env_type: str):
        """Ortam tipine göre badge'i günceller."""
        if env_type == "PROD":
            self.setText("★ PROD")
            bg_color = Colors.ERROR
            text_color = Colors.TEXT_PRIMARY
            font_weight = "700"
        elif env_type == "TEST":
            self.setText("TEST")
            bg_color = Colors.WARNING
            text_color = Colors.BG_BASE
            font_weight = "600"
        else:  # DEV
            self.setText("DEV")
            bg_color = Colors.ACCENT
            text_color = Colors.TEXT_PRIMARY
            font_weight = "600"

        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: {font_weight};
                font-size: 13px;
            }}
        """)


class SuccessCountBadge(QLabel):
    """
    Başarı/toplam sayacı badge.
    Örnek: "8/10" (8 başarılı, 10 toplam)
    """

    def __init__(self, success_count: int = 0, total_count: int = 0, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.update_counts(success_count, total_count)

    def update_counts(self, success_count: int, total_count: int):
        """Sayaçları günceller."""
        self.setText(f"{success_count}/{total_count}")

        # Renk: tümü başarılı → yeşil, bazıları başarısız → turuncu, hiç başarılı yok → kırmızı
        if total_count == 0:
            bg_color = Colors.BG_ELEVATED
            text_color = Colors.TEXT_SECONDARY
        elif success_count == total_count:
            bg_color = Colors.SUCCESS
            text_color = Colors.TEXT_PRIMARY
        elif success_count > 0:
            bg_color = Colors.WARNING
            text_color = Colors.BG_BASE
        else:
            bg_color = Colors.ERROR
            text_color = Colors.TEXT_PRIMARY

        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                padding: 4px 12px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 12px;
                min-width: 50px;
            }}
        """)
