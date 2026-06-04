"""
Test Runner sayfası.
API koleksiyonu için endpoint'leri listeler, test verisi üretir ve testleri çalıştırır.
"""
import asyncio
import logging
from typing import List, Dict, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QTextEdit, QLabel, QProgressBar, QHeaderView,
    QSplitter, QFrame
)
from PySide6.QtCore import Qt, Signal, QThread

from core.models import ApiCollection, Environment, EndpointDef, TestResult
from core.openapi_parser import parse_from_url, parse_from_file, OpenApiParseError
from core.test_generator import generate_test_data, generate_all
from core.test_runner import TestWorker, AuthConfig
from core.session_store import ApiCollectionStore, TestSessionStore, TestResultStore
from ui.theme import Colors, Spacing
from ui.components.buttons import PrimaryButton, SecondaryButton
from ui.components.badges import StatusBadge, EnvironmentBadge, SuccessCountBadge
from ui.components.feedback import Toast

logger = logging.getLogger(__name__)


class ParseWorker(QThread):
    """OpenAPI parse worker (async çalıştırmak için)."""
    finished = Signal(list)  # List[EndpointDef]
    error_occurred = Signal(str)

    def __init__(self, source_type: str, source: str):
        super().__init__()
        self.source_type = source_type
        self.source = source

    def run(self):
        try:
            if self.source_type == "url":
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                endpoints = loop.run_until_complete(parse_from_url(self.source))
                loop.close()
            else:  # file
                endpoints = parse_from_file(self.source)

            self.finished.emit(endpoints)
        except OpenApiParseError as e:
            self.error_occurred.emit(str(e))
        except Exception as e:
            logger.exception("Parse worker hatası")
            self.error_occurred.emit(f"Beklenmeyen hata: {e}")


class GenerateWorker(QThread):
    """AI test verisi üretim worker."""
    finished = Signal(dict)  # Dict[str, dict]
    error_occurred = Signal(str)
    progress = Signal(int, int)

    def __init__(self, endpoints: List[EndpointDef], api_name: str):
        super().__init__()
        self.endpoints = endpoints
        self.api_name = api_name

    def run(self):
        try:
            results = generate_all(self.endpoints, self.api_name)
            self.finished.emit(results)
        except Exception as e:
            logger.exception("Generate worker hatası")
            self.error_occurred.emit(f"Test verisi üretim hatası: {e}")


