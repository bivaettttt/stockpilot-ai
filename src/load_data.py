from pathlib import Path

import pandas as pd

SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}
CSV_ENCODINGS = ("utf-8-sig", "utf-8", "cp1251")


def load_sales_data(file_path: str | Path) -> pd.DataFrame:
    """
    Загружает файл с продажами и остатками.

    Поддерживаемые форматы:
    - CSV
    - XLSX

    Возвращает pandas.DataFrame.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")

    suffix = path.suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Неподдерживаемый формат файла: {path.suffix}. "
            f"Поддерживаются: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    if suffix == ".csv":
        df = _read_csv_with_fallbacks(path)

    elif suffix == ".xlsx":
        df = pd.read_excel(path, engine="openpyxl")

    else:
        raise ValueError(f"Не удалось обработать файл: {path}")

    return df


def _read_csv_with_fallbacks(path: Path) -> pd.DataFrame:
    last_error: Exception | None = None

    for encoding in CSV_ENCODINGS:
        try:
            return pd.read_csv(path, encoding=encoding, sep=None, engine="python")
        except Exception as error:
            last_error = error

    if last_error is not None:
        raise ValueError(
            "Не удалось прочитать CSV-файл. Проверьте кодировку и разделитель."
        ) from last_error

    raise ValueError("Не удалось прочитать CSV-файл.")
