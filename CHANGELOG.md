# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (Faz 3 - OpenAPI Parser & Test Engine)

- **OpenAPI Parser** (`core/openapi_parser.py`)
  - URL veya dosyadan OpenAPI 3.x ve Swagger 2.x dokümanı parse etme
  - Endpoint listesi çıkarma (method, path, summary, parameters, request_body_schema)
  - `parse_from_url()` ve `parse_from_file()` fonksiyonları
  - Kapsamlı hata yönetimi ve `OpenApiParseError` exception

- **AI Test Verisi Üretimi** (`core/test_generator.py`)
  - Claude API (Anthropic SDK) entegrasyonu
  - Endpoint şemasına göre gerçekçi test verisi üretme
  - `generate_test_data()` ve `generate_all()` fonksiyonları
  - Hata durumunda graceful fallback

- **HTTP Test Runner** (`core/test_runner.py`)
  - Async HTTP test engine (httpx kullanarak)
  - Bearer token ve API key auth desteği
  - Response body truncate (10KB limit)
  - `TestWorker` QThread implementasyonu (UI bloklamadan)
  - `run_single()` ve `run_all()` fonksiyonları
  - Progress tracking ve error handling

- **Test Runner UI Sayfası** (`ui/pages/test_runner_page.py`)
  - Endpoint listesi tablosu (method renk kodlu)
  - JSON test body editörü (format butonu ile)
  - Parse, AI üret (tek/tümü) ve test çalıştır butonları
  - Anlık test sonuçları (status badge'ler)
  - Progress bar ve özet göstergesi
  - Test session ve result'ları DB'ye kaydetme

- **Badge Bileşenleri** (`ui/components/badges.py`)
  - `StatusBadge`: HTTP status code renk kodu (2xx/3xx/4xx/5xx)
  - `EnvironmentBadge`: PROD/TEST/DEV ortam göstergesi
  - `SuccessCountBadge`: Başarı/toplam sayaç

- **Test Suite**
  - `tests/test_openapi_parser.py`: 7 test (OpenAPI 3.x, Swagger 2.x parse)
  - `tests/test_runner.py`: 11 test (auth, HTTP, timeout, error handling)
  - Tüm testler başarıyla geçiyor (46/46)

- **Sidebar Entegrasyonu**
  - API koleksiyonu seçildiğinde test runner sayfasına geçiş
  - `api_collection_selected` sinyali implementasyonu

### Changed

- `ui/main_window.py`: Test runner sayfası entegre edildi
- `ui/components/navigation.py`: API koleksiyonu seçim sinyali eklendi
