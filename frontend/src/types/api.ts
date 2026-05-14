export type SummaryMetrics = {
  total_revenue?: number;
  total_units_sold?: number;
  unique_products?: number;
  unique_categories?: number;
  gross_profit?: number;
  gross_margin_percent?: number;
  inventory_turnover_ratio?: number;
  date_range_days?: number;
};

export type ValidationIssue = {
  severity: "error" | "warning" | string;
  code: string;
  message: string;
  column?: string | null;
  affected_rows?: number;
  sample_values?: string[];
  suggestion?: string | null;
};

export type DataQualityProfile = {
  total_rows: number;
  completeness_score: number;
  validity_score: number;
  consistency_score: number;
  duplicate_rows: number;
  missing_required_values: number;
  invalid_date_rows: number;
  invalid_numeric_rows: number;
  negative_value_rows: number;
  outlier_rows: number;
  inconsistent_rows: number;
  warnings_count: number;
  errors_count: number;
};

export type Recommendation = {
  sku: string;
  product_name: string;
  category: string;
  supplier?: string | null;
  purchase_price?: number | null;
  selling_price?: number | null;
  type: string;
  action_group?: "urgent" | "planned" | "monitor" | "no_action" | string;
  priority: string;
  current_stock: number;
  stock_days_left: number | string;
  days_of_cover?: number | null;
  average_daily_demand: number;
  predicted_quantity: number;
  recommended_order_qty: number;
  expected_revenue: number;
  safety_stock?: number;
  lead_time_demand?: number;
  reorder_point?: number;
  target_stock_level?: number;
  inventory_gap?: number;
  stockout_risk?: number;
  stockout_risk_label?: string;
  overstock_risk?: number;
  overstock_risk_label?: string;
  forecast_model?: string;
  confidence_score?: number;
  confidence_label?: string;
  demand_pattern?: string;
  qty_if_lead_time_plus_2?: number;
  qty_if_safety_stock_plus_10pct?: number;
  qty_if_demand_growth_10pct?: number;
  system_recommended_qty?: number | null;
  adjusted_order_qty?: number | null;
  adjustment_reason?: string | null;
  supplier_name?: string | null;
  supplier_lead_time_days?: number | null;
  moq?: number | null;
  pack_size?: number | null;
  estimated_cost?: number | null;
  supplier_source?: "file" | "directory" | "missing" | string;
  purchase_price_source?: "file" | "directory" | "missing" | string;
  selling_price_source?: "file" | "directory" | "missing" | string;
  lead_time_source?: "file" | "directory" | "missing" | string;
  moq_source?: "file" | "directory" | "missing" | string;
  pack_size_source?: "file" | "directory" | "missing" | string;
  message: string;
  explanation?: string;
};

export type CategoryRecommendation = {
  category: string;
  skus: number;
  urgent_skus: number;
  total_recommended_order_qty: number;
  forecast_revenue: number;
  average_stockout_risk: number;
  average_overstock_risk: number;
  action_group: string;
  message: string;
};

export type TopProduct = {
  sku: string;
  product_name: string;
  category: string;
  total_quantity_sold: number;
  total_revenue: number;
  current_stock: number;
  average_daily_sales: number;
  stock_days_left: number | string;
};

export type ProductForecast = {
  sku: string;
  product_name: string;
  category: string;
  horizon_days: number;
  current_stock: number;
  average_daily_demand: number;
  predicted_quantity: number;
  lower_bound: number;
  upper_bound: number;
  expected_revenue: number;
  forecast_model?: string;
  forecast_score?: number;
  confidence_score?: number;
  confidence_label?: string;
  trend_percent?: number;
  seasonality_strength?: number;
  demand_pattern?: string;
  intermittency_ratio?: number;
};

export type DailyForecastPoint = {
  date: string;
  sku: string;
  product_name: string;
  predicted_quantity: number;
  forecast_model?: string;
};

export type CategorySales = {
  category: string;
  total_quantity_sold: number;
  total_revenue: number;
  unique_products: number;
  average_stock_on_hand?: number;
  inventory_turnover_ratio?: number;
};

