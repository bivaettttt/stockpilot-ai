from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from src.api.templates import ensure_template_file
from src.domain.constants import API_OUTPUT_DIR

router = APIRouter(tags=["Files"])


@router.get("/files/template")
def download_template() -> FileResponse:
    template_path = ensure_template_file()
    return FileResponse(
        path=template_path,
        filename=template_path.name,
        media_type="text/csv",
    )


@router.get("/files/demo")
def download_demo_file() -> FileResponse:
    demo_path = Path("data/input/sample_sales.csv")
    if not demo_path.exists():
        raise HTTPException(status_code=404, detail="Demo-файл не найден.")

    return FileResponse(
        path=demo_path,
        filename=demo_path.name,
        media_type="text/csv",
    )


@router.get("/files/report/{filename}")
def download_report(filename: str) -> FileResponse:
    file_path = resolve_api_output_file(filename)
    if file_path.suffix != ".xlsx":
        raise HTTPException(
            status_code=400,
            detail="Можно скачивать только .xlsx отчёты через этот endpoint.",
        )

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/files/dashboard/{filename}")
def download_dashboard(filename: str) -> FileResponse:
    file_path = resolve_api_output_file(filename)
    if file_path.suffix != ".html":
        raise HTTPException(
            status_code=400,
            detail="Можно открывать только .html дашборды через этот endpoint.",
        )

    return FileResponse(path=file_path, filename=file_path.name, media_type="text/html")


@router.get("/files/recommendations/{filename}")
def download_recommendations_csv(filename: str) -> FileResponse:
    file_path = resolve_api_output_file(filename)
    if file_path.suffix != ".csv":
        raise HTTPException(
            status_code=400,
            detail="Можно скачивать только .csv рекомендации через этот endpoint.",
        )

    return FileResponse(path=file_path, filename=file_path.name, media_type="text/csv")


@router.get("/files/recommendations-raw/{filename}")
def download_recommendations_raw_csv(filename: str) -> FileResponse:
    file_path = resolve_api_output_file(filename)
    if file_path.suffix != ".csv":
        raise HTTPException(
            status_code=400,
            detail="Можно скачивать только .csv рекомендации через этот endpoint.",
        )

    return FileResponse(path=file_path, filename=file_path.name, media_type="text/csv")


@router.get("/files/abc-xyz/{filename}")
def download_abc_xyz_matrix_csv(filename: str) -> FileResponse:
    file_path = resolve_api_output_file(filename)
    if file_path.suffix != ".csv":
        raise HTTPException(
            status_code=400,
            detail="Можно скачивать только .csv ABC/XYZ-матрицу через этот endpoint.",
        )

    return FileResponse(path=file_path, filename=file_path.name, media_type="text/csv")


def resolve_api_output_file(filename: str) -> Path:
    safe_filename = Path(filename).name
    file_path = API_OUTPUT_DIR / safe_filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Файл не найден.")

    return file_path
