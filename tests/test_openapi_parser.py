"""
OpenAPI parser testleri.
"""
import pytest
import json
import asyncio
from pathlib import Path

from core.openapi_parser import parse_from_file, parse_from_url, OpenApiParseError, _parse_spec
from core.models import EndpointDef


# Test fixture: minimal OpenAPI 3.x spec
OPENAPI_3_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Test API", "version": "1.0.0"},
    "paths": {
        "/users": {
            "get": {
                "summary": "List users",
                "parameters": [
                    {"name": "limit", "in": "query", "schema": {"type": "integer"}}
                ]
            },
            "post": {
                "summary": "Create user",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "email": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "/users/{id}": {
            "parameters": [
                {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
            ],
            "get": {
                "summary": "Get user by ID"
            },
            "delete": {
                "summary": "Delete user"
            }
        }
    }
}


# Test fixture: Swagger 2.x spec
SWAGGER_2_SPEC = {
    "swagger": "2.0",
    "info": {"title": "Test API", "version": "1.0.0"},
    "paths": {
        "/products": {
            "get": {
                "summary": "List products",
                "parameters": [
                    {"name": "category", "in": "query", "type": "string"}
                ]
            },
            "post": {
                "summary": "Create product",
                "parameters": [
                    {
                        "name": "body",
                        "in": "body",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "price": {"type": "number"}
                            }
                        }
                    }
                ]
            }
        }
    }
}


def test_parse_openapi_3_spec():
    """OpenAPI 3.x spec'i doğru parse eder."""
    endpoints = _parse_spec(OPENAPI_3_SPEC)

    assert len(endpoints) == 4

    # GET /users
    get_users = next(e for e in endpoints if e.method == "GET" and e.path == "/users")
    assert get_users.summary == "List users"
    assert len(get_users.parameters) == 1
    assert get_users.parameters[0]['name'] == 'limit'
    assert get_users.request_body_schema is None

    # POST /users
    post_users = next(e for e in endpoints if e.method == "POST" and e.path == "/users")
    assert post_users.summary == "Create user"
    assert post_users.request_body_schema is not None
    assert 'properties' in post_users.request_body_schema
    assert 'name' in post_users.request_body_schema['properties']

    # GET /users/{id}
    get_user = next(e for e in endpoints if e.method == "GET" and e.path == "/users/{id}")
    assert get_user.summary == "Get user by ID"
    # Path-level parameter dahil edilmeli
    assert len(get_user.parameters) == 1
    assert get_user.parameters[0]['name'] == 'id'
    assert get_user.parameters[0]['in'] == 'path'

    # DELETE /users/{id}
    delete_user = next(e for e in endpoints if e.method == "DELETE" and e.path == "/users/{id}")
    assert delete_user.summary == "Delete user"
    assert len(delete_user.parameters) == 1


def test_parse_swagger_2_spec():
    """Swagger 2.x spec'i doğru parse eder."""
    endpoints = _parse_spec(SWAGGER_2_SPEC)

    assert len(endpoints) == 2

    # GET /products
    get_products = next(e for e in endpoints if e.method == "GET")
    assert get_products.summary == "List products"
    assert len(get_products.parameters) == 1
    assert get_products.parameters[0]['name'] == 'category'

    # POST /products
    post_products = next(e for e in endpoints if e.method == "POST")
    assert post_products.summary == "Create product"
    assert post_products.request_body_schema is not None
    assert 'properties' in post_products.request_body_schema


def test_parse_from_file_json(tmp_path):
    """JSON dosyadan parse eder."""
    spec_file = tmp_path / "openapi.json"
    spec_file.write_text(json.dumps(OPENAPI_3_SPEC))

    endpoints = parse_from_file(str(spec_file))

    assert len(endpoints) == 4
    assert all(isinstance(e, EndpointDef) for e in endpoints)


def test_parse_from_file_yaml(tmp_path):
    """YAML dosyadan parse eder."""
    import yaml

    spec_file = tmp_path / "openapi.yaml"
    spec_file.write_text(yaml.dump(SWAGGER_2_SPEC))

    endpoints = parse_from_file(str(spec_file))

    assert len(endpoints) == 2


def test_parse_from_file_not_found():
    """Dosya bulunamadığında exception fırlatır."""
    with pytest.raises(OpenApiParseError, match="Dosya bulunamadı"):
        parse_from_file("/nonexistent/path.json")


def test_parse_empty_paths():
    """Boş paths alanı boş liste döndürür."""
    spec = {"openapi": "3.0.0", "info": {}, "paths": {}}
    endpoints = _parse_spec(spec)
    assert endpoints == []


def test_parse_no_paths():
    """paths alanı yoksa boş liste döndürür."""
    spec = {"openapi": "3.0.0", "info": {}}
    endpoints = _parse_spec(spec)
    assert endpoints == []
