import time
from datetime import datetime, UTC

import httpx
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from tracker.collectors.base import BaseCollector, CategoriaColetada, ProdutoColetado
from tracker.config import get_settings

log = structlog.get_logger()
settings = get_settings()


class NovaEraCollector(BaseCollector):
    nome_supermercado = "Nova Era"

    def __init__(self) -> None:
        self.base_url = settings.novaera_base_url
        self.headers = {
            "User-Agent": settings.user_agent,
            "Accept": "application/json",
        }
        self.client = httpx.Client(
            headers=self.headers,
            timeout=20.0,
            follow_redirects=True,
        )

    def __del__(self) -> None:
        self.client.close()

    @retry(
        stop=stop_after_attempt(5),  # Tenta até 5 vezes
        wait=wait_exponential(multiplier=2, min=4, max=60), # Espera 4s, 8s, 16s...
        retry=retry_if_exception_type(httpx.HTTPStatusError), # Só tenta de novo em erros HTTP
        reraise=True,
    )
    def _get(self, endpoint: str, params: dict | None = None) -> list | dict:
        """Faz a requisição com retry automático e respeita o tempo de espera."""
        url = f"{self.base_url}{endpoint}"
        log.debug("novaera_request", url=url, params=params)
        
        response = self.client.get(url, params=params)
        
        # Se for 503 ou 429, o retry vai cuidar disso
        response.raise_for_status()
        
        # Delay para não sobrecarregar o servidor
        time.sleep(settings.request_delay_seconds)
        
        return response.json()

    def obter_categorias(self) -> list[CategoriaColetada]:
        """Busca a árvore de categorias e retorna apenas as folhas."""
        log.info("novaera_buscando_categorias")
        arvore = self._get("/api/catalog_system/pub/category/tree/10")
        
        folhas: list[CategoriaColetada] = []
        
        def _percorrer(no: dict, caminho_atual: str) -> None:
            nome = no.get("name", "")
            caminho = f"{caminho_atual} > {nome}" if caminho_atual else nome
            
            if not no.get("hasChildren"):
                folhas.append(
                    CategoriaColetada(
                        id_externo=str(no.get("id")),
                        nome=nome,
                        caminho=caminho,
                        url=no.get("url"),
                    )
                )
            else:
                for filho in no.get("children", []):
                    _percorrer(filho, caminho)

        for raiz in arvore:
            _percorrer(raiz, "")

        log.info("novaera_categorias_encontradas", total=len(folhas))
        return folhas

    def obter_produtos_da_categoria(self, categoria_id: str) -> list[ProdutoColetado]:
        """Busca produtos de uma categoria com paginação."""
        log.info("novaera_buscando_produtos", categoria_id=categoria_id)
        
        produtos: list[ProdutoColetado] = []
        pagina = 0
        
        while pagina < settings.max_paginas_por_categoria:
            params = {
                "fq": f"C:/{categoria_id}/",
                "_from": pagina * 50,
                "_to": (pagina + 1) * 50 - 1,
            }
            
            try:
                dados = self._get("/api/catalog_system/pub/products/search", params)
            except Exception as e:
                log.error("novaera_erro_pagina", categoria_id=categoria_id, pagina=pagina, erro=str(e))
                break

            if not isinstance(dados, list) or not dados:
                break  # Acabaram os produtos desta categoria

            for prod in dados:
                # Um produto pode ter várias variações (items) e vários vendedores (sellers)
                for item in prod.get("items", []):
                    for seller in item.get("sellers", []):
                        oferta = seller.get("commertialOffer", {})
                        preco = oferta.get("Price")
                        
                        if preco is None or preco <= 0:
                            continue

                        produtos.append(
                            ProdutoColetado(
                                product_id=str(prod.get("productId")),
                                sku_id=str(item.get("itemId")),
                                ean=item.get("ean"),
                                nome=prod.get("productName", ""),
                                marca=prod.get("brand"),
                                link=prod.get("link"),
                                categoria_id_externo=categoria_id,
                                preco=float(preco),
                                preco_lista=float(oferta.get("ListPrice") or 0) or None,
                                disponivel=int(oferta.get("AvailableQuantity") or 0),
                                seller=seller.get("sellerName"),
                                coletado_em=datetime.now(UTC),
                            )
                        )
            
            pagina += 1

        log.info("novaera_produtos_coletados", categoria_id=categoria_id, total=len(produtos))
        return produtos