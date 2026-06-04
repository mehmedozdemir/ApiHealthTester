# CLAUDE.md — API Health Tester

## Proje Özeti

**API Health Tester**, çoklu müşteri (multi-tenant) yapısında her müşterinin farklı
ortamları (PROD/TEST/DEV) ve her ortamda birden fazla Swagger/OpenAPI dokümanı ile
tanımlanmış API servislerini test etmeye yarayan bir PySide6 masaüstü uygulamasıdır.

**Birincil kullanım:** Yeni müşteri kurulumu sonrası sistemin ayakta olup olmadığını,
endpoint'lerin doğru cevap verip vermediğini hızlıca doğrulamak.

---

## Skill Referansları — Önce Oku

| Ne Yapıyorsun | Hangi Skill'i Oku |
|---|---|
| Herhangi bir UI kodu yazmadan önce | `/mnt/skills/user/pyside6-ui-ux/SKILL.md` |
| Yeni proje/modül/refactor | `/mnt/skills/user/engineering-standards/SKILL.md` |

**Bu skill'leri okumadan HİÇBİR UI kodu yazma. Zorunludur.**

---

## Tech Stack

| Katman | Teknoloji |
|---|---|
| UI Framework | PySide6 (Qt6) |
| HTTP Client | `httpx` (async, timeout destekli) |
| AI Entegrasyonu | Anthropic Python SDK (`claude-sonnet-4-20250514`) |
| Veritabanı | SQLite (`sqlite3` built-in) |
| OpenAPI Parse | `pyyaml` + `json` (built-in) |
| Export | `jinja2` (HTML), `json` (built-in) |
| Async Bridge | `asyncio` + `QThread` (UI bloklamadan HTTP) |

---

## Proje Yapısı

```
api-health-tester/
├── main.py                        # Entry point — QApplication başlatır
├── requirements.txt
├── .env.example                   # ANTHROPIC_API_KEY=
├── CLAUDE.md                      # Bu dosya
├── PROJECT_PLAN.md                # Faz planı ve görevler
├── README.md
├── CHANGELOG.md
│
├── core/
│   ├── __init__.py
│   ├── database.py                # SQLite init, migration, connection
│   ├── models.py                  # Dataclass modeller (Customer, Environment, vb.)
│   ├── openapi_parser.py          # URL/dosyadan OpenAPI parse → endpoint listesi
│   ├── test_generator.py          # Claude API ile test verisi üretimi
│   ├── test_runner.py             # httpx async HTTP engine
│   └── session_store.py           # Test session/result kaydetme & okuma
│
├── ui/
│   ├── theme.py                   # Design tokens (renkler, spacing, typography)
│   ├── stylesheets.py             # Global QSS (theme.py'den üretilir)
│   ├── main_window.py             # Ana pencere — sidebar + content stack
│   ├── components/
│   │   ├── __init__.py
│   │   ├── buttons.py             # PrimaryButton, SecondaryButton, IconButton, DangerButton
│   │   ├── cards.py               # StatCard, CustomerCard, EnvironmentCard
│   │   ├── inputs.py              # StyledInput, JsonEditor, SearchInput
│   │   ├── navigation.py          # Sidebar, SidebarItem, CustomerTreeItem
│   │   ├── badges.py              # StatusBadge (200/201/4xx/5xx renk kodlu)
│   │   ├── dialogs.py             # AddCustomerDialog, AddApiDialog, ConfirmDialog
│   │   ├── feedback.py            # Toast, Spinner, ProgressBar, EmptyState
│   │   └── tables.py              # ResultsTable, HistoryTable
│   └── pages/
│       ├── __init__.py
│       ├── dashboard_page.py      # Tüm müşterilerin PROD özeti
│       ├── customer_page.py       # Seçili müşteri detayı
│       ├── test_runner_page.py    # Endpoint listesi + test çalıştırma
│       └── history_page.py        # Geçmiş oturumlar + export
│
├── exporters/
│   ├── __init__.py
│   ├── json_exporter.py           # Test session → JSON dosyası
│   └── html_exporter.py           # Test session → HTML rapor (Jinja2)
│
├── templates/
│   └── report.html.j2             # HTML export şablonu
│
└── tests/
    ├── __init__.py
    ├── test_openapi_parser.py
    ├── test_test_runner.py
    └── test_session_store.py
```

---

## Veri Modeli

