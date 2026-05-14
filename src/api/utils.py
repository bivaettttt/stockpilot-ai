import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
from fastapi import UploadFile

from src.domain.constants import (
    ALLOWED_FILE_EXTENSIONS,
    API_OUTPUT_DIR,
    MAX_UPLOAD_SIZE_BYTES,
    UPLOAD_DIR,
)


@dataclass(frozen=True)
class SavedUpload:
    path: Path
    original_filename: str
    safe_filename: str
    file_hash: str
    size_bytes: int


def ensure_api_dirs() -> None:
    """
    Создаёт директории для API-загрузок и API-результатов.
    """
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    API_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_safe_filename(filename: str) -> str:
    """
    Простейшая очистка имени файла.

    Для MVP достаточно убрать потенциально проблемные символы.
    """
    safe_name = filename.replace("/", "_").replace("\\", "_").strip()

    if not safe_name:
        safe_name = "uploaded_file.csv"

    return safe_name


def validate_upload_extension(filename: str) -> None:
    """
    Проверяет расширение загружаемого файла.
    """
    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_FILE_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_FILE_EXTENSIONS))
        raise ValueError(
            f"Неподдерживаемый формат файла '{suffix or 'без расширения'}'. "
            f"Загрузите файл в формате: {allowed}."
        )


async def save_upload_file(upload_file: UploadFile) -> Path:
    """
    Сохраняет загруженный файл в data/uploads.
    """
    return (await save_upload_file_with_metadata(upload_file)).path


async def save_upload_file_with_metadata(upload_file: UploadFile) -> SavedUpload:
    """
    Сохраняет загруженный файл и возвращает метаданные для аудита и кэширования.
    """
    ensure_api_dirs()

    original_filename = upload_file.filename or "uploaded_file.csv"
    safe_filename = get_safe_filename(original_filename)
    validate_upload_extension(safe_filename)

    content = await upload_file.read()

    if not content:
        raise ValueError("Загруженный файл пустой.")

    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise ValueError(
            f"Размер файла превышает допустимый лимит {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} МБ."
        )

    file_hash = hashlib.sha256(content).hexdigest()
    unique_name = f"{Path(safe_filename).stem}_{uuid4().hex[:8]}{Path(safe_filename).suffix.lower()}"
    file_path = UPLOAD_DIR / unique_name

    file_path.write_bytes(content)

    return SavedUpload(
        path=file_path,
        original_filename=original_filename,
        safe_filename=unique_name,
        file_hash=file_hash,
        size_bytes=len(content),
    )


def dataframe_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Конвертирует DataFrame в JSON-friendly список словарей.
    """
    if df.empty:
        return []

    prepared_df = df.copy()

    for column in prepared_df.columns:
        if pd.api.types.is_datetime64_any_dtype(prepared_df[column]):
            prepared_df[column] = prepared_df[column].dt.strftime("%Y-%m-%d")

    prepared_df = prepared_df.replace([float("inf"), float("-inf")], None)
    prepared_df = prepared_df.where(pd.notnull(prepared_df), None)

    return prepared_df.to_dict(orient="records")
