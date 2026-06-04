"""
HTTP test runner modülü.
Async HTTP istekleri ile endpoint testlerini çalıştırır.
"""
import asyncio
import time
import json
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

import httpx
from PySide6.QtCore import QThread, Signal

from .models import EndpointDef, TestResult, TestSession

logger = logging.getLogger(__name__)

# Response body max boyutu (byte)
MAX_RESPONSE_BODY_BYTES = 10 * 1024


@dataclass
class AuthConfig:
    """Auth konfigürasyonu."""
    type: str  # "bearer" | "api_key" | "none"
    value: str
    header_name: str = "X-Api-Key"  # api_key için header adı


def build_auth_header(auth: AuthConfig) -> Dict[str, str]:
    """
    Auth config'den HTTP header dict'i oluşturur.

    Args:
        auth: Auth konfigürasyonu

    Returns:
        Header dict. Auth yoksa boş dict.
    """
    if auth.type == "none" or not auth.value:
        return {}
    elif auth.type == "bearer":
        return {"Authorization": f"Bearer {auth.value}"}
    elif auth.type == "api_key":
        return {auth.header_name: auth.value}
    else:
        logger.warning(f"Bilinmeyen auth type: {auth.type}")
        return {}


async def run_single(
    endpoint: EndpointDef,
    base_url: str,
    auth: AuthConfig,
    body: Optional[dict] = None,
    timeout: int = 30
) -> TestResult:
    """
    Tek bir endpoint'i test eder.

    Args:
        endpoint: Test edilecek endpoint
        base_url: Base URL (örn: https://api.example.com)
        auth: Auth konfigürasyonu
        body: Request body (dict)
        timeout: HTTP timeout (saniye)

    Returns:
        TestResult
    """
    # URL oluştur
    url = base_url.rstrip('/') + endpoint.path

    # Auth header
    headers = build_auth_header(auth)
    if body and endpoint.method in ['POST', 'PUT', 'PATCH']:
        headers['Content-Type'] = 'application/json'

    # Request body JSON'a çevir
    json_body = json.dumps(body) if body else None

    start_time = time.time()
    status_code = None
    response_body = None
    error_message = None
    success = False

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=endpoint.method,
                url=url,
                headers=headers,
                content=json_body
            )

            status_code = response.status_code
            response_time_ms = int((time.time() - start_time) * 1000)

            # Response body (max 10KB)
            response_bytes = response.content
            if len(response_bytes) > MAX_RESPONSE_BODY_BYTES:
                response_body = response_bytes[:MAX_RESPONSE_BODY_BYTES].decode('utf-8', errors='ignore') + "\n...(truncated)"
            else:
                response_body = response.text

            # 2xx başarı sayılır
            success = 200 <= status_code < 300

            return TestResult(
                id=0,  # DB'ye kaydedilince doldurulur
                session_id=0,
                method=endpoint.method,
                path=endpoint.path,
                status_code=status_code,
                response_time_ms=response_time_ms,
                request_body=json_body,
                response_body=response_body,
                error_message=error_message,
                success=success,
                tested_at=datetime.now()
            )

    except httpx.TimeoutException:
        error_message = f"Timeout ({timeout}s)"
    except httpx.ConnectError as e:
        error_message = f"Bağlantı hatası: {str(e)}"
    except Exception as e:
        error_message = f"Hata: {str(e)}"

    response_time_ms = int((time.time() - start_time) * 1000)

    return TestResult(
        id=0,
        session_id=0,
        method=endpoint.method,
        path=endpoint.path,
        status_code=status_code,
        response_time_ms=response_time_ms,
        request_body=json_body,
        response_body=response_body,
        error_message=error_message,
        success=False,
        tested_at=datetime.now()
    )


class TestWorker(QThread):
    """
    QThread içinde test çalıştırma worker'ı.

    Signals:
        result_ready: Tek bir test sonucu hazır
        all_done: Tüm testler bitti, TestSession döner
        error_occurred: Genel hata oluştu
        progress: İlerleme (current, total)
    """
    result_ready = Signal(object)  # TestResult
    all_done = Signal(object)  # TestSession
    error_occurred = Signal(str)
    progress = Signal(int, int)  # current, total

    def __init__(
        self,
        endpoints: List[EndpointDef],
        base_url: str,
        auth: AuthConfig,
        test_bodies: Dict[str, dict],  # {endpoint_key: body}
        api_collection_id: int,
        mode: str = "run_all",  # "run_all" | "run_single"
        timeout: int = 30
    ):
        super().__init__()
        self.endpoints = endpoints
        self.base_url = base_url
        self.auth = auth
        self.test_bodies = test_bodies
        self.api_collection_id = api_collection_id
        self.mode = mode
        self.timeout = timeout

    def run(self):
        """QThread run methodu."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            if self.mode == "run_all":
                session = loop.run_until_complete(self._run_all())
                self.all_done.emit(session)
            elif self.mode == "run_single":
                # İlk endpoint'i çalıştır
                if self.endpoints:
                    result = loop.run_until_complete(self._run_single_endpoint(self.endpoints[0]))
                    self.result_ready.emit(result)
            else:
                self.error_occurred.emit(f"Bilinmeyen mod: {self.mode}")
        except Exception as e:
            logger.exception("Test worker hatası")
            self.error_occurred.emit(str(e))
        finally:
            loop.close()

    async def _run_single_endpoint(self, endpoint: EndpointDef) -> TestResult:
        """Tek endpoint'i test eder."""
        key = f"{endpoint.method} {endpoint.path}"
        body = self.test_bodies.get(key)
        return await run_single(endpoint, self.base_url, self.auth, body, self.timeout)

    async def _run_all(self) -> TestSession:
        """Tüm endpoint'leri test eder."""
        results = []
        total = len(self.endpoints)

        for i, endpoint in enumerate(self.endpoints, 1):
            key = f"{endpoint.method} {endpoint.path}"
            body = self.test_bodies.get(key)

            result = await run_single(endpoint, self.base_url, self.auth, body, self.timeout)
            results.append(result)

            # Sinyal gönder
            self.result_ready.emit(result)
            self.progress.emit(i, total)

        # TestSession oluştur
        success_count = sum(1 for r in results if r.success)
        fail_count = total - success_count

        session = TestSession(
            id=0,  # DB'ye kaydedilince doldurulur
            api_collection_id=self.api_collection_id,
            started_at=datetime.now(),
            finished_at=datetime.now(),
            triggered_by=self.mode,
            total_count=total,
            success_count=success_count,
            fail_count=fail_count
        )

        return session