export type DailySalesPoint = {
  date: string;
  revenue: number;
  quantity_sold: number;
};

export type ABCAnalysisItem = {
  sku: string;
  product_name: string;
  category: string;
  total_revenue: number;
  total_quantity_sold: number;
  revenue_share_percent: number;
  cumulative_share_percent: number;
  abc_class: string;
  abc_description: string;
};

export type ABCSummaryGroup = {
  products_count: number;
  total_revenue: number;
  revenue_share_percent: number;
};

export type ABCSummary = Record<string, ABCSummaryGroup>;

export type XYZAnalysisItem = {
  sku: string;
  product_name: string;
  category: string;
  observation_days: number;
  total_quantity_sold: number;
  total_revenue: number;
  average_daily_demand: number;
  demand_std: number;
  coefficient_of_variation: number;
  xyz_class: string;
  xyz_description: string;
};

export type XYZSummary = Record<string, ABCSummaryGroup>;

export type ABCXYZMatrixItem = {
  sku: string;
  product_name: string;
  category: string;
  abc_class: string;
  xyz_class: string;
  abc_xyz_class: string;
  total_revenue: number;
  total_quantity_sold: number;
  revenue_share_percent: number;
  cumulative_share_percent: number;
  average_daily_demand: number;
  coefficient_of_variation: number;
  management_action: string;
  management_priority: "high" | "medium" | "low" | string;
};

export type ABCXYZSummaryGroup = {
  products_count: number;
  total_revenue: number;
  revenue_share_percent: number;
  management_action: string;
  management_priority: "high" | "medium" | "low" | string;
};

export type AnalyticsSnapshot = {
  weekday_sales?: Array<Record<string, number | string>>;
  monthly_sales?: Array<Record<string, number | string>>;
  supplier_sales?: Array<Record<string, number | string>>;
  promotion_performance?: Array<Record<string, number | string>>;
  inventory_health?: Array<Record<string, number | string>>;
  demand_anomalies?: Array<Record<string, number | string>>;
};

export type ReliabilityWarning = {
  code: string;
  title: string;
  message: string;
  suggestion?: string | null;
};

export type ReliabilityDataQuality = {
  score?: number | null;
  label: string;
  warnings: ReliabilityWarning[];
};

export type ForecastQuality = {
  overall_confidence: "high" | "medium" | "low" | "insufficient_data" | string;
  reliability_score?: number | null;
  wape?: number | null;
  mae?: number | null;
  bias?: number | null;
  backtest_period_days?: number | null;
  coverage?: number | null;
  warnings: ReliabilityWarning[];
};

export type SkuReliability = {
  sku: string;
  product_name: string;
  category: string;
  demand_pattern?: string | null;
  data_points?: number | null;
  history_days?: number | null;
  zero_sales_days?: number | null;
  stockout_risk_days?: number | null;
  wape?: number | null;
  mae?: number | null;
  bias?: number | null;
  confidence: "high" | "medium" | "low" | "insufficient_data" | string;
  reliability_reason: string;
  reason: string;
};

export type AnalysisReliability = {
  data_quality: ReliabilityDataQuality;
  forecast_quality: ForecastQuality;
  sku_reliability: SkuReliability[];
  warnings: ReliabilityWarning[];
};

