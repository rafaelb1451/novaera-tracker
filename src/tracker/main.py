import structlog
from pathlib import Path
from fastapi import FastAPI, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from tracker.config import get_settings
from tracker.logging import setup_logging
from tracker.api.routes import produtos, auth
from tracker.db.models import Usuario

setup_logging()
log = structlog.get_logger()
settings = get_settings()

# Instancia o FastAPI com os parâmetros nomeados corretamente
app = FastAPI(
    title="Nova Era Tracker API",
    description="API para rastreamento de preços do supermercado Nova Era",
    version="0.1.0",
)

# Middleware de CORS (para o frontend conseguir acessar a API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração de templates (Jinja2) e arquivos estáticos
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Inclui as rotas da API e de Autenticação
app.include_router(auth.router)
app.include_router(produtos.router)

@app.get("/health", tags=["Sistema"])
def health_check():
    return {"status": "ok", "ambiente": settings.environment}

# Rota Principal do Painel (Protegida por Login)
@app.get("/", tags=["Painel"])
def painel_home(
    request: Request, 
    usuario_logado: Usuario = Depends(auth.get_usuario_logado)
):
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"titulo": "Rastreador Nova Era", "usuario": usuario_logado}
    )

@app.get("/partials/produtos", tags=["Painel"])
def partial_produtos(
    request: Request, 
    busca: str = "",
    usuario_logado: Usuario = Depends(auth.get_usuario_logado)
):
    import httpx
    import os
    # Pega a URL base da API (se estiver no Railway, usa o domínio público)
    base_url = os.getenv("RAILWAY_PUBLIC_DOMAIN", "http://localhost:8000")
    r = httpx.get(f"https://{base_url}/api/produtos?busca={busca}&limite=50" if not base_url.startswith("http") else f"{base_url}/api/produtos?busca={busca}&limite=50")
    
    produtos_lista = r.json() if r.status_code == 200 else []
    
    return templates.TemplateResponse(
        request=request, 
        name="partials/tabela_produtos.html", 
        context={"produtos": produtos_lista}
    )

# Handler para redirecionar usuários não logados para a tela de login
@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def custom_401_handler(request: Request, exc):
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)