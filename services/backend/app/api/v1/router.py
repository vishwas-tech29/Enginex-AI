from fastapi import APIRouter

from app.api.v1.auth.routes import router as auth_router
from app.api.v1.projects.routes import router as projects_router
from app.api.v1.cad.routes import router as cad_router
from app.api.v1.pcb.routes import router as pcb_router
from app.api.v1.ai.routes import router as ai_router
from app.api.v1.files.routes import router as files_router
from app.api.v1.users.routes import router as users_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(projects_router)
router.include_router(cad_router)
router.include_router(pcb_router)
router.include_router(ai_router)
router.include_router(files_router)
router.include_router(users_router)