export type AnalyzeResponse = {
  run_id?: string | null;
  status: string;
  message: string;
  original_filename?: string | null;
  created_at?: string | null;
  parameters?: Record<string, string | number | boolean | null>;
  summary_metrics: SummaryMetrics;
  insights: string[];
  recommendations: Recommendation[];
  category_recommendations: CategoryRecommendation[];
  top_products: TopProduct[];
  daily_sales: DailySalesPoint[];
  product_forecast: ProductForecast[];
  daily_forecast_chart_data: DailyForecastPoint[];
  category_sales: CategorySales[];
  analytics_snapshot: AnalyticsSnapshot;
  abc_analysis: ABCAnalysisItem[];
  abc_summary: ABCSummary;
  xyz_analysis: XYZAnalysisItem[];
  xyz_summary: XYZSummary;
  abc_xyz_matrix: ABCXYZMatrixItem[];
  abc_xyz_summary: Record<string, ABCXYZSummaryGroup>;
  data_quality?: DataQualityProfile | null;
  analysis_reliability?: AnalysisReliability | null;
  warnings?: string[];
  analysis_duration_ms?: number | null;
  report_path: string;
  dashboard_path: string;
  recommendations_csv_path: string;
  abc_xyz_matrix_csv_path: string;
  report_url: string;
  dashboard_url: string;
  recommendations_csv_url: string;
  abc_xyz_matrix_csv_url: string;
};

export type CopilotStatusResponse = {
  provider: "ollama" | string;
  is_local: boolean;
  base_url: string;
  model: string;
  available: boolean;
  message: string;
  error_code?: string | null;
};

export type ValidateFileResponse = {
  status: string;
  message: string;
  is_valid: boolean;
  row_count: number;
  columns_found: string[];
  required_columns: string[];
  missing_columns: string[];
  optional_columns: string[];
  optional_columns_found: string[];
  errors: string[];
  warnings: string[];
  issues: ValidationIssue[];
  data_quality?: DataQualityProfile | null;
};

export type ColumnPresenceStatus = {
  present: boolean;
  source_column: string | null;
};

export type ImportInspectWarning = {
  code: string;
  field?: string | null;
  title: string;
  message: string;
  suggestion?: string | null;
};

export type ImportInspectResponse = {
  filename: string;
  file_type: string;
  row_count: number;
  column_count: number;
  columns: string[];
  sample_rows: Array<Record<string, string | number | boolean | null>>;
  required_columns_status: Record<string, ColumnPresenceStatus>;
  optional_columns_status: Record<string, ColumnPresenceStatus>;
  date_range?: {
    min?: string | null;
    max?: string | null;
  } | null;
  sku_count?: number | null;
  warnings: ImportInspectWarning[];
  is_ready_for_analysis: boolean;
  human_readable_summary: string;
};

export type MappingSuggestionItem = {
  source_column: string | null;
  confidence: number;
  status: string;
};

export type MappingWarningResponse = {
  code: string;
  field?: string | null;
  title: string;
  message: string;
  suggestion?: string | null;
};

export type SuggestMappingResponse = {
  filename: string;
  columns: string[];
  suggested_mapping: Record<string, MappingSuggestionItem>;
  warnings: MappingWarningResponse[];
  is_ready_for_normalization: boolean;
};

export type ValidateMappingResponse = {
  is_valid: boolean;
  errors: MappingWarningResponse[];
  warnings: MappingWarningResponse[];
  mapping: Record<string, MappingSuggestionItem>;
  human_readable_summary: string;
};

export type HistoryRecord = {
  id: string;
  created_at: string;
  original_filename: string;
  horizon: number;
  safety_stock: number;
  lead_time: number;
  status: string;
  file_hash?: string | null;
  summary_metrics: SummaryMetrics;
  recommendations_count: number;
  analysis_duration_ms?: number | null;
  report_path: string;
  dashboard_path: string;
  report_url: string;
  dashboard_url: string;
  data_quality?: DataQualityProfile | null;
  recommendations_csv_path?: string | null;
  abc_xyz_matrix_csv_path?: string | null;
  recommendations_csv_url?: string | null;
  abc_xyz_matrix_csv_url?: string | null;
  has_result_snapshot?: boolean;
  has_saved_decisions?: boolean;
};

export type PaginationMeta = {
  page: number;
  page_size: number;
  total_records: number;
  total_pages: number;
};

export type HistoryResponse = {
  status: string;
  records: HistoryRecord[];
  pagination?: PaginationMeta | null;
};

export type HistoryArtifactFile = {
  kind: string;
  title: string;
  path?: string | null;
  url?: string | null;
  available: boolean;
};

