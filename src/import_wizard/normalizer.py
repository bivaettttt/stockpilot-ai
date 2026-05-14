from __future__ import annotations

from io import BytesIO

import pandas as pd

from src.domain.constants import BOOLEAN_COLUMNS, NUMERIC_COLUMNS, OPTIONAL_COLUMNS, REQUIRED_COLUMNS


def normalize_dataset(
    raw_df: pd.DataFrame,
    mapping: dict[str, dict[str, object]],
) -> pd.DataFrame:
    rename_map = {
        payload["source_column"]: field
        for field, payload in mapping.items()
        if payload.get("source_column")
    }
    selected_columns = list(rename_map.keys())
    normalized_df = raw_df[selected_columns].rename(columns=rename_map).copy()

    for field in [*REQUIRED_COLUMNS, *OPTIONAL_COLUMNS]:
        if field not in normalized_df.columns:
            normalized_df[field] = None

    normalized_df = normalized_df[[*REQUIRED_COLUMNS, *OPTIONAL_COLUMNS]]

    normalized_df["date"] = pd.to_datetime(normalized_df["date"], errors="coerce").dt.strftime("%Y-%m-%d")

    for field in NUMERIC_COLUMNS:
        if field in normalized_df.columns:
            normalized_df[field] = pd.to_numeric(normalized_df[field], errors="coerce")

    for field in {"sku", "product_name", "category", "supplier"}:
        if field in normalized_df.columns:
            normalized_df[field] = normalized_df[field].fillna("").astype(str).str.strip()

    for field in BOOLEAN_COLUMNS:
        if field in normalized_df.columns:
            normalized_df[field] = normalized_df[field].map(_normalize_boolean_value)

    return normalized_df


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    df.to_csv(buffer, index=False, encoding="utf-8-sig")
    return buffer.getvalue()


def _normalize_boolean_value(value: object) -> bool | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "y", "да", "акция", "promo", "promо"}:
        return True
    if normalized in {"false", "0", "no", "n", "нет"}:
        return False
    return None
