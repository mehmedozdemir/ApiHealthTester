from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Customer:
    id: int
    name: str
    color: str
    created_at: datetime

    @classmethod
    def from_row(cls, row) -> "Customer":
        return cls(
            id=row["id"],
            name=row["name"],
            color=row["color"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Environment:
    id: int
    customer_id: int
    env_type: str
    base_url: str
    auth_type: str
    auth_value: str
    auth_header_name: str

    @classmethod
    def from_row(cls, row) -> "Environment":
        return cls(
            id=row["id"],
            customer_id=row["customer_id"],
            env_type=row["env_type"],
            base_url=row["base_url"],
            auth_type=row["auth_type"],
            auth_value=row["auth_value"],
            auth_header_name=row["auth_header_name"],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "env_type": self.env_type,
            "base_url": self.base_url,
            "auth_type": self.auth_type,
            "auth_value": self.auth_value,
            "auth_header_name": self.auth_header_name,
        }


@dataclass
class ApiCollection:
    id: int
    environment_id: int
    name: str
    swagger_source_type: str
    swagger_source: str
    last_parsed_at: Optional[datetime]

    @classmethod
    def from_row(cls, row) -> "ApiCollection":
        last_parsed = row["last_parsed_at"]
        return cls(
            id=row["id"],
            environment_id=row["environment_id"],
            name=row["name"],
            swagger_source_type=row["swagger_source_type"],
            swagger_source=row["swagger_source"],
            last_parsed_at=datetime.fromisoformat(last_parsed) if last_parsed else None,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "environment_id": self.environment_id,
            "name": self.name,
            "swagger_source_type": self.swagger_source_type,
            "swagger_source": self.swagger_source,
            "last_parsed_at": self.last_parsed_at.isoformat() if self.last_parsed_at else None,
        }


@dataclass
class EndpointDef:
    method: str
    path: str
    summary: str
    parameters: List[dict]
    request_body_schema: Optional[dict]


@dataclass
class TestSession:
    id: int
    api_collection_id: int
    started_at: datetime
    finished_at: Optional[datetime]
    triggered_by: str
    total_count: int
    success_count: int
    fail_count: int

    @classmethod
    def from_row(cls, row) -> "TestSession":
        finished = row["finished_at"]
        return cls(
            id=row["id"],
            api_collection_id=row["api_collection_id"],
            started_at=datetime.fromisoformat(row["started_at"]),
            finished_at=datetime.fromisoformat(finished) if finished else None,
            triggered_by=row["triggered_by"],
            total_count=row["total_count"],
            success_count=row["success_count"],
            fail_count=row["fail_count"],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "api_collection_id": self.api_collection_id,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "triggered_by": self.triggered_by,
            "total_count": self.total_count,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
        }


@dataclass
class TestResult:
    id: int
    session_id: int
    method: str
    path: str
    status_code: Optional[int]
    response_time_ms: Optional[int]
    request_body: Optional[str]
    response_body: Optional[str]
    error_message: Optional[str]
    success: bool
    tested_at: datetime

    @classmethod
    def from_row(cls, row) -> "TestResult":
        return cls(
            id=row["id"],
            session_id=row["session_id"],
            method=row["method"],
            path=row["path"],
            status_code=row["status_code"],
            response_time_ms=row["response_time_ms"],
            request_body=row["request_body"],
            response_body=row["response_body"],
            error_message=row["error_message"],
            success=bool(row["success"]),
            tested_at=datetime.fromisoformat(row["tested_at"]),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "method": self.method,
            "path": self.path,
            "status_code": self.status_code,
            "response_time_ms": self.response_time_ms,
            "request_body": self.request_body,
            "response_body": self.response_body,
            "error_message": self.error_message,
            "success": self.success,
            "tested_at": self.tested_at.isoformat(),
        }