```python
# core/models.py içindeki dataclass'lar

@dataclass
class Customer:
    id: int
    name: str           # "Ankara", "İstanbul"
    color: str          # UI renk kodu, müşteri ayırt edici
    created_at: datetime

@dataclass
class Environment:
    id: int
    customer_id: int
    env_type: str       # "PROD" | "TEST" | "DEV"
    base_url: str       # "https://ankara.prod.myapi.com"
    auth_type: str      # "bearer" | "api_key" | "none"
    auth_value: str     # token veya api key değeri
    auth_header_name: str  # API key için header adı (örn. "X-Api-Key")

@dataclass
class ApiCollection:
    id: int
    environment_id: int
    name: str           # "UserService", "OrderService"
    swagger_source_type: str  # "url" | "file"
    swagger_source: str       # URL veya dosya yolu
    last_parsed_at: Optional[datetime]

@dataclass
class EndpointDef:
    # OpenAPI parse sonucu — DB'ye kaydedilmez, parse edilir
    method: str         # GET, POST, PUT, DELETE, PATCH
    path: str           # /api/users/{id}
    summary: str
    parameters: List[dict]   # path/query params
    request_body_schema: Optional[dict]

@dataclass
class TestSession:
    id: int
    api_collection_id: int
    started_at: datetime
    finished_at: Optional[datetime]
    triggered_by: str   # "manual_single" | "run_all"
    total_count: int
    success_count: int
    fail_count: int

@dataclass
class TestResult:
    id: int
    session_id: int
    method: str
    path: str
    status_code: Optional[int]
    response_time_ms: Optional[int]
    request_body: Optional[str]   # JSON string
    response_body: Optional[str]  # JSON string (ilk 10KB)
    error_message: Optional[str]  # bağlantı hatası vb.
    success: bool
    tested_at: datetime
```

---

## SQLite Şeması

