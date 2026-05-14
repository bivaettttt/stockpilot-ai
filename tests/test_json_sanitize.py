import math

import numpy as np

from src.api.json_sanitize import sanitize_json_value


def test_sanitize_replaces_nan_inf_in_nested_structures() -> None:
    raw = {"a": float("nan"), "b": {"c": float("inf")}, "d": [1.0, np.float64("nan")]}
    out = sanitize_json_value(raw)
    assert out["a"] is None
    assert out["b"]["c"] is None
    assert out["d"] == [1.0, None]


def test_sanitize_preserves_plain_numbers() -> None:
    assert sanitize_json_value(42) == 42
    assert sanitize_json_value(3.5) == 3.5
