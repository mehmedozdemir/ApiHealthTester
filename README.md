# API Health Tester

Multi-tenant API health check desktop application. Tests OpenAPI/Swagger-defined endpoints across multiple customers and environments (PROD/TEST/DEV), generates test data via Claude AI, and reports results.

## Prerequisites

- Python 3.11+
- pip

## Quick Start

```bash
# 1. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# Edit .env and set ANTHROPIC_API_KEY

# 4. Run
python main.py
```

## Configuration

| Variable | Description | Default |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude API key (required) | — |
| `DB_PATH` | SQLite database file path | `./data/health_tester.db` |
| `HTTP_TIMEOUT` | HTTP request timeout in seconds | `30` |
| `MAX_RESPONSE_BODY_KB` | Max response body stored per result | `10` |

## Architecture

```
core/           ← Data models, database, OpenAPI parser, test engine
ui/             ← PySide6 UI (theme, components, pages)
exporters/      ← JSON and HTML report exporters
templates/      ← Jinja2 HTML report template
tests/          ← pytest test suite
```

## Contributing

1. Branch from `main`: `feature/<description>` or `fix/<description>`
2. Commit with Conventional Commits: `feat(scope): description`
3. Tests must pass before merge: `pytest`
