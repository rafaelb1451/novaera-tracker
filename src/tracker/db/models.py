from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tracker.db.base import Base


class Supermercado(Base):
    __tablename__ = "supermercados"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    base_url: Mapped[str] = mapped_column(String(255), nullable=False)
    plataforma: Mapped[str] = mapped_column(String(50), nullable=False, default="vtex")
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    categorias: Mapped[list["Categoria"]] = relationship(back_populates="supermercado")
    produtos: Mapped[list["Produto"]] = relationship(back_populates="supermercado")


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    papel: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ultimo_login_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Categoria(Base):
    __tablename__ = "categorias"
    __table_args__ = (
        UniqueConstraint("supermercado_id", "categoria_externa_id", name="uq_cat_sm_externo"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supermercado_id: Mapped[int] = mapped_column(
        ForeignKey("supermercados.id", ondelete="CASCADE"), nullable=False
    )
    categoria_externa_id: Mapped[str] = mapped_column(String(50), nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    caminho: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    supermercado: Mapped["Supermercado"] = relationship(back_populates="categorias")
    produtos: Mapped[list["Produto"]] = relationship(back_populates="categoria")


class Produto(Base):
    __tablename__ = "produtos"
    __table_args__ = (
        UniqueConstraint("supermercado_id", "sku_id_externo", name="uq_prod_sm_sku"),
        Index("idx_produtos_ean", "ean"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    supermercado_id: Mapped[int] = mapped_column(
        ForeignKey("supermercados.id", ondelete="CASCADE"), nullable=False
    )
    categoria_id: Mapped[int | None] = mapped_column(
        ForeignKey("categorias.id", ondelete="SET NULL"), nullable=True
    )
    product_id_externo: Mapped[str] = mapped_column(String(50), nullable=False)
    sku_id_externo: Mapped[str] = mapped_column(String(50), nullable=False)
    ean: Mapped[str | None] = mapped_column(String(20), nullable=True)
    nome: Mapped[str] = mapped_column(Text, nullable=False)
    marca: Mapped[str | None] = mapped_column(String(255), nullable=True)
    link: Mapped[str | None] = mapped_column(Text, nullable=True)
    imagem_url: Mapped[str | None] = mapped_column(Text, nullable=True) # <-- NOVA COLUNA
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    supermercado: Mapped["Supermercado"] = relationship(back_populates="produtos")
    categoria: Mapped["Categoria | None"] = relationship(back_populates="produtos")
    precos: Mapped[list["Preco"]] = relationship(
        back_populates="produto", cascade="all, delete-orphan"
    )


class Preco(Base):
    __tablename__ = "precos"
    __table_args__ = (
        Index("idx_precos_produto_tempo", "produto_id", "tempo"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id", ondelete="CASCADE"), nullable=False
    )
    tempo: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    preco: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    preco_lista: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    disponivel: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    seller: Mapped[str | None] = mapped_column(String(100), nullable=True)

    produto: Mapped["Produto"] = relationship(back_populates="precos")
