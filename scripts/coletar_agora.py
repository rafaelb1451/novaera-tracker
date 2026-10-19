import structlog
from tracker.logging import setup_logging
from tracker.db.session import SessionLocal
from tracker.services.coleta import executar_coleta_por_termo

def main():
    setup_logging()
    log = structlog.get_logger()
    
    termos_para_coletar = ["arroz", "feijao", "leite", "cafe", "oleo"]
    
    log.info("Iniciando rotina de coleta", total_termos=len(termos_para_coletar))
    
    db = SessionLocal()
    try:
        for termo in termos_para_coletar:
            try:
                executar_coleta_por_termo(db, termo)
            except Exception as e:
                log.error("erro_ao_coletar_termo", termo=termo, erro=str(e))
                # O ideal aqui é não parar a coleta toda se um termo falhar
    finally:
        db.close()
        
    log.info("Rotina de coleta finalizada")

if __name__ == "__main__":
    main()