export type HistoryFilesResponse = {
  run_id: string;
  files: HistoryArtifactFile[];
};

export type HistoryDecisionsResponse = {
  run_id: string;
  decisions: Record<string, unknown>;
};

export type Supplier = {
  id: string;
  name: string;
  contact_name?: string | null;
  email?: string | null;
  phone?: string | null;
  default_lead_time_days: number;
  min_order_value?: number | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
};

export type SupplierPayload = {
  name: string;
  contact_name?: string | null;
  email?: string | null;
  phone?: string | null;
  default_lead_time_days: number;
  min_order_value?: number | null;
  notes?: string | null;
};

export type SuppliersResponse = {
  status: string;
  suppliers: Supplier[];
};

export type SkuSetting = {
  sku: string;
  product_name?: string | null;
  supplier_id?: string | null;
  supplier_name?: string | null;
  supplier_default_lead_time_days?: number | null;
  purchase_price?: number | null;
  selling_price?: number | null;
  lead_time_days?: number | null;
  moq?: number | null;
  pack_size?: number | null;
  safety_stock_override?: number | null;
  notes?: string | null;
  updated_at: string;
};

export type SkuSettingPayload = {
  product_name?: string | null;
  supplier_id?: string | null;
  purchase_price?: number | null;
  selling_price?: number | null;
  lead_time_days?: number | null;
  moq?: number | null;
  pack_size?: number | null;
  safety_stock_override?: number | null;
  notes?: string | null;
};

export type SkuSettingsResponse = {
  status: string;
  items: SkuSetting[];
};

export type ProcurementEnrichResponse = {
  items: Recommendation[];
};

export type WorkspaceSettings = {
  locale: "ru" | "en";
  theme: "light" | "dark" | "system";
  density: "comfortable" | "compact";
  workspaceName: string;
};

export type WorkspaceSettingsResponse = {
  status: string;
  data: WorkspaceSettings;
};

export type CopilotMessage = {
  role: "user" | "assistant";
  text: string;
};

export type CopilotStreamPayload = {
  message: string;
  locale: "ru" | "en";
  selected_sku?: string | null;
  active_page?: string | null;
  context?: Record<string, unknown>;
  conversation?: CopilotMessage[];
};

export type ImportAssistContext = {
  stage: string;
  filename: string;
  columns: string[];
  required_columns_status: Record<string, ColumnPresenceStatus>;
  optional_columns_status: Record<string, ColumnPresenceStatus>;
  suggested_mapping: Record<string, MappingSuggestionItem>;
  validation_errors: MappingWarningResponse[];
  validation_warnings: MappingWarningResponse[];
  warnings: MappingWarningResponse[];
  is_ready_for_analysis: boolean;
  sample_rows: Array<Record<string, string | number | boolean | null>>;
};

export type ImportAssistResponse = {
  answer: string;
  model: string;
  provider: "ollama" | string;
  is_local: boolean;
  fallback: boolean;
  error_code?: string | null;
};

export type AnalysisAssistContext = {
  stage: "analysis";
  summary: {
    filename: string | null;
    period: string | null;
    sku_count: number | null;
    row_count: number | null;
  };
  kpis: Record<string, string | number | boolean | null>;
  top_recommendations: Array<Record<string, string | number | boolean | null>>;
  high_risk_items: Array<Record<string, string | number | boolean | null>>;
  overstock_items: Array<Record<string, string | number | boolean | null>>;
  exceptions: Array<Record<string, string | number | boolean | null>>;
  forecast_quality: Record<string, string | number | boolean | null>;
  data_quality: Record<string, string | number | boolean | null>;
  reliability_warnings: ReliabilityWarning[];
  purchase_plan_decisions: Array<Record<string, string | number | boolean | null>>;
  selected_sku?: Record<string, string | number | boolean | null> | null;
};

export type ActiveTab =
  | "overview"
  | "data_quality"
  | "forecast_lab"
  | "planning"
  | "reliability"
  | "segments"
  | "exceptions"
  | "reports"
  | "history"
  | "ai_copilot"
  | "settings";
