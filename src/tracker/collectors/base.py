from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CategoriaColetada:
    id_externo: str
    nome: str
    caminho: str
    url: str | None = None


@dataclass
class ProdutoColetado:
    product_id: str
    sku_id: str
    ean: str | None
    nome: str
    marca: str | None
    link: str | None
    categoria_id_externo: str | None
    preco: float
    preco_lista: float | None
    disponivel: int
    seller: str | None
    coletado_em: datetime


class BaseCollector(ABC):
    """Interface que todo coletor de supermercado deve implementar."""
    
    nome_supermercado: str

    @abstractmethod
    def obter_categorias(self) -> list[CategoriaColetada]:
        """Retorna a lista de categorias-folha do supermercado."""
        pass

    @abstractmethod
    def obter_produtos_da_categoria(self, categoria_id: str) -> list[ProdutoColetado]:
        """Retorna todos os produtos de uma categoria específica."""
        pass