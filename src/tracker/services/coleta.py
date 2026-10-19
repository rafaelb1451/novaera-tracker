import structlog
from datetime import datetime, UTC
from sqlalchemy.orm import Session
from sqlalchemy import select

from tracker.db.models import Supermercado, Produto, Preco
from tracker.collectors.novaera import NovaEraCollector

log = structlog.get_logger()

def obter_ou_criar_supermercado(db: Session, nome: str, base_url: str) -> Supermercado:
    """Busca o supermercado no banco ou cria se não existir."""
    sm = db.scalar(select(Supermercado).where(Supermercado.nome == nome))
    if not sm:
        log.info("criando_supermercado", nome=nome)
        sm = Supermercado(nome=nome, base_url=base_url, plataforma="vtex")
        db.add(sm)
        db.commit()
        db.refresh(sm)
    return sm

def processar_e_salvar_produtos(db: Session, supermercado_id: int, produtos_coletados: list):
    """Salva produtos e seus preços no banco."""
    novos = 0
    atualizados = 0

    for p in produtos_coletados:
        # 1. Verifica se o produto já existe (pelo SKU do supermercado)
        produto_db = db.scalar(
            select(Produto).where(
                Produto.supermercado_id == supermercado_id,
                Produto.sku_id_externo == p.sku_id
            )
        )

        if not produto_db:
            # Cria o produto novo
            produto_db = Produto(
                supermercado_id=supermercado_id,
                product_id_externo=p.product_id,
                sku_id_externo=p.sku_id,
                ean=p.ean,
                nome=p.nome,
                marca=p.marca,
                link=p.link,
            )
            db.add(produto_db)
            db.flush() # Gera o ID do produto sem commitar ainda
            novos += 1
        else:
            # Atualiza os dados cadastrais (nome, marca, link) caso tenham mudado
            produto_db.nome = p.nome
            produto_db.marca = p.marca
            produto_db.link = p.link
            atualizados += 1

        # 2. Salva o preço atual
        preco_db = Preco(
            produto_id=produto_db.id,
            tempo=p.coletado_em,
            preco=p.preco,
            preco_lista=p.preco_lista,
            disponivel=p.disponivel,
            seller=p.seller,
        )
        db.add(preco_db)

    db.commit()
    log.info("produtos_salvos", novos=novos, atualizados=atualizados)

def executar_coleta_por_termo(db: Session, termo: str):
    """Orquestra a coleta para um termo de busca específico."""
    log.info("iniciando_coleta", termo=termo)
    
    # 1. Configura o coletor
    coletor = NovaEraCollector()
    sm = obter_ou_criar_supermercado(db, "Nova Era", coletor.base_url)

    # 2. Puxa os dados da API (simulando o Plano B que funcionou)
    dados_brutos = coletor._get("/api/catalog_system/pub/products/search", params={"ft": termo, "_from": 0, "_to": 19})
    
    # 3. Transforma o JSON bruto no nosso DTO ProdutoColetado
    produtos_formatados = []
    for prod in dados_brutos:
        for item in prod.get("items", []):
            for seller in item.get("sellers", []):
                oferta = seller.get("commertialOffer", {})
                preco = oferta.get("Price")
                if preco is None or preco <= 0:
                    continue
                
                from tracker.collectors.base import ProdutoColetado
                produtos_formatados.append(
                    ProdutoColetado(
                        product_id=str(prod.get("productId")),
                        sku_id=str(item.get("itemId")),
                        ean=item.get("ean"),
                        nome=prod.get("productName", ""),
                        marca=prod.get("brand"),
                        link=prod.get("link"),
                        categoria_id_externo=None,
                        preco=float(preco),
                        preco_lista=float(oferta.get("ListPrice") or 0) or None,
                        disponivel=int(oferta.get("AvailableQuantity") or 0),
                        seller=seller.get("sellerName"),
                        coletado_em=datetime.now(UTC),
                    )
                )

    # 4. Salva no banco
    if produtos_formatados:
        processar_e_salvar_produtos(db, sm.id, produtos_formatados)
    
    log.info("coleta_finalizada", termo=termo, total=len(produtos_formatados))