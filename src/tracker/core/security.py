from datetime import datetime, timedelta, UTC
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from passlib.context import CryptContext
from tracker.config import get_settings

settings = get_settings()

# Contexto para gerar e verificar hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def gerar_hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)

def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    return pwd_context.verify(senha_plana, senha_hash)

# Serializador para assinar o Cookie de sessão
serializer = URLSafeTimedSerializer(settings.api_secret_key)

def criar_cookie_sessao(usuario_id: int) -> str:
    """Cria um token assinado contendo o ID do usuário."""
    return serializer.dumps({"usuario_id": usuario_id})

def ler_cookie_sessao(token: str, max_age_seconds: int = 86400) -> int | None:
    """Lê o token e retorna o ID do usuário, ou None se for inválido/expirado."""
    try:
        dados = serializer.loads(token, max_age=max_age_seconds)
        return dados.get("usuario_id")
    except (BadSignature, SignatureExpired):
        return None