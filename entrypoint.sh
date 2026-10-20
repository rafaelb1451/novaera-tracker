#!/bin/sh
set -e

echo "Rodando migrações do banco de dados..."
python -m alembic upgrade head

echo "Criando usuário administrador (se não existir)..."
python -m scripts.criar_admin

echo "Iniciando a aplicação..."
exec uvicorn tracker.main:app --host 0.0.0.0 --port ${PORT:-8000}