FROM python:3.11-slim

# Impede o Python de gerar arquivos .pyc e permite logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependências do sistema necessárias para o psycopg2 (Postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos de dependência
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY src/tracker/static/ ./src/tracker/static/
COPY src/tracker/templates/ ./src/tracker/templates/
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY scripts/ ./scripts/

# Instala as dependências do projeto
RUN pip install --no-cache-dir .

# Expõe a porta que o Railway usa (ele injeta a variável $PORT)
EXPOSE 8000

# Comando para rodar a aplicação em produção
CMD uvicorn tracker.main:app --host 0.0.0.0 --port ${PORT:-8000}