# PROJECT_PLAN.md — API Health Tester

## Proje Tanımı

Multi-tenant yapıda (Müşteri → Ortam → API Koleksiyonu) OpenAPI/Swagger dokümanlarından
otomatik test verisi üretip HTTP endpoint testleri çalıştıran, sonuçları görsel olarak
takip eden ve raporlayan PySide6 masaüstü uygulaması.

**Hedef kullanıcı:** Yazılım ekibi — yeni müşteri kurulumu sonrası sistem doğrulama  
**Platform:** Windows / macOS / Linux (PySide6 cross-platform)  
**Versiyon:** 0.1.0 (initial)

---

## Geliştirme Fazları

---

### FAZ 1 — Altyapı & Veri Katmanı
**Tahmini süre:** 1 oturum  
**Amaç:** Uygulama çalışır hale gelsin, veri modeli yerine oturmuş olsun.

#### Görevler

**1.1 Proje iskeleti**
- [ ] `requirements.txt` oluştur
- [ ] `.env.example` oluştur
- [ ] `README.md` oluştur (minimum: ne yapar, nasıl kurulur)
- [ ] `CHANGELOG.md` oluştur (`## [Unreleased]` ile başlar)
- [ ] `.gitignore` oluştur (Python + PySide6 + .env + SQLite)
- [ ] `data/` dizini `.gitkeep` ile
- [ ] `main.py` entry point (sadece `QApplication` başlatır, `MainWindow` açar)

**1.2 requirements.txt içeriği**
```
PySide6>=6.7.0
httpx>=0.27.0
anthropic>=0.30.0
pyyaml>=6.0.1
jinja2>=3.1.4
python-dotenv>=1.0.1
respx>=0.21.0   # test mock
pytest>=8.2.0
pytest-asyncio>=0.23.0
```

**1.3 Core — database.py**
- [ ] `init_db(db_path: str)` — tabloları oluştur (CREATE TABLE IF NOT EXISTS)
- [ ] `get_connection(db_path: str) -> sqlite3.Connection` — context manager
- [ ] Tüm SQL şemasını CLAUDE.md'deki gibi uygula
- [ ] `data/health_tester.db` varsayılan path

**1.4 Core — models.py**
- [ ] Tüm dataclass'ları tanımla: `Customer`, `Environment`, `ApiCollection`, `EndpointDef`, `TestSession`, `TestResult`
- [ ] `from_row(row: sqlite3.Row)` classmethod her modelde
- [ ] `to_dict()` methodu export için

**1.5 Core — session_store.py**
- [ ] `CustomerStore`: `create`, `get_all`, `get_by_id`, `update`, `delete`
- [ ] `EnvironmentStore`: `create`, `get_by_customer`, `get_by_id`, `update`
- [ ] `ApiCollectionStore`: `create`, `get_by_environment`, `get_by_id`, `update`, `delete`
- [ ] `TestSessionStore`: `create`, `update_summary`, `get_latest`, `get_history`
- [ ] `TestResultStore`: `create_batch`, `get_by_session`

**1.6 Testler**
- [ ] `tests/test_session_store.py` — in-memory SQLite ile CRUD testleri
- [ ] `conftest.py` — test DB fixture'ı

**✅ Faz 1 Tamamlanma Kriteri:**
`python main.py` çalışır (boş pencere açılır). Tüm store testleri geçer.

---

### FAZ 2 — UI İskeleti & Müşteri Yönetimi
**Tahmini süre:** 1-2 oturum  
**Amaç:** Uygulamanın görsel iskeleti tamamlansın, müşteri/ortam/API CRUD çalışsın.

#### Görevler

**2.1 Design System**
- [ ] `ui/theme.py` — tüm design token'ları (CLAUDE.md'deki renkler + spacing + typography)
- [ ] `ui/stylesheets.py` — `get_global_stylesheet() -> str` fonksiyonu
  - QMainWindow, QWidget, QScrollArea temel stilleri
  - QPushButton variant'ları (primary, secondary, ghost, danger)
  - QLineEdit, QTextEdit focus/error stilleri
  - QTreeWidget, QListWidget satır hover stilleri
  - Scrollbar stili (varsayılan asla kabul edilmez)