class TestRunnerPage(QWidget):
    """Test Runner sayfası."""

    def __init__(self, db_path: str, parent=None):
        super().__init__(parent)
        self.db_path = db_path

        # Stores
        self.api_store = ApiCollectionStore(db_path)
        self.session_store = TestSessionStore(db_path)
        self.result_store = TestResultStore(db_path)

        # State
        self.current_api: Optional[ApiCollection] = None
        self.current_env: Optional[Environment] = None
        self.endpoints: List[EndpointDef] = []
        self.test_bodies: Dict[str, dict] = {}  # {endpoint_key: body}
        self.test_results: Dict[str, TestResult] = {}  # {endpoint_key: result}

        # Workers
        self.parse_worker: Optional[ParseWorker] = None
        self.generate_worker: Optional[GenerateWorker] = None
        self.test_worker: Optional[TestWorker] = None

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.LG)

        # Üst bar
        top_bar = self._create_top_bar()
        layout.addWidget(top_bar)

        # Splitter: endpoint listesi (üst) + JSON editör (alt)
        splitter = QSplitter(Qt.Vertical)

        # Endpoint listesi
        self.endpoint_table = self._create_endpoint_table()
        splitter.addWidget(self.endpoint_table)

        # JSON editör
        editor_frame = self._create_editor_frame()
        splitter.addWidget(editor_frame)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

        # Alt bar: özet
        summary_bar = self._create_summary_bar()
        layout.addWidget(summary_bar)

    def _create_top_bar(self) -> QWidget:
        """Üst bar: API adı + ortam badge + butonlar."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.MD)

        # API adı + ortam badge
        self.api_label = QLabel("API koleksiyonu seçilmedi")
        self.api_label.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(self.api_label)

        self.env_badge = EnvironmentBadge("PROD")
        self.env_badge.hide()
        layout.addWidget(self.env_badge)

        layout.addStretch()

        # Parse butonu
        self.parse_btn = SecondaryButton("🔄 Parse Et")
        self.parse_btn.clicked.connect(self._on_parse_clicked)
        self.parse_btn.setEnabled(False)
        layout.addWidget(self.parse_btn)

        # AI üret butonu
        self.generate_all_btn = SecondaryButton("🤖 AI Test Verisi Üret (Tümü)")
        self.generate_all_btn.clicked.connect(self._on_generate_all_clicked)
        self.generate_all_btn.setEnabled(False)
        layout.addWidget(self.generate_all_btn)

        # Tümünü çalıştır butonu
        self.run_all_btn = PrimaryButton("▶ Tümünü Çalıştır")
        self.run_all_btn.clicked.connect(self._on_run_all_clicked)
        self.run_all_btn.setEnabled(False)
        layout.addWidget(self.run_all_btn)

        return widget

    def _create_endpoint_table(self) -> QTableWidget:
        """Endpoint listesi tablosu."""
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(["", "METHOD", "PATH", "ÖZET", "AI Üret", "Test Et", "DURUM"])

        # Column resize
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Checkbox
        header.setSectionResizeMode(1, QHeaderView.Fixed)  # Method
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Path
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Özet
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # AI Üret
        header.setSectionResizeMode(5, QHeaderView.Fixed)  # Test Et
        header.setSectionResizeMode(6, QHeaderView.Fixed)  # Durum

        table.setColumnWidth(0, 40)
        table.setColumnWidth(1, 80)
        table.setColumnWidth(4, 100)
        table.setColumnWidth(5, 100)
        table.setColumnWidth(6, 80)

        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)

        table.itemSelectionChanged.connect(self._on_endpoint_selected)

        return table

    def _create_editor_frame(self) -> QWidget:
        """JSON editör frame."""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        # Başlık
        header_layout = QHBoxLayout()
        self.editor_label = QLabel("Test Body (JSON)")
        self.editor_label.setStyleSheet(f"font-weight: 600; color: {Colors.TEXT_PRIMARY};")
        header_layout.addWidget(self.editor_label)

        header_layout.addStretch()

        # Format butonu
        format_btn = QPushButton("⚡ Format")
        format_btn.clicked.connect(self._on_format_json)
        header_layout.addWidget(format_btn)

        layout.addLayout(header_layout)

        # JSON editör
        self.json_editor = QTextEdit()
        self.json_editor.setPlaceholderText("Endpoint seçilince test body buraya gelir...")
        layout.addWidget(self.json_editor)

        return frame

    def _create_summary_bar(self) -> QWidget:
        """Alt özet bar."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.MD)

        self.summary_label = QLabel("Henüz test çalıştırılmadı")
        self.summary_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(self.summary_label)

        layout.addStretch()

        self.success_badge = SuccessCountBadge()
        self.success_badge.hide()
        layout.addWidget(self.success_badge)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        return widget

    def load_api_collection(self, api: ApiCollection, env: Environment):
        """API koleksiyonu yükler ve parse eder."""
        self.current_api = api
        self.current_env = env
        self.endpoints = []
        self.test_bodies = {}
        self.test_results = {}

        # UI güncelle
        self.api_label.setText(api.name)
        self.env_badge.set_env_type(env.env_type)
        self.env_badge.show()

        self.parse_btn.setEnabled(True)
        self.generate_all_btn.setEnabled(False)
        self.run_all_btn.setEnabled(False)

        self.endpoint_table.setRowCount(0)
        self.json_editor.clear()
        self.summary_label.setText("Parse Et butonuna tıklayın")
        self.success_badge.hide()

    def _on_parse_clicked(self):
        """Parse Et butonuna tıklandı."""
        if not self.current_api:
            return

        self.parse_btn.setEnabled(False)
        self.parse_btn.setText("⏳ Parse ediliyor...")

        # Parse worker başlat
        self.parse_worker = ParseWorker(
            self.current_api.swagger_source_type,
            self.current_api.swagger_source
        )
        self.parse_worker.finished.connect(self._on_parse_finished)
        self.parse_worker.error_occurred.connect(self._on_parse_error)
        self.parse_worker.start()

    def _on_parse_finished(self, endpoints: List[EndpointDef]):
        """Parse tamamlandı."""
        self.endpoints = endpoints
        self.parse_btn.setText("🔄 Parse Et")
        self.parse_btn.setEnabled(True)

        if not endpoints:
            Toast.show(self, "Uyarı", "Endpoint bulunamadı", "warning")
            return

        # Tabloyu doldur
        self._populate_endpoint_table()

        # Last parsed güncelle
        self.api_store.update_last_parsed(self.current_api.id)

        Toast.show(self, "Başarılı", f"{len(endpoints)} endpoint bulundu", "success")

        self.generate_all_btn.setEnabled(True)
        self.run_all_btn.setEnabled(True)
        self.summary_label.setText(f"{len(endpoints)} endpoint yüklendi")

    def _on_parse_error(self, error_msg: str):
        """Parse hatası."""
        self.parse_btn.setText("🔄 Parse Et")
        self.parse_btn.setEnabled(True)
        Toast.show(self, "Hata", f"Parse hatası: {error_msg}", "error")

    def _populate_endpoint_table(self):
        """Endpoint tablosunu doldurur."""
        self.endpoint_table.setRowCount(len(self.endpoints))

        for row, endpoint in enumerate(self.endpoints):
            # Checkbox
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.Checked)
            self.endpoint_table.setItem(row, 0, checkbox_item)

            # Method
            method_item = QTableWidgetItem(endpoint.method)
            method_item.setTextAlignment(Qt.AlignCenter)
            # Method renk kodu
            method_color = self._get_method_color(endpoint.method)
            method_item.setForeground(method_color)
            self.endpoint_table.setItem(row, 1, method_item)

            # Path
            path_item = QTableWidgetItem(endpoint.path)
            self.endpoint_table.setItem(row, 2, path_item)

            # Özet
            summary_item = QTableWidgetItem(endpoint.summary)
            self.endpoint_table.setItem(row, 3, summary_item)

            # AI Üret butonu
            generate_btn = QPushButton("🤖 Üret")
            generate_btn.clicked.connect(lambda checked, e=endpoint: self._on_generate_single(e))
            self.endpoint_table.setCellWidget(row, 4, generate_btn)

            # Test Et butonu
            test_btn = QPushButton("▶ Test")
            test_btn.clicked.connect(lambda checked, e=endpoint: self._on_test_single(e))
            self.endpoint_table.setCellWidget(row, 5, test_btn)

            # Durum badge
            status_badge = StatusBadge()
            status_badge.setText("-")
            status_badge.setStyleSheet(f"background-color: {Colors.BG_ELEVATED}; color: {Colors.TEXT_SECONDARY};")
            self.endpoint_table.setCellWidget(row, 6, status_badge)

    def _get_method_color(self, method: str) -> Qt.GlobalColor:
        """HTTP method renk kodu."""
        colors = {
            "GET": Qt.cyan,
            "POST": Qt.green,
            "PUT": Qt.yellow,
            "DELETE": Qt.red,
            "PATCH": Qt.magenta,
        }
        return colors.get(method, Qt.white)

    def _on_endpoint_selected(self):
        """Endpoint seçildi, JSON editörü güncelle."""
        selected_rows = self.endpoint_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        if row >= len(self.endpoints):
            return

        endpoint = self.endpoints[row]
        key = f"{endpoint.method} {endpoint.path}"

        # Test body varsa göster
        if key in self.test_bodies:
            import json
            body_json = json.dumps(self.test_bodies[key], indent=2, ensure_ascii=False)
            self.json_editor.setPlainText(body_json)
        else:
            self.json_editor.clear()

        self.editor_label.setText(f"Test Body: {endpoint.method} {endpoint.path}")

    def _on_generate_single(self, endpoint: EndpointDef):
        """Tek endpoint için AI test verisi üret."""
        if not self.current_api:
            return

        key = f"{endpoint.method} {endpoint.path}"
        test_data = generate_test_data(endpoint, self.current_api.name)

        if test_data:
            self.test_bodies[key] = test_data
            import json
            self.json_editor.setPlainText(json.dumps(test_data, indent=2, ensure_ascii=False))
            Toast.show(self, "Başarılı", f"Test verisi üretildi: {endpoint.path}", "success")
        else:
            Toast.show(self, "Hata", "Test verisi üretilemedi", "error")

    def _on_generate_all_clicked(self):
        """Tüm endpoint'ler için AI test verisi üret."""
        if not self.current_api or not self.endpoints:
            return

        self.generate_all_btn.setEnabled(False)
        self.generate_all_btn.setText("⏳ Üretiliyor...")

        self.generate_worker = GenerateWorker(self.endpoints, self.current_api.name)
        self.generate_worker.finished.connect(self._on_generate_all_finished)
        self.generate_worker.error_occurred.connect(self._on_generate_all_error)
        self.generate_worker.start()

    def _on_generate_all_finished(self, results: Dict[str, dict]):
        """AI test verisi üretimi tamamlandı."""
        self.test_bodies = results
        self.generate_all_btn.setText("🤖 AI Test Verisi Üret (Tümü)")
        self.generate_all_btn.setEnabled(True)
        Toast.show(self, "Başarılı", f"{len(results)} endpoint için test verisi üretildi", "success")

    def _on_generate_all_error(self, error_msg: str):
        """AI üretim hatası."""
        self.generate_all_btn.setText("🤖 AI Test Verisi Üret (Tümü)")
        self.generate_all_btn.setEnabled(True)
        Toast.show(self, "Hata", f"Test verisi üretim hatası: {error_msg}", "error")

    def _on_test_single(self, endpoint: EndpointDef):
        """Tek endpoint test et."""
        # TODO: Implement single test
        Toast.show(self, "Bilgi", "Tek test henüz implement edilmedi", "info")

    def _on_run_all_clicked(self):
        """Tüm endpoint'leri test et."""
        if not self.current_api or not self.current_env or not self.endpoints:
            return

        # Auth config
        auth = AuthConfig(
            type=self.current_env.auth_type,
            value=self.current_env.auth_value,
            header_name=self.current_env.auth_header_name
        )

        # Worker başlat
        self.test_worker = TestWorker(
            endpoints=self.endpoints,
            base_url=self.current_env.base_url,
            auth=auth,
            test_bodies=self.test_bodies,
            api_collection_id=self.current_api.id,
            mode="run_all"
        )

        self.test_worker.result_ready.connect(self._on_test_result)
        self.test_worker.all_done.connect(self._on_all_tests_done)
        self.test_worker.error_occurred.connect(self._on_test_error)
        self.test_worker.progress.connect(self._on_test_progress)

        self.test_worker.start()

        # UI güncelle
        self.run_all_btn.setEnabled(False)
        self.progress_bar.show()
        self.progress_bar.setMaximum(len(self.endpoints))
        self.progress_bar.setValue(0)
        self.summary_label.setText("Testler çalıştırılıyor...")

    def _on_test_result(self, result: TestResult):
        """Tek test sonucu geldi."""
        key = f"{result.method} {result.path}"
        self.test_results[key] = result

        # Tabloda ilgili satırı bul ve badge'i güncelle
        for row, endpoint in enumerate(self.endpoints):
            endpoint_key = f"{endpoint.method} {endpoint.path}"
            if endpoint_key == key:
                badge = self.endpoint_table.cellWidget(row, 6)
                if isinstance(badge, StatusBadge):
                    badge.update_status(result.status_code, result.error_message is not None)
                break

    def _on_test_progress(self, current: int, total: int):
        """Test ilerleme güncellemesi."""
        self.progress_bar.setValue(current)
        self.summary_label.setText(f"Test {current}/{total}")

    def _on_all_tests_done(self, session):
        """Tüm testler bitti."""
        self.progress_bar.hide()
        self.run_all_btn.setEnabled(True)

        # Session ve result'ları DB'ye kaydet
        # Session ID'yi al
        session_id = self.session_store.create(
            self.current_api.id,
            triggered_by="run_all"
        ).id

        # Result'ları session_id ile güncelle ve kaydet
        results_list = list(self.test_results.values())
        for r in results_list:
            r.session_id = session_id

        self.result_store.create_batch(results_list)

        # Session summary güncelle
        self.session_store.update_summary(
            session_id,
            session.total_count,
            session.success_count,
            session.fail_count
        )

        # UI güncelle
        self.summary_label.setText(f"Test tamamlandı: {session.success_count} başarılı, {session.fail_count} başarısız")
        self.success_badge.update_counts(session.success_count, session.total_count)
        self.success_badge.show()

        Toast.show(self, "Tamamlandı", f"Testler tamamlandı: {session.success_count}/{session.total_count} başarılı", "success")

    def _on_test_error(self, error_msg: str):
        """Test hatası."""
        self.progress_bar.hide()
        self.run_all_btn.setEnabled(True)
        self.summary_label.setText(f"Test hatası: {error_msg}")
        Toast.show(self, "Hata", f"Test hatası: {error_msg}", "error")

    def _on_format_json(self):
        """JSON formatla."""
        import json
        try:
            text = self.json_editor.toPlainText()
            if not text.strip():
                return

            data = json.loads(text)
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            self.json_editor.setPlainText(formatted)
        except json.JSONDecodeError as e:
            Toast.show(self, "Hata", f"Geçersiz JSON: {e}", "error")