```sql
-- core/database.py içinde CREATE TABLE ifadeleri

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    color TEXT NOT NULL DEFAULT '#5B8AF0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS environments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    env_type TEXT NOT NULL CHECK(env_type IN ('PROD', 'TEST', 'DEV')),
    base_url TEXT NOT NULL DEFAULT '',
    auth_type TEXT NOT NULL DEFAULT 'none' CHECK(auth_type IN ('bearer', 'api_key', 'none')),
    auth_value TEXT NOT NULL DEFAULT '',
    auth_header_name TEXT NOT NULL DEFAULT 'X-Api-Key',
    UNIQUE(customer_id, env_type)
);

CREATE TABLE IF NOT EXISTS api_collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    environment_id INTEGER NOT NULL REFERENCES environments(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    swagger_source_type TEXT NOT NULL CHECK(swagger_source_type IN ('url', 'file')),
    swagger_source TEXT NOT NULL,
    last_parsed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS test_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_collection_id INTEGER NOT NULL REFERENCES api_collections(id) ON DELETE CASCADE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    triggered_by TEXT NOT NULL DEFAULT 'manual_single',
    total_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    fail_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS test_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES test_sessions(id) ON DELETE CASCADE,
    method TEXT NOT NULL,
    path TEXT NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    request_body TEXT,
    response_body TEXT,
    error_message TEXT,
    success INTEGER NOT NULL DEFAULT 0,
    tested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## UI Kuralları — Zorunlu

### Design System
- Tüm renkler: `ui/theme.py`'den import et — HİÇBİR YERDE hex hardcode etme
- Tüm spacing: `Spacing` sabitlerini kullan — piksel değeri hardcode etme
- Tüm fontlar: `Typography` sabitlerini kullan
- Stylesheet: `ui/stylesheets.py`'i genişlet — widget dosyalarına QSS yazma

### Tema
Dark theme kullanılır. Renk referansları:
```
BG_BASE      = "#0F1117"   # Ana arka plan
BG_SURFACE   = "#1A1D27"   # Panel, sidebar, kartlar
BG_ELEVATED  = "#22263A"   # Input, hover satırı
ACCENT       = "#5B8AF0"   # Primary CTA, aktif durum
SUCCESS      = "#4CAF80"
WARNING      = "#F0A84A"
ERROR        = "#E05C6A"
```

### PROD Ortamı Görsel Vurgusu
- Sidebar'da PROD kalın font + yıldız ikonu (★) ile gösterilir
- CustomerCard içinde PROD durumu büyük renkli badge ile öne çıkar
- Dashboard'da PROD durumu kart başlığında yer alır
- "Tümünü Çalıştır" → önce PROD testleri çalışır

### StatusBadge Renk Kodu
```
2xx → SUCCESS (#4CAF80)
3xx → INFO (#5B8AF0)
4xx → WARNING (#F0A84A)
5xx → ERROR (#E05C6A)
bağlantı hatası → ERROR, "ERR" yazar
```

### Layout Mimarisi
```
MainWindow
├── Sidebar (240px sabit genişlik)
│   ├── Logo / başlık alanı
│   ├── Navigasyon (Dashboard, Müşteriler, Geçmiş)
│   └── Müşteri ağacı (Customer → PROD★ / TEST / DEV → API koleksiyonları)
└── ContentStack (QStackedWidget)
    ├── DashboardPage     (index 0 — varsayılan)
    ├── CustomerPage      (index 1)
    ├── TestRunnerPage    (index 2)
    └── HistoryPage       (index 3)
```

---

## Core Modül Kuralları

### openapi_parser.py
- `parse_from_url(url: str) -> List[EndpointDef]` — httpx ile çek, parse et
- `parse_from_file(path: str) -> List[EndpointDef]` — JSON veya YAML dosyasını oku
- JSON Schema'dan `request_body_schema` çıkar
- Path/query parameter'ları da çıkar
- Hata durumunda `OpenApiParseError` exception fırlat

### test_generator.py
- `generate_test_data(endpoint: EndpointDef, api_name: str) -> dict` — Claude API çağrısı
- Anthropic SDK kullan (`claude-sonnet-4-20250514`)
- `ANTHROPIC_API_KEY` environment variable'dan al
- Claude'a şemayı ver, JSON test body döndürmesini iste
- Yanıt JSON parse edilemezse boş dict döndür, hata logla

### test_runner.py
- `run_single(endpoint, base_url, auth_config, body) -> TestResult` — tek endpoint test
- `run_all(endpoints, ...) -> TestSession` — tüm endpoint'leri sırayla çalıştır
- `httpx.AsyncClient` kullan, timeout=30 saniye
- Response body max 10KB sakla (truncate et)
- `QThread` içinde çalıştır, sinyal ile UI'ya bildir
- Auth header'ı çalıştırma öncesi ekle (Bearer veya API Key)

### session_store.py
- CRUD: Customer, Environment, ApiCollection, TestSession, TestResult
- `get_latest_session(api_collection_id)` → son oturumu döndür
- `get_sessions_for_collection(id, limit=50)` → geçmiş listesi
- Context manager ile connection yönetimi

---

## Async & Thread Yönetimi

UI asla bloklanmamalı. Kural:
```python
# HTTP ve AI çağrıları QThread içinde yapılır
class TestWorker(QThread):
    result_ready = Signal(TestResult)
    all_done = Signal(TestSession)
    error_occurred = Signal(str)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self._run_tests())
        # Signal ile UI'ya bildir
```

---

## Export Kuralları

### JSON Export
- Tam `TestSession` + tüm `TestResult`'lar
- Müşteri adı, ortam tipi, API koleksiyonu adı da dahil
- Dosya adı: `{customer}_{env}_{api}_{tarih}.json`

### HTML Export
- `templates/report.html.j2` Jinja2 şablonu
- Standalone HTML (tek dosya, inline CSS)
- Müşteri / ortam / API bilgisi başlıkta
- Endpoint'ler tablo halinde, status code renkli
- Özet: toplam/başarılı/başarısız sayıları
- Dosya adı: `{customer}_{env}_{api}_{tarih}.html`

---

## Çevre Değişkenleri

```bash
# .env.example
ANTHROPIC_API_KEY=         # Claude API erişimi için zorunlu
DB_PATH=./data/health_tester.db   # SQLite dosya yolu (opsiyonel, default: ./data/)
HTTP_TIMEOUT=30            # HTTP istek timeout (saniye, default: 30)
MAX_RESPONSE_BODY_KB=10    # Response body max saklama boyutu (default: 10)
```

---

## Güvenlik Kuralları

- `ANTHROPIC_API_KEY` → sadece environment variable, ASLA kaynak kodda değil
- Auth token'lar SQLite'da plaintext saklanır (şifreleme bu versiyonda yok)
- HTTP istekler için SSL verify açık, self-signed için `verify=False` seçeneği opsiyonel
- Response body loglanmaz, sadece DB'ye kaydedilir

---

## Test Yazım Kuralları

- `pytest` kullan
- HTTP mock için `httpx` ile `respx` kullan
- Her parser fonksiyonu için en az bir unit test
- Test dosyaları `tests/` altında, `src/` yapısını mirror'la
- Fixture'lar `conftest.py` içinde

---

## Geliştirme Ortamı Kurulumu

```bash
# 1. Sanal ortam
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Bağımlılıklar
pip install -r requirements.txt

# 3. Env dosyası
cp .env.example .env
# .env dosyasını düzenle, ANTHROPIC_API_KEY ekle

# 4. Çalıştır
python main.py
```

---

## Commit Standartları (Conventional Commits)

```
feat(customer): add customer creation dialog
feat(test-runner): implement async HTTP test execution
fix(parser): handle YAML swagger documents
feat(export): add HTML report template with Jinja2
feat(ui): add status badge color coding for HTTP responses
fix(db): correct cascade delete for environments
```
