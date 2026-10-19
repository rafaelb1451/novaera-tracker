from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from tracker.db.session import get_db
from tracker.db.models import Produto, Preco

router = APIRouter(prefix="/api/produtos", tags=["Produtos"])


@router.get("")
def listar_produtos(
    db: Annotated[Session, Depends(get_db)],
    limite: int = Query(20, ge=1, le=100),
    busca: str | None = Query(None, description="Filtrar pelo nome do produto"),
):
    """Lista os produtos cadastrados e traz o preço mais recente de cada um."""
    
    # Faz um JOIN com a tabela de preços e pega o preço mais recente
    # (A subquery garante que pegamos apenas o último preço registrado)
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
        .limit(limite)
    )

    if busca:
        stmt = stmt.where(Produto.nome.ilike(f"%{busca}%"))

    resultados = db.execute(stmt).all()

    # Formata a resposta para o frontend
    return [
        {
            "id": p.Produto.id,
            "nome": p.Produto.nome,
            "marca": p.Produto.marca,
            "ean": p.Produto.ean,
            "preco": float(p.preco) if p.preco else None,
            "preco_lista": float(p.preco_lista) if p.preco_lista else None,
            "tempo": p.tempo.isoformat() if p.tempo else None,
            "disponivel": p.disponivel,
        }
        for p in resultados
    ]