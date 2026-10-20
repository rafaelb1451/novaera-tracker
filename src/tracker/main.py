import structlog
from pathlib import Path
from typing import Annotated
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session

from tracker.config import get_settings
from tracker.logging import setup_logging
from tracker.api.routes import produtos
from tracker.db.session import get_db
from tracker.db.models import Produto, Preco

setup_logging()
log = structlog.get_logger()
settings = get_settings()

app = FastAPI(title="Nova Era Tracker API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(produtos.router)

@app.get("/health", tags=["Sistema"])
def health_check():
    return {"status": "ok", "ambiente": settings.environment}

@app.get("/", tags=["Painel"])
def painel_home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"titulo": "Rastreador Nova Era"})

@app.get("/partials/produtos", tags=["Painel"])
def partial_produtos(request: Request, busca: str = "", db: Session = Depends(get_db)):
    subq = (
        select(Preco.produto_id, Preco.preco, Preco.preco_lista, Preco.tempo, Preco.disponivel)
        .distinct(Preco.produto_id)
        .order_by(Preco.produto_id, desc(Preco.tempo))
        .subquery()
    )

    stmt = select(Produto, subq.c.preco, subq.c.preco_lista).join(subq, Produto.id == subq.c.produto_id)

    if busca:
        # Se o usuário digitou algo, busca normal e ordena por data
        stmt = stmt.where(Produto.nome.ilike(f"%{busca}%")).order_by(desc(subq.c.tempo))
    else:
        # Se a busca estiver vazia, traz 12 produtos aleatórios
        stmt = stmt.order_by(func.random()).limit(12)

    resultados = db.execute(stmt).all()

    produtos_lista = [
        {
            "nome": p.Produto.nome,
            "marca": p.Produto.marca,
            "imagem_url": p.Produto.imagem_url,
            "preco": float(p.preco) if p.preco else 0.0,
        }
        for p in resultados
    ]
    
    return templates.TemplateResponse(
        request=request, name="partials/tabela_produtos.html", context={"produtos": produtos_lista}
    )