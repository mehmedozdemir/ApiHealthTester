from datetime import datetime
from typing import List, Optional

from core.database import get_connection
from core.models import ApiCollection, Customer, Environment, TestResult, TestSession


class CustomerStore:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def create(self, name: str, color: str = "#5B8AF0") -> Customer:
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO customers (name, color) VALUES (?, ?)",
                (name, color),
            )
            row_id = cursor.lastrowid
        return self.get_by_id(row_id)

    def get_all(self) -> List[Customer]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM customers ORDER BY name"
            ).fetchall()
        return [Customer.from_row(r) for r in rows]

    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM customers WHERE id = ?", (customer_id,)
            ).fetchone()
        return Customer.from_row(row) if row else None

    def update(self, customer_id: int, name: str, color: str) -> Optional[Customer]:
        with get_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE customers SET name = ?, color = ? WHERE id = ?",
                (name, color, customer_id),
            )
        return self.get_by_id(customer_id)

    def delete(self, customer_id: int) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))


class EnvironmentStore:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def create(
        self,
        customer_id: int,
        env_type: str,
        base_url: str = "",
        auth_type: str = "none",
        auth_value: str = "",
        auth_header_name: str = "X-Api-Key",
    ) -> Environment:
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO environments
                   (customer_id, env_type, base_url, auth_type, auth_value, auth_header_name)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (customer_id, env_type, base_url, auth_type, auth_value, auth_header_name),
            )
            row_id = cursor.lastrowid
        return self.get_by_id(row_id)

    def get_by_customer(self, customer_id: int) -> List[Environment]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM environments WHERE customer_id = ? ORDER BY env_type",
                (customer_id,),
            ).fetchall()
        return [Environment.from_row(r) for r in rows]

    def get_by_id(self, env_id: int) -> Optional[Environment]:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM environments WHERE id = ?", (env_id,)
            ).fetchone()
        return Environment.from_row(row) if row else None

    def update(
        self,
        env_id: int,
        base_url: str,
        auth_type: str,
        auth_value: str,
        auth_header_name: str,
    ) -> Optional[Environment]:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """UPDATE environments
                   SET base_url = ?, auth_type = ?, auth_value = ?, auth_header_name = ?
                   WHERE id = ?""",
                (base_url, auth_type, auth_value, auth_header_name, env_id),
            )
        return self.get_by_id(env_id)


class ApiCollectionStore:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def create(
        self,
        environment_id: int,
        name: str,
        swagger_source_type: str,
        swagger_source: str,
    ) -> ApiCollection:
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO api_collections
                   (environment_id, name, swagger_source_type, swagger_source)
                   VALUES (?, ?, ?, ?)""",
                (environment_id, name, swagger_source_type, swagger_source),
            )
            row_id = cursor.lastrowid
        return self.get_by_id(row_id)

    def get_by_environment(self, environment_id: int) -> List[ApiCollection]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM api_collections WHERE environment_id = ? ORDER BY name",
                (environment_id,),
            ).fetchall()
        return [ApiCollection.from_row(r) for r in rows]

    def get_by_id(self, collection_id: int) -> Optional[ApiCollection]:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM api_collections WHERE id = ?", (collection_id,)
            ).fetchone()
        return ApiCollection.from_row(row) if row else None

    def update(
        self,
        collection_id: int,
        name: str,
        swagger_source_type: str,
        swagger_source: str,
    ) -> Optional[ApiCollection]:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """UPDATE api_collections
                   SET name = ?, swagger_source_type = ?, swagger_source = ?
                   WHERE id = ?""",
                (name, swagger_source_type, swagger_source, collection_id),
            )
        return self.get_by_id(collection_id)

    def update_last_parsed(self, collection_id: int) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE api_collections SET last_parsed_at = ? WHERE id = ?",
                (datetime.now().isoformat(), collection_id),
            )

    def delete(self, collection_id: int) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                "DELETE FROM api_collections WHERE id = ?", (collection_id,)
            )


class TestSessionStore:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def create(self, api_collection_id: int, triggered_by: str = "manual_single") -> TestSession:
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO test_sessions (api_collection_id, triggered_by) VALUES (?, ?)",
                (api_collection_id, triggered_by),
            )
            row_id = cursor.lastrowid
        return self.get_by_id(row_id)

    def get_by_id(self, session_id: int) -> Optional[TestSession]:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM test_sessions WHERE id = ?", (session_id,)
            ).fetchone()
        return TestSession.from_row(row) if row else None

    def update_summary(
        self,
        session_id: int,
        total_count: int,
        success_count: int,
        fail_count: int,
    ) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """UPDATE test_sessions
                   SET total_count = ?, success_count = ?, fail_count = ?, finished_at = ?
                   WHERE id = ?""",
                (total_count, success_count, fail_count, datetime.now().isoformat(), session_id),
            )

    def get_latest(self, api_collection_id: int) -> Optional[TestSession]:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """SELECT * FROM test_sessions
                   WHERE api_collection_id = ?
                   ORDER BY started_at DESC, id DESC LIMIT 1""",
                (api_collection_id,),
            ).fetchone()
        return TestSession.from_row(row) if row else None

    def get_history(self, api_collection_id: int, limit: int = 50) -> List[TestSession]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """SELECT * FROM test_sessions
                   WHERE api_collection_id = ?
                   ORDER BY started_at DESC LIMIT ?""",
                (api_collection_id, limit),
            ).fetchall()
        return [TestSession.from_row(r) for r in rows]


class TestResultStore:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def create_batch(self, results: List[TestResult]) -> None:
        with get_connection(self.db_path) as conn:
            conn.executemany(
                """INSERT INTO test_results
                   (session_id, method, path, status_code, response_time_ms,
                    request_body, response_body, error_message, success)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (
                        r.session_id,
                        r.method,
                        r.path,
                        r.status_code,
                        r.response_time_ms,
                        r.request_body,
                        r.response_body,
                        r.error_message,
                        int(r.success),
                    )
                    for r in results
                ],
            )

    def get_by_session(self, session_id: int) -> List[TestResult]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM test_results WHERE session_id = ? ORDER BY tested_at",
                (session_id,),
            ).fetchall()
        return [TestResult.from_row(r) for r in rows]
