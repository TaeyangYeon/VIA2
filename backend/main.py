from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.routers.engine import router as engine_router
from backend.routers.images import router as images_router

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


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.version}
