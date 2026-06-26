from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.rag import router as rag_router


app = FastAPI(
    title="Thesis Defense Agent API",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(rag_router)
