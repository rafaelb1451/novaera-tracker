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
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from tracker.db.session import get_db
from tracker.db.models import Produto, Preco
from typing import Annotated

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
    db: Annotated[Session, Depends(get_db)] = None,
    usuario_logado: Usuario = Depends(auth.get_usuario_logado)
):
    # Mesma lógica da API, mas buscando direto do banco para ser mais rápido no Render
    subq = (
        select(
            Preco.produto_id,
            Preco.preco,
            Preco.preco_lista,
            Preco.tempo,
            Preco.disponivel
        )
        .distinct(Preco.produto_id)
        .order_by(Preco.produto_id, desc(Preco.tempo))
        .subquery()
    )

    stmt = (
        select(Produto, subq.c.preco, subq.c.preco_lista, subq.c.tempo, subq.c.disponivel)
        .join(subq, Produto.id == subq.c.produto_id)
        .order_by(desc(subq.c.tempo))
        .limit(50)
    )

    if busca:
        stmt = stmt.where(Produto.nome.ilike(f"%{busca}%"))

    resultados = db.execute(stmt).all()

    produtos_lista = [
        {
            "nome": p.Produto.nome,
            "marca": p.Produto.marca,
            "preco": float(p.preco) if p.preco else 0.0,
        }
        for p in resultados
    ]
    
    return templates.TemplateResponse(
        request=request, 
        name="partials/tabela_produtos.html", 
        context={"produtos": produtos_lista}
    )

# Handler para redirecionar usuários não logados para a tela de login
@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def custom_401_handler(request: Request, exc):
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)