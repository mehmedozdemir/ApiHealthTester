"""
OpenAPI/Swagger parser module.
URL veya dosyadan OpenAPI/Swagger dokümanı parse eder ve EndpointDef listesi döndürür.
"""
import json
from typing import List, Dict, Any, Optional
import httpx
import yaml

from .models import EndpointDef


class OpenApiParseError(Exception):
    """OpenAPI parse hatalarında fırlatılır."""
    pass


async def parse_from_url(url: str, timeout: int = 30) -> List[EndpointDef]:
    """
    URL'den OpenAPI/Swagger dokümanı çeker ve parse eder.

    Args:
        url: OpenAPI doküman URL'i
        timeout: HTTP timeout (saniye)

    Returns:
        EndpointDef listesi

    Raises:
        OpenApiParseError: Parse hatası veya HTTP hatası durumunda
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            content = response.text

            # JSON veya YAML olabilir
            try:
                spec = json.loads(content)
            except json.JSONDecodeError:
                try:
                    spec = yaml.safe_load(content)
                except yaml.YAMLError as e:
                    raise OpenApiParseError(f"JSON veya YAML parse edilemedi: {e}")

            return _parse_spec(spec)
    except httpx.HTTPError as e:
        raise OpenApiParseError(f"HTTP hatası: {e}")
    except Exception as e:
        raise OpenApiParseError(f"Parse hatası: {e}")


def parse_from_file(path: str) -> List[EndpointDef]:
    """
    Dosyadan OpenAPI/Swagger dokümanı okur ve parse eder.

    Args:
        path: JSON veya YAML dosya yolu

    Returns:
        EndpointDef listesi

    Raises:
        OpenApiParseError: Dosya okuma veya parse hatası durumunda
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Dosya uzantısına göre parse et
        if path.endswith('.json'):
            spec = json.loads(content)
        elif path.endswith(('.yaml', '.yml')):
            spec = yaml.safe_load(content)
        else:
            # Uzantı bilinmiyorsa önce JSON dene, sonra YAML
            try:
                spec = json.loads(content)
            except json.JSONDecodeError:
                spec = yaml.safe_load(content)

        return _parse_spec(spec)
    except FileNotFoundError:
        raise OpenApiParseError(f"Dosya bulunamadı: {path}")
    except Exception as e:
        raise OpenApiParseError(f"Dosya parse hatası: {e}")


def _parse_spec(spec: Dict[str, Any]) -> List[EndpointDef]:
    """
    OpenAPI/Swagger spec dict'ini parse eder.
    OpenAPI 3.x ve Swagger 2.x destekler.

    Args:
        spec: Parse edilmiş OpenAPI/Swagger dokümanı

    Returns:
        EndpointDef listesi
    """
    endpoints = []

    # paths alanını kontrol et
    paths = spec.get('paths', {})
    if not paths:
        return endpoints

    # OpenAPI versiyonunu tespit et
    is_openapi_3 = 'openapi' in spec and spec['openapi'].startswith('3')

    for path, path_item in paths.items():
        # HTTP method'ları iterate et
        for method in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
            if method not in path_item:
                continue

            operation = path_item[method]

            # Summary bilgisi
            summary = operation.get('summary', operation.get('operationId', f"{method.upper()} {path}"))

            # Parameters (path/query/header)
            parameters = _extract_parameters(operation, path_item, is_openapi_3)

            # Request body schema
            request_body_schema = _extract_request_body(operation, is_openapi_3)

            endpoint = EndpointDef(
                method=method.upper(),
                path=path,
                summary=summary,
                parameters=parameters,
                request_body_schema=request_body_schema
            )

            endpoints.append(endpoint)

    return endpoints


def _extract_parameters(operation: Dict[str, Any], path_item: Dict[str, Any], is_openapi_3: bool) -> List[Dict[str, Any]]:
    """
    Operation ve path_item'dan parameter listesini çıkarır.
    Path-level ve operation-level parametreleri birleştirir.
    """
    params = []

    # Path-level parametreler (her method için geçerli)
    path_params = path_item.get('parameters', [])
    # Operation-level parametreler
    operation_params = operation.get('parameters', [])

    # Birleştir (operation-level override eder)
    all_params = path_params + operation_params

    for param in all_params:
        param_info = {
            'name': param.get('name', ''),
            'in': param.get('in', 'query'),  # query, path, header, cookie
            'required': param.get('required', False),
            'description': param.get('description', ''),
        }

        # Schema bilgisi (OpenAPI 3.x)
        if is_openapi_3 and 'schema' in param:
            param_info['schema'] = param['schema']
        # Type bilgisi (Swagger 2.x)
        elif 'type' in param:
            param_info['type'] = param['type']

        params.append(param_info)

    return params


def _extract_request_body(operation: Dict[str, Any], is_openapi_3: bool) -> Optional[Dict[str, Any]]:
    """
    Operation'dan request body schema'yı çıkarır.
    OpenAPI 3.x ve Swagger 2.x için farklı şekilde çalışır.
    """
    if is_openapi_3:
        # OpenAPI 3.x: requestBody field'ı
        request_body = operation.get('requestBody')
        if not request_body:
            return None

        content = request_body.get('content', {})
        # application/json öncelikli, yoksa ilk content type
        if 'application/json' in content:
            return content['application/json'].get('schema')
        elif content:
            # İlk content type'ı al
            first_content = next(iter(content.values()))
            return first_content.get('schema')

        return None
    else:
        # Swagger 2.x: parameters içinde body type'ı
        params = operation.get('parameters', [])
        for param in params:
            if param.get('in') == 'body':
                return param.get('schema')

        return None
