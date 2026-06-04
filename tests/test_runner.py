"""
Test runner testleri (respx mock ile).
"""
import pytest
import asyncio
import httpx
import respx

from core.test_runner import run_single, build_auth_header, AuthConfig
from core.models import EndpointDef


@pytest.fixture
def mock_endpoint():
    """Test için örnek endpoint."""
    return EndpointDef(
        method="GET",
        path="/api/users",
        summary="List users",
        parameters=[],
        request_body_schema=None
    )


@pytest.fixture
def post_endpoint():
    """POST endpoint fixture."""
    return EndpointDef(
        method="POST",
        path="/api/users",
        summary="Create user",
        parameters=[],
        request_body_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"}
            }
        }
    )


def test_build_auth_header_none():
    """Auth none ise boş header döner."""
    auth = AuthConfig(type="none", value="")
    headers = build_auth_header(auth)
    assert headers == {}


def test_build_auth_header_bearer():
    """Bearer token header oluşturur."""
    auth = AuthConfig(type="bearer", value="test-token-123")
    headers = build_auth_header(auth)
    assert headers == {"Authorization": "Bearer test-token-123"}


def test_build_auth_header_api_key():
    """API key header oluşturur."""
    auth = AuthConfig(type="api_key", value="my-key", header_name="X-Custom-Key")
    headers = build_auth_header(auth)
    assert headers == {"X-Custom-Key": "my-key"}


@pytest.mark.asyncio
@respx.mock
async def test_run_single_success(mock_endpoint):
    """Başarılı HTTP isteği test eder."""
    base_url = "https://api.example.com"
    auth = AuthConfig(type="none", value="")

    # Mock response
    respx.get("https://api.example.com/api/users").mock(
        return_value=httpx.Response(200, json={"users": []})
    )

    result = await run_single(mock_endpoint, base_url, auth)

    assert result.method == "GET"
    assert result.path == "/api/users"
    assert result.status_code == 200
    assert result.success is True
    assert result.error_message is None
    assert result.response_time_ms > 0


@pytest.mark.asyncio
@respx.mock
async def test_run_single_with_bearer_auth(mock_endpoint):
    """Bearer auth ile istek test eder."""
    base_url = "https://api.example.com"
    auth = AuthConfig(type="bearer", value="secret-token")

    route = respx.get("https://api.example.com/api/users").mock(
        return_value=httpx.Response(200, json={})
    )

    result = await run_single(mock_endpoint, base_url, auth)

    assert result.success is True
    # Auth header'ı kontrol et
    assert route.calls.last.request.headers["Authorization"] == "Bearer secret-token"


@pytest.mark.asyncio
@respx.mock
async def test_run_single_post_with_body(post_endpoint):
    """POST request body ile test eder."""
    base_url = "https://api.example.com"
    auth = AuthConfig(type="none", value="")
    body = {"name": "John", "email": "john@example.com"}

    route = respx.post("https://api.example.com/api/users").mock(
        return_value=httpx.Response(201, json={"id": 1})
    )

    result = await run_single(post_endpoint, base_url, auth, body)

    assert result.method == "POST"
    assert result.status_code == 201
    assert result.success is True
    assert '"name": "John"' in result.request_body


@pytest.mark.asyncio
@respx.mock
async def test_run_single_4xx_error(mock_endpoint):
    """4xx hatası success=True döner (endpoint ulaşılabilir)."""
    base_url = "https://api.example.com"
    auth = AuthConfig(type="none", value="")

    respx.get("https://api.example.com/api/users").mock(
        return_value=httpx.Response(404, json={"error": "Not found"})
    )

    result = await run_single(mock_endpoint, base_url, auth)

    assert result.status_code == 404
    assert result.success is False  # 2xx dışı başarısız
    assert result.error_message is None


@pytest.mark.asyncio
@respx.mock
async def test_run_single_5xx_error(mock_endpoint):
    """5xx hatası success=False döner."""
    base_url = "https://api.example.com"
    auth = AuthConfig(type="none", value="")

    respx.get("https://api.example.com/api/users").mock(
        return_value=httpx.Response(500, json={"error": "Internal error"})
    )

    result = await run_single(mock_endpoint, base_url, auth)

    assert result.status_code == 500
    assert result.success is False


@pytest.mark.asyncio
@respx.mock
async def test_run_single_connection_error(mock_endpoint):
    """Bağlantı hatası error_message doldurur."""
    base_url = "https://api.example.com"
    auth = AuthConfig(type="none", value="")

    respx.get("https://api.example.com/api/users").mock(
        side_effect=httpx.ConnectError("Connection refused")
    )

    result = await run_single(mock_endpoint, base_url, auth)

    assert result.status_code is None
    assert result.success is False
    assert "Bağlantı hatası" in result.error_message


@pytest.mark.asyncio
@respx.mock
async def test_run_single_timeout(mock_endpoint):
    """Timeout hatası yakalar."""
    base_url = "https://api.example.com"
    auth = AuthConfig(type="none", value="")

    respx.get("https://api.example.com/api/users").mock(
        side_effect=httpx.TimeoutException("Timeout")
    )

    result = await run_single(mock_endpoint, base_url, auth, timeout=1)

    assert result.success is False
    assert "Timeout" in result.error_message


@pytest.mark.asyncio
@respx.mock
async def test_run_single_large_response_truncated(mock_endpoint):
    """Büyük response body kesilir (10KB limit)."""
    base_url = "https://api.example.com"
    auth = AuthConfig(type="none", value="")

    # 20KB response
    large_body = "x" * (20 * 1024)
    respx.get("https://api.example.com/api/users").mock(
        return_value=httpx.Response(200, text=large_body)
    )

    result = await run_single(mock_endpoint, base_url, auth)

    assert result.success is True
    # Truncate edilmeli
    assert "(truncated)" in result.response_body
    assert len(result.response_body) < len(large_body)