**2.2 Temel Bileşenler**
- [ ] `ui/components/buttons.py` — `PrimaryButton`, `SecondaryButton`, `IconButton`, `DangerButton`
- [ ] `ui/components/inputs.py` — `StyledLineEdit`, `StyledTextEdit`
- [ ] `ui/components/feedback.py` — `Toast` (success/error/info, 4 saniye auto-dismiss), `Spinner`
- [ ] `ui/components/dialogs.py` — `ConfirmDialog`

**2.3 Ana Pencere**
- [ ] `ui/main_window.py` — `MainWindow(QMainWindow)`
  - Sidebar (240px) + ContentStack yapısı
  - Minimum pencere boyutu: 1280x800
  - Başlık: "API Health Tester"

**2.4 Sidebar**
- [ ] `ui/components/navigation.py` — `Sidebar`
  - Üst navigasyon: Dashboard | Geçmiş
  - Müşteri ağacı: `QTreeWidget`
    - Müşteri düğümü (renk göstergesi + isim)
    - Alt düğümler: PROD ★ (kalın) | TEST | DEV
    - Alt-alt düğümler: API koleksiyonları
  - Alt: "+ Müşteri Ekle" butonu

**2.5 Diyaloglar — Müşteri & Ortam & API**
- [ ] `AddCustomerDialog` — isim + renk seçici
- [ ] `EditEnvironmentDialog` — base URL + auth tipi + auth değeri
- [ ] `AddApiCollectionDialog` — isim + swagger kaynak tipi (URL/Dosya) + kaynak
- [ ] Her dialog'da validasyon (boş alan, geçersiz URL formatı)

