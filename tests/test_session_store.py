import pytest
from core.models import TestResult
from core.session_store import (
    ApiCollectionStore,
    CustomerStore,
    EnvironmentStore,
    TestResultStore,
    TestSessionStore,
)
from datetime import datetime


# ---------------------------------------------------------------------------
# CustomerStore
# ---------------------------------------------------------------------------

class TestCustomerStore:
    def test_create_returns_customer(self, db_path):
        store = CustomerStore(db_path)
        customer = store.create("Ankara", "#FF0000")
        assert customer.id is not None
        assert customer.name == "Ankara"
        assert customer.color == "#FF0000"

    def test_get_all_empty(self, db_path):
        store = CustomerStore(db_path)
        assert store.get_all() == []

    def test_get_all_returns_created(self, db_path):
        store = CustomerStore(db_path)
        store.create("Ankara")
        store.create("İstanbul")
        customers = store.get_all()
        assert len(customers) == 2
        names = [c.name for c in customers]
        assert "Ankara" in names
        assert "İstanbul" in names

    def test_get_by_id_found(self, db_path):
        store = CustomerStore(db_path)
        created = store.create("Ankara")
        fetched = store.get_by_id(created.id)
        assert fetched is not None
        assert fetched.name == "Ankara"

    def test_get_by_id_not_found(self, db_path):
        store = CustomerStore(db_path)
        assert store.get_by_id(9999) is None

    def test_update(self, db_path):
        store = CustomerStore(db_path)
        customer = store.create("Ankara", "#000000")
        updated = store.update(customer.id, "Ankara Şubesi", "#FFFFFF")
        assert updated.name == "Ankara Şubesi"
        assert updated.color == "#FFFFFF"

    def test_delete_removes_customer(self, db_path):
        store = CustomerStore(db_path)
        customer = store.create("Geçici")
        store.delete(customer.id)
        assert store.get_by_id(customer.id) is None

    def test_delete_cascades_to_environments(self, db_path):
        c_store = CustomerStore(db_path)
        e_store = EnvironmentStore(db_path)
        customer = c_store.create("Cascade Test")
        env = e_store.create(customer.id, "PROD")
        c_store.delete(customer.id)
        assert e_store.get_by_id(env.id) is None


# ---------------------------------------------------------------------------
# EnvironmentStore
# ---------------------------------------------------------------------------

class TestEnvironmentStore:
    def test_create_and_get_by_customer(self, db_path):
        c_store = CustomerStore(db_path)
        e_store = EnvironmentStore(db_path)
        customer = c_store.create("Ankara")
        env = e_store.create(customer.id, "PROD", base_url="https://api.ankara.com")
        envs = e_store.get_by_customer(customer.id)
        assert len(envs) == 1
        assert envs[0].env_type == "PROD"
        assert envs[0].base_url == "https://api.ankara.com"

    def test_get_by_customer_empty(self, db_path):
        c_store = CustomerStore(db_path)
        e_store = EnvironmentStore(db_path)
        customer = c_store.create("Ankara")
        assert e_store.get_by_customer(customer.id) == []

    def test_get_by_id_found(self, db_path):
        c_store = CustomerStore(db_path)
        e_store = EnvironmentStore(db_path)
        customer = c_store.create("Ankara")
        env = e_store.create(customer.id, "TEST")
        fetched = e_store.get_by_id(env.id)
        assert fetched is not None
        assert fetched.env_type == "TEST"

    def test_update_env(self, db_path):
        c_store = CustomerStore(db_path)
        e_store = EnvironmentStore(db_path)
        customer = c_store.create("Ankara")
        env = e_store.create(customer.id, "PROD")
        updated = e_store.update(
            env.id,
            base_url="https://prod.ankara.com",
            auth_type="bearer",
            auth_value="token_xyz",
            auth_header_name="Authorization",
        )
        assert updated.base_url == "https://prod.ankara.com"
        assert updated.auth_type == "bearer"
        assert updated.auth_value == "token_xyz"

    def test_default_auth_values(self, db_path):
        c_store = CustomerStore(db_path)
        e_store = EnvironmentStore(db_path)
        customer = c_store.create("Ankara")
        env = e_store.create(customer.id, "DEV")
        assert env.auth_type == "none"
        assert env.auth_value == ""
        assert env.auth_header_name == "X-Api-Key"


# ---------------------------------------------------------------------------
# ApiCollectionStore
# ---------------------------------------------------------------------------

