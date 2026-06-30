from fastapi import FastAPI

from app.api.middleware import log_request_middleware
from app.api.routes.alerts import router as alerts_router
from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.rag import router as rag_router
from app.api.routes.stream import router as stream_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.websocket_tasks import router as websocket_tasks_router


app = FastAPI(
    title="Thesis Defense Agent API",
    version="0.1.0",
)

app.middleware("http")(log_request_middleware)

app.include_router(alerts_router)
app.include_router(documents_router)
app.include_router(health_router)
app.include_router(rag_router)
app.include_router(stream_router)
app.include_router(tasks_router)
app.include_router(websocket_tasks_router)
