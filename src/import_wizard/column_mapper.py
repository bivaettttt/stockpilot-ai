from __future__ import annotations

import re
from difflib import SequenceMatcher

from src.import_wizard.schema import (
    CANONICAL_COLUMN_ORDER,
    CANONICAL_FIELD_LABELS,
    COLUMN_SYNONYMS,
    MappingCandidate,
)


def normalize_column_name(name: str) -> str:
    normalized = name.strip().lower().replace("ё", "е")
    normalized = normalized.replace("_", " ").replace("-", " ")
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def suggest_mapping(columns: list[str]) -> tuple[dict[str, MappingCandidate], list[dict[str, str | None]]]:
    source_columns = list(columns)
    available_columns = {
        column: normalize_column_name(column)
        for column in source_columns
    }
    candidates_by_field = {
        field: _find_best_candidate(field, source_columns, available_columns)
        for field in CANONICAL_COLUMN_ORDER
    }

    assignments: dict[str, MappingCandidate] = {}
    used_source_columns: set[str] = set()
    warnings: list[dict[str, str | None]] = []

    ranked_candidates = sorted(
        candidates_by_field.values(),
        key=lambda candidate: candidate.confidence,
        reverse=True,
    )

    for candidate in ranked_candidates:
        if candidate.source_column is None:
            assignments[candidate.canonical_field] = candidate
            continue

        if candidate.source_column in used_source_columns:
            warnings.append(
                {
                    "code": "mapping_conflict",
                    "field": candidate.canonical_field,
                    "title": f"Есть конфликт по полю «{CANONICAL_FIELD_LABELS[candidate.canonical_field]}»",
                    "message": (
                        f"Колонка «{candidate.source_column}» подходит сразу для нескольких полей. "
                        "Проверьте сопоставление вручную."
                    ),
                    "suggestion": "Выберите для каждого поля отдельную колонку из вашего файла.",
                }
            )
            assignments[candidate.canonical_field] = MappingCandidate(
                canonical_field=candidate.canonical_field,
                source_column=None,
                confidence=0.0,
                status="missing",
            )
            continue

        used_source_columns.add(candidate.source_column)
        assignments[candidate.canonical_field] = candidate
        if candidate.status == "uncertain":
            warnings.append(
                {
                    "code": "low_confidence_mapping",
                    "field": candidate.canonical_field,
                    "title": f"Проверьте колонку «{CANONICAL_FIELD_LABELS[candidate.canonical_field]}»",
                    "message": (
                        f"Мы предполагаем, что колонка «{candidate.source_column}» соответствует "
                        f"{candidate.canonical_field}, но уверенность ниже обычной."
                    ),
                    "suggestion": "Проверьте сопоставление перед запуском анализа.",
                }
            )

    for field in CANONICAL_COLUMN_ORDER:
        assignments.setdefault(
            field,
            MappingCandidate(
                canonical_field=field,
                source_column=None,
                confidence=0.0,
                status="missing",
            ),
        )

    return assignments, warnings


def _find_best_candidate(
    canonical_field: str,
    source_columns: list[str],
    available_columns: dict[str, str],
) -> MappingCandidate:
    normalized_canonical = normalize_column_name(canonical_field)
    normalized_synonyms = [normalize_column_name(value) for value in COLUMN_SYNONYMS[canonical_field]]
    best_source: str | None = None
    best_confidence = 0.0

    for source_column in source_columns:
        normalized_source = available_columns[source_column]
        if normalized_source == normalized_canonical:
            return MappingCandidate(canonical_field, source_column, 1.0, "matched")

        if normalized_source in normalized_synonyms:
            return MappingCandidate(canonical_field, source_column, 0.98, "matched")

        similarity = max(
            SequenceMatcher(None, normalized_source, synonym).ratio()
            for synonym in [normalized_canonical, *normalized_synonyms]
        )
        if similarity > best_confidence:
            best_confidence = similarity
            best_source = source_column

    if best_source is None or best_confidence < 0.72:
        return MappingCandidate(canonical_field, None, 0.0, "missing")

    status = "matched" if best_confidence >= 0.85 else "uncertain"
    return MappingCandidate(canonical_field, best_source, round(best_confidence, 2), status)