class TestApiCollectionStore:
    def _setup(self, db_path):
        customer = CustomerStore(db_path).create("Ankara")
        env = EnvironmentStore(db_path).create(customer.id, "PROD")
        return env.id

    def test_create_and_get_by_environment(self, db_path):
        env_id = self._setup(db_path)
        store = ApiCollectionStore(db_path)
        col = store.create(env_id, "UserService", "url", "https://api.example.com/swagger.json")
        cols = store.get_by_environment(env_id)
        assert len(cols) == 1
        assert cols[0].name == "UserService"

    def test_get_by_id(self, db_path):
        env_id = self._setup(db_path)
        store = ApiCollectionStore(db_path)
        col = store.create(env_id, "OrderService", "url", "https://api.example.com/order.json")
        fetched = store.get_by_id(col.id)
        assert fetched is not None
        assert fetched.name == "OrderService"

    def test_update(self, db_path):
        env_id = self._setup(db_path)
        store = ApiCollectionStore(db_path)
        col = store.create(env_id, "OldName", "url", "https://old.com/swagger.json")
        updated = store.update(col.id, "NewName", "file", "/local/swagger.yaml")
        assert updated.name == "NewName"
        assert updated.swagger_source_type == "file"
        assert updated.swagger_source == "/local/swagger.yaml"

    def test_update_last_parsed(self, db_path):
        env_id = self._setup(db_path)
        store = ApiCollectionStore(db_path)
        col = store.create(env_id, "UserService", "url", "https://api.example.com/swagger.json")
        assert col.last_parsed_at is None
        store.update_last_parsed(col.id)
        updated = store.get_by_id(col.id)
        assert updated.last_parsed_at is not None

    def test_delete(self, db_path):
        env_id = self._setup(db_path)
        store = ApiCollectionStore(db_path)
        col = store.create(env_id, "ToDelete", "url", "https://api.example.com/swagger.json")
        store.delete(col.id)
        assert store.get_by_id(col.id) is None


# ---------------------------------------------------------------------------
# TestSessionStore & TestResultStore
# ---------------------------------------------------------------------------

class TestTestSessionStore:
    def _setup(self, db_path):
        customer = CustomerStore(db_path).create("Ankara")
        env = EnvironmentStore(db_path).create(customer.id, "PROD")
        col = ApiCollectionStore(db_path).create(
            env.id, "UserService", "url", "https://api.example.com/swagger.json"
        )
        return col.id

    def test_create_session(self, db_path):
        col_id = self._setup(db_path)
        store = TestSessionStore(db_path)
        session = store.create(col_id, "manual_single")
        assert session.id is not None
        assert session.api_collection_id == col_id
        assert session.triggered_by == "manual_single"
        assert session.total_count == 0
        assert session.finished_at is None

    def test_update_summary(self, db_path):
        col_id = self._setup(db_path)
        store = TestSessionStore(db_path)
        session = store.create(col_id)
        store.update_summary(session.id, total_count=5, success_count=4, fail_count=1)
        updated = store.get_by_id(session.id)
        assert updated.total_count == 5
        assert updated.success_count == 4
        assert updated.fail_count == 1
        assert updated.finished_at is not None

    def test_get_latest(self, db_path):
        col_id = self._setup(db_path)
        store = TestSessionStore(db_path)
        store.create(col_id)
        second = store.create(col_id)
        latest = store.get_latest(col_id)
        assert latest.id == second.id

    def test_get_latest_none_when_empty(self, db_path):
        col_id = self._setup(db_path)
        store = TestSessionStore(db_path)
        assert store.get_latest(col_id) is None

    def test_get_history(self, db_path):
        col_id = self._setup(db_path)
        store = TestSessionStore(db_path)
        for _ in range(3):
            store.create(col_id)
        history = store.get_history(col_id)
        assert len(history) == 3

    def test_get_history_limit(self, db_path):
        col_id = self._setup(db_path)
        store = TestSessionStore(db_path)
        for _ in range(5):
            store.create(col_id)
        history = store.get_history(col_id, limit=3)
        assert len(history) == 3


class TestTestResultStore:
    def _setup(self, db_path):
        customer = CustomerStore(db_path).create("Ankara")
        env = EnvironmentStore(db_path).create(customer.id, "PROD")
        col = ApiCollectionStore(db_path).create(
            env.id, "UserService", "url", "https://api.example.com/swagger.json"
        )
        session = TestSessionStore(db_path).create(col.id)
        return session.id

    def _make_result(self, session_id: int, path: str, success: bool) -> TestResult:
        return TestResult(
            id=0,
            session_id=session_id,
            method="GET",
            path=path,
            status_code=200 if success else 500,
            response_time_ms=120,
            request_body=None,
            response_body='{"ok": true}' if success else None,
            error_message=None if success else "Internal Server Error",
            success=success,
            tested_at=datetime.now(),
        )

    def test_create_batch_and_get(self, db_path):
        session_id = self._setup(db_path)
        store = TestResultStore(db_path)
        results = [
            self._make_result(session_id, "/api/users", True),
            self._make_result(session_id, "/api/orders", False),
        ]
        store.create_batch(results)
        fetched = store.get_by_session(session_id)
        assert len(fetched) == 2
        paths = [r.path for r in fetched]
        assert "/api/users" in paths
        assert "/api/orders" in paths

    def test_success_flag_preserved(self, db_path):
        session_id = self._setup(db_path)
        store = TestResultStore(db_path)
        store.create_batch([self._make_result(session_id, "/api/users", True)])
        results = store.get_by_session(session_id)
        assert results[0].success is True

    def test_failure_flag_preserved(self, db_path):
        session_id = self._setup(db_path)
        store = TestResultStore(db_path)
        store.create_batch([self._make_result(session_id, "/api/fail", False)])
        results = store.get_by_session(session_id)
        assert results[0].success is False
        assert results[0].error_message == "Internal Server Error"

    def test_empty_session_returns_empty_list(self, db_path):
        session_id = self._setup(db_path)
        store = TestResultStore(db_path)
        assert store.get_by_session(session_id) == []
