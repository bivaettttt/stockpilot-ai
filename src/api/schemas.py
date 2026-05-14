from typing import Any

from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ValidationIssueResponse(BaseModel):
    severity: str
    code: str
    message: str
    column: str | None = None
    affected_rows: int = 0
    sample_values: list[str] = Field(default_factory=list)
    suggestion: str | None = None


class DataQualityResponse(BaseModel):
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


class ValidateFileResponse(BaseModel):
    status: str
    message: str
    is_valid: bool
    row_count: int
    columns_found: list[str]
    required_columns: list[str]
    missing_columns: list[str]
    optional_columns: list[str]
    optional_columns_found: list[str]
    errors: list[str]
    warnings: list[str] = Field(default_factory=list)
    issues: list[ValidationIssueResponse] = Field(default_factory=list)
    data_quality: DataQualityResponse | None = None


class ColumnPresenceStatus(BaseModel):
    present: bool
    source_column: str | None = None


class ImportInspectWarning(BaseModel):
    code: str
    field: str | None = None
    title: str
    message: str
    suggestion: str | None = None


class ImportInspectResponse(BaseModel):
    filename: str
    file_type: str
    row_count: int
    column_count: int
    columns: list[str]
    sample_rows: list[dict[str, Any]] = Field(default_factory=list)
    required_columns_status: dict[str, ColumnPresenceStatus]
    optional_columns_status: dict[str, ColumnPresenceStatus]
    date_range: dict[str, str | None] | None = None
    sku_count: int | None = None
    warnings: list[ImportInspectWarning] = Field(default_factory=list)
    is_ready_for_analysis: bool
    human_readable_summary: str


class MappingSuggestionItem(BaseModel):
    source_column: str | None = None
    confidence: float = 0.0
    status: str


class MappingWarningResponse(BaseModel):
    code: str
    field: str | None = None
    title: str
    message: str
    suggestion: str | None = None


class SuggestMappingResponse(BaseModel):
    filename: str
    columns: list[str]
    suggested_mapping: dict[str, MappingSuggestionItem]
    warnings: list[MappingWarningResponse] = Field(default_factory=list)
    is_ready_for_normalization: bool


class ValidateMappingResponse(BaseModel):
    is_valid: bool
    errors: list[MappingWarningResponse] = Field(default_factory=list)
    warnings: list[MappingWarningResponse] = Field(default_factory=list)
    mapping: dict[str, MappingSuggestionItem]
    human_readable_summary: str


class AnalyzeResponse(BaseModel):
    run_id: str | None = None
    status: str
    message: str
    original_filename: str | None = None
    created_at: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    summary_metrics: dict[str, Any]
    insights: list[str]
    recommendations: list[dict[str, Any]]
    category_recommendations: list[dict[str, Any]] = Field(default_factory=list)
    top_products: list[dict[str, Any]]
    daily_sales: list[dict[str, Any]] = Field(default_factory=list)
    product_forecast: list[dict[str, Any]]
    daily_forecast_chart_data: list[dict[str, Any]] = Field(default_factory=list)
    category_sales: list[dict[str, Any]]
    analytics_snapshot: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    abc_analysis: list[dict[str, Any]]
    abc_summary: dict[str, Any]
    xyz_analysis: list[dict[str, Any]]
    xyz_summary: dict[str, Any]
    abc_xyz_matrix: list[dict[str, Any]]
    abc_xyz_summary: dict[str, Any]
    data_quality: DataQualityResponse | None = None
    analysis_reliability: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)
    analysis_duration_ms: int | None = None
    report_path: str
    dashboard_path: str
    recommendations_csv_path: str
    abc_xyz_matrix_csv_path: str
    report_url: str
    dashboard_url: str
    recommendations_csv_url: str
    abc_xyz_matrix_csv_url: str
    recommendations_raw_csv_path: str | None = None
    recommendations_raw_csv_url: str | None = None


class HistoryRecord(BaseModel):
    id: str
    created_at: str
    original_filename: str
    horizon: int
    safety_stock: float
    lead_time: int
    status: str = "success"
    file_hash: str | None = None
    summary_metrics: dict[str, Any]
    recommendations_count: int
    analysis_duration_ms: int | None = None
    report_path: str
    dashboard_path: str
    report_url: str
    dashboard_url: str
    data_quality: DataQualityResponse | None = None
    recommendations_csv_path: str | None = None
    recommendations_csv_url: str | None = None
    abc_xyz_matrix_csv_path: str | None = None
    abc_xyz_matrix_csv_url: str | None = None
    has_result_snapshot: bool = False
    has_saved_decisions: bool = False


