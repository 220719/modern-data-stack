from loguru import logger
from src.ingestion.infodengue import coletar_todos
from src.ingestion.openmeteo import coletar_clima_todos
from src.storage.database import inicializar_banco, inserir_casos, inserir_clima


def executar_pipeline(
    ano_start: int = 2020,
    ano_end: int = 2025,
    data_inicio: str = "2020-01-01",
    data_fim: str = "2025-12-31",
) -> dict:
    logger.info("=" * 60)
    logger.info("INICIANDO PIPELINE DE INGESTÃO")
    logger.info("=" * 60)

    # 1. Inicializa banco
    inicializar_banco()

    # 2. Coleta casos
    logger.info("Coletando dados de casos (InfoDengue)...")
    casos = coletar_todos(ano_start=ano_start, ano_end=ano_end)
    n_casos = inserir_casos(casos)

    # 3. Coleta clima
    logger.info("Coletando dados de clima (OpenMeteo)...")
    clima = coletar_clima_todos(data_inicio=data_inicio, data_fim=data_fim)
    n_clima = inserir_clima(clima)

    resultado = {
        "casos_inseridos": n_casos,
        "clima_inseridos": n_clima,
    }

    logger.info("=" * 60)
    logger.success(f"PIPELINE CONCLUÍDO: {resultado}")
    logger.info("=" * 60)

    return resultado


if __name__ == "__main__":
    executar_pipeline()