from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import ceil
from typing import Any


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    code: str
    message: str
    column: str | None = None
    affected_rows: int = 0
    sample_values: list[str] = field(default_factory=list)
    suggestion: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DataQualityProfile:
    total_rows: int
    completeness_score: float
    validity_score: float
    consistency_score: float
    duplicate_rows: int = 0
    missing_required_values: int = 0
    invalid_date_rows: int = 0
    invalid_numeric_rows: int = 0
    negative_value_rows: int = 0
    outlier_rows: int = 0
    inconsistent_rows: int = 0
    warnings_count: int = 0
    errors_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationReport:
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    issues: list[ValidationIssue]
    data_quality: DataQualityProfile

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "issues": [issue.to_dict() for issue in self.issues],
            "data_quality": self.data_quality.to_dict(),
        }


@dataclass(frozen=True)
class HistoryQuery:
    page: int = 1
    page_size: int = 10
    original_filename: str | None = None
    status: str | None = None
    file_hash: str | None = None
    date_from: str | None = None
    date_to: str | None = None

    @property
    def offset(self) -> int:
        return max(self.page - 1, 0) * self.page_size


@dataclass(frozen=True)
class PaginatedHistoryResult:
    records: list[dict[str, Any]]
    total_records: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.page_size <= 0:
            return 0

        return ceil(self.total_records / self.page_size)

    def to_dict(self) -> dict[str, Any]:
        return {
            "records": self.records,
            "total_records": self.total_records,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
        }