class PaginationResponse(BaseModel):
    page: int
    page_size: int
    total_records: int
    total_pages: int


class HistoryResponse(BaseModel):
    status: str
    records: list[HistoryRecord]
    pagination: PaginationResponse | None = None


class HistoryArtifactFile(BaseModel):
    kind: str
    title: str
    path: str | None = None
    url: str | None = None
    available: bool


class HistoryFilesResponse(BaseModel):
    run_id: str
    files: list[HistoryArtifactFile]


class HistoryDecisionsResponse(BaseModel):
    run_id: str
    decisions: dict[str, Any] = Field(default_factory=dict)


class SupplierPayload(BaseModel):
    name: str
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    default_lead_time_days: int = Field(default=0, ge=0)
    min_order_value: float | None = Field(default=None, ge=0)
    notes: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Укажите название поставщика.")
        return normalized

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        normalized = value.strip()
        if "@" not in normalized or "." not in normalized.split("@")[-1]:
            raise ValueError("Укажите корректный email поставщика.")
        return normalized


class SupplierResponse(SupplierPayload):
    id: str
    created_at: str
    updated_at: str


class SupplierListResponse(BaseModel):
    status: str
    suppliers: list[SupplierResponse]


class SkuSettingPayload(BaseModel):
    product_name: str | None = None
    supplier_id: str | None = None
    purchase_price: float | None = Field(default=None, ge=0)
    selling_price: float | None = Field(default=None, ge=0)
    lead_time_days: int | None = Field(default=None, ge=0)
    moq: int | None = Field(default=None, ge=0)
    pack_size: int | None = Field(default=None, ge=1)
    safety_stock_override: float | None = Field(default=None, ge=0)
    notes: str | None = None


class SkuSettingResponse(SkuSettingPayload):
    sku: str
    supplier_name: str | None = None
    supplier_default_lead_time_days: int | None = None
    updated_at: str


class SkuSettingsListResponse(BaseModel):
    status: str
    items: list[SkuSettingResponse]


class ProcurementPlanItem(BaseModel):
    sku: str
    product_name: str
    category: str | None = None
    supplier: str | None = None
    purchase_price: float | None = None
    selling_price: float | None = None
    current_stock: float | None = None
    average_daily_demand: float | None = None
    stock_days_left: float | str | None = None
    recommended_order_qty: float = Field(ge=0)
    priority: str | None = None
    message: str | None = None
    explanation: str | None = None
    stockout_risk: float | None = None


class ProcurementEnrichRequest(BaseModel):
    items: list[ProcurementPlanItem] = Field(default_factory=list)


class ProcurementEnrichedItem(ProcurementPlanItem):
    system_recommended_qty: int
    adjusted_order_qty: int
    adjustment_reason: str | None = None
    supplier_name: str | None = None
    supplier_lead_time_days: int | None = None
    moq: int | None = None
    pack_size: int | None = None
    estimated_cost: float | None = None
    supplier_source: str
    purchase_price_source: str
    selling_price_source: str
    lead_time_source: str
    moq_source: str
    pack_size_source: str


class ProcurementEnrichResponse(BaseModel):
    items: list[ProcurementEnrichedItem] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    status: str
    message: str
    errors: list[str] | None = None
    request_id: str | None = None


class CopilotMessage(BaseModel):
    role: str
    text: str


class CopilotStreamRequest(BaseModel):
    message: str
    locale: str = "ru"
    selected_sku: str | None = None
    active_page: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    conversation: list[CopilotMessage] = Field(default_factory=list)


class ImportAssistRequest(BaseModel):
    question: str
    context: dict[str, Any] = Field(default_factory=dict)


class ImportAssistResponse(BaseModel):
    answer: str
    model: str
    provider: str = "ollama"
    is_local: bool = True
    fallback: bool = False
    error_code: str | None = None


class CopilotStatusResponse(BaseModel):
    provider: str = "ollama"
    is_local: bool = True
    base_url: str
    model: str
    available: bool
    message: str
    error_code: str | None = None


class WorkspaceSettingsResponse(BaseModel):
    status: str
    data: dict[str, Any]
