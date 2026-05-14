"""Guarantees JSON-compatible payloads (NaN/Inf break browser JSON parsing)."""

from __future__ import annotations

import math
import numbers
from typing import Any


def sanitize_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: sanitize_json_value(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [sanitize_json_value(item) for item in value]
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, numbers.Real):
        coerced = float(value)
        if math.isnan(coerced) or math.isinf(coerced):
            return None
        return coerced
    return value
