from __future__ import annotations

from pathlib import Path

REQUIRED_COLUMNS = [
    "date",
    "sku",
    "product_name",
    "quantity_sold",
    "revenue",
    "stock_on_hand",
]

OPTIONAL_COLUMNS = [
    "category",
    "purchase_price",
    "selling_price",
    "supplier",
    "promotion_flag",
]

NUMERIC_COLUMNS = [
    "quantity_sold",
    "revenue",
    "stock_on_hand",
    "purchase_price",
    "selling_price",
]

TEXT_COLUMNS = [
    "sku",
    "product_name",
    "category",
    "supplier",
]

BOOLEAN_COLUMNS = [
    "promotion_flag",
]

DEFAULT_CATEGORY = "Без категории"
DEFAULT_SERVICE_LEVEL = 0.95
DEFAULT_HISTORY_PAGE_SIZE = 10
MAX_HISTORY_PAGE_SIZE = 100
MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024

UPLOAD_DIR = Path("data/uploads")
API_OUTPUT_DIR = Path("data/output/api")
TEMPLATE_DIR = Path("data/templates")
HISTORY_JSON_FILE = API_OUTPUT_DIR / "history.json"
HISTORY_DB_FILE = API_OUTPUT_DIR / "history.db"

ALLOWED_FILE_EXTENSIONS = {".csv", ".xlsx"}

PRIORITY_ORDER = {
    "critical": 1,
    "high": 2,
    "medium": 3,
    "low": 4,
    "info": 5,
}

