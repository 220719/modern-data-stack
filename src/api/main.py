from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.storage.database import query
from src.ingestion.infodengue import MUNICIPIOS, DOENCAS

app = FastAPI(
    title="Arboviroses Brasil API",
    description="API de vigilância epidemiológica — dengue, chikungunya e zika",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/municipios")
def listar_municipios():
    return {"municipios": list(MUNICIPIOS.keys())}


@app.get("/doencas")
def listar_doencas():
    return {"doencas": list(DOENCAS.keys())}


@app.get("/historico/{municipio}/{doenca}")
def historico(municipio: str, doenca: str, limit: int = 104):
    if municipio not in MUNICIPIOS:
        raise HTTPException(status_code=404, detail=f"Município '{municipio}' não encontrado")
    if doenca not in DOENCAS:
        raise HTTPException(status_code=404, detail=f"Doença '{doenca}' não encontrada")

    df = query(f"""
        SELECT
            ano,
            semana,
            semana_epidemiologica,
            data_inicio_se,
            casos_estimados,
            casos_confirmados,
            nivel_alerta,
            media_movel_4s
        FROM mart_arboviroses
        WHERE municipio = '{municipio}'
          AND doenca    = '{doenca}'
        ORDER BY semana_epidemiologica DESC
        LIMIT {limit}
    """)

    return {
        "municipio": municipio,
        "doenca":    doenca,
        "registros": df.to_dict(orient="records"),
    }


@app.get("/alertas")
def alertas(nivel_minimo: int = 3):
    df = query(f"""
        SELECT
            municipio,
            doenca,
            ano,
            semana,
            casos_estimados,
            nivel_alerta
        FROM mart_arboviroses
        WHERE nivel_alerta >= {nivel_minimo}
        ORDER BY semana_epidemiologica DESC, nivel_alerta DESC
        LIMIT 50
    """)

    return {
        "nivel_minimo": nivel_minimo,
        "total":        len(df),
        "alertas":      df.to_dict(orient="records"),
    }


@app.get("/resumo")
def resumo():
    df = query("""
        SELECT
            doenca,
            COUNT(DISTINCT municipio)  as municipios,
            COUNT(*)                   as registros,
            ROUND(AVG(casos_estimados), 1) as media_casos,
            MAX(casos_estimados)       as max_casos
        FROM mart_arboviroses
        GROUP BY doenca
        ORDER BY doenca
    """)

    return {"resumo": df.to_dict(orient="records")}


@app.get("/ranking/{doenca}")
def ranking(doenca: str, ano: int = 2025):
    if doenca not in DOENCAS:
        raise HTTPException(status_code=404, detail=f"Doença '{doenca}' não encontrada")

    df = query(f"""
        SELECT
            municipio,
            ROUND(AVG(casos_estimados), 1) as media_semanal,
            SUM(casos_estimados)           as total_casos,
            MAX(nivel_alerta)              as nivel_max
        FROM mart_arboviroses
        WHERE doenca = '{doenca}'
          AND ano    = {ano}
        GROUP BY municipio
        ORDER BY total_casos DESC
    """)

    return {
        "doenca": doenca,
        "ano":    ano,
        "ranking": df.to_dict(orient="records"),
    }
