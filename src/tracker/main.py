import structlog
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from tracker.config import get_settings
from tracker.logging import setup_logging
from tracker.api.routes import produtos

setup_logging()
log = structlog.get_logger()
settings = get_settings()

app = FastAPI(
    title="Nova Era Tracker API",
    description="API para rastreamento de preços do supermercado Nova Era",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração do Jinja2 e arquivos estáticos
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Inclui a API
app.include_router(produtos.router)

@app.get("/health", tags=["Sistema"])
def health_check():
    return {"status": "ok", "ambiente": settings.environment}

# NOVO: Rota para renderizar o painel (HTML)
@app.get("/", tags=["Painel"])
def painel_home(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"titulo": "Rastreador Nova Era"}
    )

# NOVO: Rota HTMX que retorna apenas o HTML da tabela
@app.get("/partials/produtos", tags=["Painel"])
def partial_produtos(request: Request, busca: str = ""):
    # Para simplificar, vamos chamar a nossa própria API via requisição interna
    # (Em produção faríamos a query direto no banco, mas para reuso está ok)
    import httpx
    
    # Faz a requisição para a rota /api/produtos que já criamos
    r = httpx.get(f"http://localhost:8000/api/produtos?busca={busca}&limite=50")
    produtos = r.json() if r.status_code == 200 else []
    
    return templates.TemplateResponse(
        request=request, 
        name="partials/tabela_produtos.html", 
        context={"produtos": produtos}
    )