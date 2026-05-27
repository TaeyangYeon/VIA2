from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.routers.engine import router as engine_router
from backend.routers.images import router as images_router
from backend.routers.roi import router as roi_router
from backend.routers.config import router as config_router
from backend.routers.directives import router as directives_router
from backend.routers.execute import router as execute_router
from backend.routers.logs import router as logs_router
from backend.routers.light_test import router as light_test_router

app = FastAPI(title=settings.app_name, version=settings.version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(engine_router, prefix="/api")
app.include_router(images_router, prefix="/api")
app.include_router(roi_router, prefix="/api")
app.include_router(config_router, prefix="/api")
app.include_router(directives_router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(execute_router, prefix="/api")
app.include_router(light_test_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.version}
