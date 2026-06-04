"""
Claude API ile test verisi üretimi modülü.
"""
import os
import json
import logging
from typing import Dict, List
from anthropic import Anthropic

from .models import EndpointDef

logger = logging.getLogger(__name__)


def generate_test_data(endpoint: EndpointDef, api_name: str) -> dict:
    """
    Claude API kullanarak endpoint için test verisi üretir.

    Args:
        endpoint: Test verisi üretilecek endpoint
        api_name: API koleksiyonu adı (context için)

    Returns:
        Test verisi (dict). Parse hatası durumunda boş dict döner.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable bulunamadı")
        return {}

    try:
        client = Anthropic(api_key=api_key)

        # Prompt oluştur
        prompt = _build_prompt(endpoint, api_name)

        # Claude API çağrısı
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system="Sen bir API test uzmanısın. Verilen endpoint şeması için gerçekçi test verisi üret. Sadece JSON döndür, açıklama ekleme.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Response'u parse et
        response_text = message.content[0].text.strip()

        # JSON olarak parse et
        test_data = json.loads(response_text)
        return test_data

    except json.JSONDecodeError as e:
        logger.warning(f"Claude API yanıtı JSON olarak parse edilemedi: {e}")
        logger.debug(f"Yanıt metni: {response_text}")
        return {}
    except Exception as e:
        logger.error(f"Test verisi üretim hatası: {e}")
        return {}


def generate_all(endpoints: List[EndpointDef], api_name: str) -> Dict[str, dict]:
    """
    Tüm endpoint'ler için test verisi üretir.

    Args:
        endpoints: EndpointDef listesi
        api_name: API koleksiyonu adı

    Returns:
        Path'e göre test verisi dict'i: {"/api/users": {...}, ...}
    """
    results = {}

    for endpoint in endpoints:
        # Sadece request body gerektiren endpoint'ler için üret
        if endpoint.request_body_schema:
            test_data = generate_test_data(endpoint, api_name)
            key = f"{endpoint.method} {endpoint.path}"
            results[key] = test_data
        else:
            # Body gerektirmeyen endpoint'ler için boş dict
            key = f"{endpoint.method} {endpoint.path}"
            results[key] = {}

    return results


def _build_prompt(endpoint: EndpointDef, api_name: str) -> str:
    """
    Claude API için prompt oluşturur.
    """
    prompt_parts = [
        f"API: {api_name}",
        f"Endpoint: {endpoint.method} {endpoint.path}",
        f"Açıklama: {endpoint.summary}",
        ""
    ]

    # Parameters varsa ekle
    if endpoint.parameters:
        prompt_parts.append("Parametreler:")
        for param in endpoint.parameters:
            param_desc = f"- {param['name']} ({param['in']})"
            if param.get('required'):
                param_desc += " [zorunlu]"
            if 'description' in param and param['description']:
                param_desc += f": {param['description']}"
            prompt_parts.append(param_desc)
        prompt_parts.append("")

    # Request body schema varsa ekle
    if endpoint.request_body_schema:
        prompt_parts.append("Request Body Schema:")
        prompt_parts.append(json.dumps(endpoint.request_body_schema, indent=2, ensure_ascii=False))
        prompt_parts.append("")
        prompt_parts.append("Bu şemaya uygun gerçekçi bir test verisi JSON'u üret. Sadece JSON döndür.")
    else:
        prompt_parts.append("Bu endpoint request body gerektirmiyor. Boş bir JSON objesi ({}) döndür.")

    return "\n".join(prompt_parts)
