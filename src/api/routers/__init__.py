from src.api.routers.analysis import router as analysis_router
from src.api.routers.copilot import router as copilot_router
from src.api.routers.files import router as files_router
from src.api.routers.history import router as history_router
from src.api.routers.imports import router as import_router
from src.api.routers.procurement import router as procurement_router
from src.api.routers.settings import router as settings_router
from src.api.routers.system import router as system_router

__all__ = [
    "analysis_router",
    "copilot_router",
    "files_router",
    "history_router",
    "import_router",
    "procurement_router",
    "settings_router",
    "system_router",
]