**2.6 Dashboard Sayfası**
- [ ] `ui/pages/dashboard_page.py`
  - Başlık: "Genel Durum" + son çalıştırma zamanı
  - Müşteri kartları grid (max 4 sütun)
    - Her kart: müşteri adı + PROD durumu (son session'dan)
    - PROD success/fail badge
  - "[Tüm PROD'ları Çalıştır]" butonu (Faz 3'te implement edilir, şimdilik disabled)
  - Müşteri yoksa tasarlanmış empty state

**2.7 Müşteri Sayfası**
- [ ] `ui/pages/customer_page.py`
  - Seçili müşteri başlığı + renk göstergesi
  - 3 ortam sekmesi: PROD (aktif) / TEST / DEV
  - Her ortam sekmesinde: base URL, auth bilgisi, API koleksiyonları listesi
  - Her koleksiyona "Test Et" butonu (Faz 3'te)

**✅ Faz 2 Tamamlanma Kriteri:**
- Müşteri ekle/düzenle/sil çalışır
- Ortam bilgisi düzenle çalışır
- API koleksiyonu ekle/sil çalışır
- Sidebar ağacı DB'den dolar
- Dashboard müşteri kartları görünür

---

### FAZ 3 — OpenAPI Parser & Test Engine
**Tahmini süre:** 1-2 oturum  
**Amaç:** Swagger dokümanı parse edilsin, Claude API ile test verisi üretilsin, testler çalıştırılsın.

#### Görevler

**3.1 Core — openapi_parser.py**
- [ ] `parse_from_url(url: str, timeout: int = 30) -> List[EndpointDef]`
  - `httpx` ile GET, JSON veya YAML parse
  - OpenAPI 3.x ve Swagger 2.x desteği
  - `paths` altındaki her method → `EndpointDef`
  - Request body schema'yı çıkar
  - Path ve query parameter'ları çıkar
- [ ] `parse_from_file(path: str) -> List[EndpointDef]`
  - `.json` veya `.yaml`/`.yml` dosyası
- [ ] `OpenApiParseError(Exception)` custom exception
- [ ] Testler: `tests/test_openapi_parser.py` — örnek fixture JSON ile

**3.2 Core — test_generator.py**
- [ ] `generate_test_data(endpoint: EndpointDef, api_name: str) -> dict`
  - `ANTHROPIC_API_KEY` env'den al (`python-dotenv`)
  - `claude-sonnet-4-20250514` model kullan
  - System prompt: "Sen bir API test uzmanısın. Verilen endpoint şeması için gerçekçi test verisi üret. Sadece JSON döndür, açıklama ekleme."
  - Endpoint method, path, summary ve request_body_schema'yı prompt'a ekle
  - Yanıtı JSON parse et, parse hatası → `{}` döndür, uyarı logla
- [ ] `generate_all(endpoints: List[EndpointDef], ...) -> Dict[str, dict]`
  - Her endpoint için sırayla üret, path'i key olarak kullan

**3.3 Core — test_runner.py**
- [ ] `AuthConfig` dataclass (type, value, header_name)
- [ ] `build_auth_header(auth: AuthConfig) -> dict`
- [ ] `run_single(endpoint, base_url, auth, body, timeout) -> TestResult` (async)
  - `httpx.AsyncClient` ile istek at
  - Response time ölç (millisecond)
  - Response body max 10KB (truncate)
  - Bağlantı hatası → `success=False`, `error_message` dolu
- [ ] `TestWorker(QThread)` — QThread wrapper
  - Sinyaller: `result_ready(TestResult)`, `all_done(TestSession)`, `error_occurred(str)`, `progress(int, int)`
  - `run_all` veya `run_single` modunda çalışır
- [ ] Testler: `tests/test_runner.py` — `respx` mock ile

**3.4 Test Runner Sayfası**
- [ ] `ui/pages/test_runner_page.py`
  - Üst bar: API koleksiyonu adı + ortam badge + "[Parse Et]" + "[AI Test Verisi Üret]" + "[Tümünü Çalıştır ▶]"
  - Endpoint listesi: `QTableWidget` veya özel widget
    - Sütunlar: ☑ | METHOD | PATH | ÖZET | [AI Üret] | [▶ Test Et] | DURUM
    - METHOD renk kodlu: GET→mavi, POST→yeşil, PUT→turuncu, DELETE→kırmızı, PATCH→mor
  - Seçili endpoint için test body editörü (JSON, syntax highlight)
  - AI Üret butonu → spinner → body editöre doldurur
  - Test Et butonu → spinner → sonuç badge güncellenir
  - Tümünü Çalıştır → progress bar + her endpoint güncellenir anlık
  - Alt panel: son çalıştırma özet (toplam/✅/❌)

**3.5 JSON Syntax Highlighter**
- [ ] `ui/components/inputs.py` içinde `JsonEditor(QTextEdit)`
  - `QSyntaxHighlighter` ile temel renklendirme (key, string, number, bool, null)
  - Format butonu (JSON güzelleştir)

**✅ Faz 3 Tamamlanma Kriteri:**
- Swagger URL verilince endpoint'ler listelenir
- AI ile test verisi üretilir ve editöre gelir
- Tek endpoint veya tümü test edilir
- Sonuçlar (status code, response time) anlık güncellenir

---

### FAZ 4 — Sonuçlar, Geçmiş & Export
**Tahmini süre:** 1 oturum  
**Amaç:** Sonuçlar DB'ye kaydedilsin, geçmiş görüntülensin, export çalışsın.

#### Görevler

**4.1 Sonuç Kaydetme**
- [ ] Test bitince `TestSession` ve tüm `TestResult`'lar DB'ye yazılır
- [ ] `TestWorker.all_done` sinyali session ID'yi de taşır
- [ ] Dashboard PROD kartları son session'dan güncellenir

**4.2 Geçmiş Sayfası**
- [ ] `ui/pages/history_page.py`
  - Filtreler: Müşteri | Ortam | API Koleksiyonu | Tarih aralığı
  - Oturum listesi tablosu: tarih | müşteri | ortam | API | toplam | ✅ | ❌ | [Detay] [Export]
  - Detay paneli: seçili oturumun tüm endpoint sonuçları
  - Sonuç satırına tıklayınca response body alt panelde gösterilir

**4.3 StatusBadge Bileşeni**
- [ ] `ui/components/badges.py` — `StatusBadge(QLabel)`
  - 2xx → SUCCESS rengi
  - 3xx → INFO rengi
  - 4xx → WARNING rengi
  - 5xx → ERROR rengi
  - Hata → ERROR, "ERR" yazar
  - Yuvarlak köşe, sabit genişlik

**4.4 JSON Exporter**
- [ ] `exporters/json_exporter.py`
  - `export(session: TestSession, results: List[TestResult], meta: dict) -> str` → JSON string
  - `save_to_file(session, results, meta, output_dir) -> Path`
  - Dosya adı: `{customer}_{env}_{api}_{YYYYMMDD_HHMM}.json`

**4.5 HTML Exporter**
- [ ] `templates/report.html.j2` — Jinja2 şablonu
  - Standalone HTML (inline CSS, tek dosya)
  - Header: rapor tarihi, müşteri, ortam, API adı
  - Özet kutusu: toplam/başarılı/başarısız/süre
  - Endpoint tablosu: method (renkli) | path | status | süre | başarı/hata
  - Başarısız endpoint'lerde response body accordion
- [ ] `exporters/html_exporter.py`
  - `export(session, results, meta, output_dir) -> Path`

**4.6 Export Tetikleyicileri**
- [ ] Test Runner sayfasında "[JSON]" ve "[HTML]" export butonları (son session)
- [ ] Geçmiş sayfasında her oturum satırında export butonu
- [ ] Export sonrası: "Dosya kaydedildi: {path}" toast + dosyayı klasörde aç (opsiyonel)

**4.7 "Tüm PROD'ları Çalıştır" Dashboard Aksiyonu**
- [ ] Tüm müşterilerin PROD ortamındaki tüm API koleksiyonlarını sırayla çalıştır
- [ ] Progress dialog göster (kaç koleksiyon, kaçıncısı)
- [ ] Tamamlanınca dashboard kartları güncellenir

**✅ Faz 4 Tamamlanma Kriteri:**
- Test sonuçları DB'ye kaydedilir
- Geçmiş sayfasında oturumlar listelenir
- JSON ve HTML export çalışır, dosya açılır
- Dashboard PROD kartları son test sonucuna göre güncellenir

---

## Dosya Öncelik Sırası (Claude Code için)

Aşağıdaki sırayla dosyaları oluştur — her sonraki katman bir öncekine bağımlı:

```
1.  requirements.txt
2.  .env.example
3.  .gitignore
4.  core/models.py
5.  core/database.py
6.  core/session_store.py
7.  tests/conftest.py
8.  tests/test_session_store.py
9.  ui/theme.py
10. ui/stylesheets.py
11. ui/components/buttons.py
12. ui/components/inputs.py
13. ui/components/feedback.py
14. ui/components/dialogs.py
15. ui/components/navigation.py
16. ui/components/badges.py
17. ui/pages/dashboard_page.py
18. ui/pages/customer_page.py
19. ui/main_window.py
20. main.py
    → Faz 1 & 2 kontrol noktası
21. core/openapi_parser.py
22. tests/test_openapi_parser.py
23. core/test_generator.py
24. core/test_runner.py
25. tests/test_runner.py
26. ui/pages/test_runner_page.py
    → Faz 3 kontrol noktası
27. exporters/json_exporter.py
28. templates/report.html.j2
29. exporters/html_exporter.py
30. ui/components/tables.py
31. ui/pages/history_page.py
    → Faz 4 kontrol noktası
```

---

## Bilinen Kısıtlar & Kararlar

| Konu | Karar | Gerekçe |
|---|---|---|
| Auth storage | SQLite plaintext | V1 scope, şifreleme sonraki versiyon |
| Paralel test | Hayır (sıralı) | Race condition riski yok, basit UI güncelleme |
| OpenAPI versiyonu | 2.x + 3.x | Müşterilerin eski Swagger 2.x kullananı da olabilir |
| Response body limit | 10KB | Büyük yanıtlar DB'yi şişirir |
| SSL verify | Açık (default) | Production güvenlik standardı |
| Dil | Türkçe UI | Kullanıcı kitlesi Türkçe konuşuyor |

---

## Başlangıç Komutu (Claude Code'a ver)

```
Faz 1'i başlat. CLAUDE.md ve PROJECT_PLAN.md dosyalarını oku.
Önce requirements.txt, .env.example, .gitignore, README.md ve CHANGELOG.md oluştur.
Sonra core/ katmanını (models.py, database.py, session_store.py) ve testlerini yaz.
Son olarak main.py entry point'ini oluştur (boş pencere açılsın yeter).
Her dosyayı bitirince hangi dosyayı yazdığını ve neden o sırada yazdığını tek satırla belirt.
```
