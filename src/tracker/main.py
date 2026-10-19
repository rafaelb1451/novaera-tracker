import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tracker.api.routes import produtos
from tracker.config import get_settings
from tracker.logging import setup_logging

setup_logging()
log = structlog.get_logger()
settings = get_settings()

app = FastAPI(
    title="Nova Era Tracker API",
    description="API para rastreamento de preços do supermercado Nova Era",
    version="0.1.0",
)

# Permite que o frontend (rodando em outra porta/domínio) acesse a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, trocar pelo domínio real do painel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Sistema"])
def health_check():
    """Endpoint simples para verificar se a API está no ar."""
    return {"status": "ok", "ambiente": settings.environment}

app.include_router(produtos.router)