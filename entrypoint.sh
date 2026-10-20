#!/bin/sh
set -e

echo "Rodando migrações do banco de dados..."
python -m alembic upgrade head

echo "Verificando se o banco precisa ser populado..."
HAS_PRODUTOS=$(python -c "from tracker.db.session import SessionLocal; from tracker.db.models import Produto; db = SessionLocal(); print(db.query(Produto).count() > 0); db.close()" | tail -n 1)

if [ "$HAS_PRODUTOS" = "False" ]; then
  echo "Banco vazio! Iniciando coleta inicial (isso pode levar alguns minutos)..."
  python -m scripts.coletar_agora
else
  echo "Banco já possui dados. Pulando coleta inicial."
fi

echo "Iniciando a aplicação..."
exec uvicorn tracker.main:app --host 0.0.0.0 --port ${PORT:-8000}