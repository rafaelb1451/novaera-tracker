from tracker.db.session import SessionLocal
from tracker.db.models import Usuario
from tracker.core.security import gerar_hash_senha

def main():
    db = SessionLocal()
    try:
        # Verifica se já existe
        if db.query(Usuario).filter(Usuario.email == "admin@admin.com").first():
            print("Usuário admin já existe.")
            return

        admin = Usuario(
            email="admin@admin.com",
            senha_hash=gerar_hash_senha("admin123"), # Troque isso depois!
            papel="admin",
            ativo=True
        )
        db.add(admin)
        db.commit()
        print("✅ Usuário admin criado! Login: admin@admin.com | Senha: admin123")
    finally:
        db.close()

if __name__ == "__main__":
    main()