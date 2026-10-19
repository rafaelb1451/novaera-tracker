from typing import Annotated
from fastapi import APIRouter, Depends, Form, Request, Response, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session

from tracker.db.session import get_db
from tracker.db.models import Usuario
from tracker.core.security import verificar_senha, criar_cookie_sessao, ler_cookie_sessao

router = APIRouter(tags=["Autenticação"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# --- DEPENDÊNCIA DE PROTEÇÃO ---
def get_usuario_logado(request: Request, db: Session = Depends(get_db)) -> Usuario:
    """Verifica se o usuário está logado através do cookie."""
    token = request.cookies.get("sessao")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado")
    
    usuario_id = ler_cookie_sessao(token)
    if not usuario_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão expirada")

    usuario = db.scalar(select(Usuario).where(Usuario.id == usuario_id, Usuario.ativo == True))
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inválido")
    
    return usuario

# --- ROTAS ---

@router.get("/login", response_class=HTMLResponse)
def tela_login(request: Request):
    return templates.TemplateResponse(request=request, name="auth/login.html")

@router.post("/login")
def fazer_login(
    request: Request,
    email: Annotated[str, Form()],
    senha: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    # Busca o usuário
    usuario = db.scalar(select(Usuario).where(Usuario.email == email))
    
    # Valida credenciais
    if not usuario or not verificar_senha(senha, usuario.senha_hash):
        return templates.TemplateResponse(
            request=request, 
            name="auth/login.html", 
            context={"erro": "E-mail ou senha incorretos."}
        )
    
    # Cria a resposta redirecionando para o painel
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    # Define o cookie HttpOnly (não acessível via JS, mais seguro)
    token = criar_cookie_sessao(usuario.id)
    response.set_cookie(
        key="sessao", 
        value=token, 
        httponly=True, 
        max_age=86400, # 1 dia
        samesite="lax"
    )
    
    # Atualiza o último login
    from datetime import datetime, UTC
    usuario.ultimo_login_em = datetime.now(UTC)
    db.commit()
    
    return response

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("sessao")
    return response