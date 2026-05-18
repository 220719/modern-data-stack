import chromadb
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger
from pathlib import Path
from src.config import settings
from src.storage.database import query

CHROMA_PATH = Path(__file__).parent.parent.parent / "data" / "chroma"
COLLECTION  = "arboviroses"


def get_embeddings():
    return OllamaEmbeddings(
        model="llama3",
        base_url=settings.ollama_base_url,
    )


def get_vectorstore():
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return Chroma(
        client=client,
        collection_name=COLLECTION,
        embedding_function=get_embeddings(),
    )


def indexar_dados_banco() -> int:
    logger.info("Indexando dados do banco no Chroma...")
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
    )

    documentos = []
    metadatas  = []

    # 1. Resumo geral por município e doença (todos os anos)
    df_resumo = query("""
        SELECT
            municipio, doenca,
            ano,
            SUM(casos_estimados)            as total_casos,
            ROUND(AVG(casos_estimados), 1)  as media_semanal,
            MAX(casos_estimados)            as pico_casos,
            MAX(nivel_alerta)               as nivel_max
        FROM mart_arboviroses
        GROUP BY municipio, doenca, ano
        ORDER BY municipio, doenca, ano
    """)

    for municipio in df_resumo["municipio"].unique():
        for doenca in df_resumo["doenca"].unique():
            subset = df_resumo[
                (df_resumo["municipio"] == municipio) &
                (df_resumo["doenca"] == doenca)
            ]
            if subset.empty:
                continue

            linhas = []
            for _, r in subset.iterrows():
                linhas.append(
                    f"  Ano {int(r['ano'])}: total={int(r['total_casos'])} casos, "
                    f"média={r['media_semanal']}/semana, "
                    f"pico={int(r['pico_casos'])}, "
                    f"nível_max={int(r['nivel_max'])}"
                )

            total_geral = int(subset["total_casos"].sum())
            pico_geral  = int(subset["pico_casos"].max())
            ano_pico    = int(subset.loc[subset["pico_casos"].idxmax(), "ano"])

            texto = f"""
Município: {municipio} | Doença: {doenca.capitalize()}
Total de casos (2020-2025): {total_geral:,}
Pico histórico: {pico_geral:,} casos (ano {ano_pico})
Nível máximo de alerta já registrado: {int(subset['nivel_max'].max())} (4=epidemia)

Evolução anual:
{chr(10).join(linhas)}
            """.strip()

            chunks = splitter.split_text(texto)
            for chunk in chunks:
                documentos.append(chunk)
                metadatas.append({
                    "municipio": municipio,
                    "doenca": doenca,
                    "tipo": "resumo_anual",
                })

    # 2. Situação atual (última semana)
    df_atual = query("""
        SELECT municipio, doenca, ano, semana,
               casos_estimados, nivel_alerta, media_movel_4s
        FROM mart_arboviroses
        WHERE (municipio, doenca, semana_epidemiologica) IN (
            SELECT municipio, doenca, MAX(semana_epidemiologica)
            FROM mart_arboviroses GROUP BY municipio, doenca
        )
        ORDER BY casos_estimados DESC
    """)

    # Documento geral de situação atual
    linhas_atual = []
    for _, r in df_atual[df_atual["doenca"] == "dengue"].iterrows():
        nivel_txt = {1:"baixo", 2:"moderado", 3:"alto", 4:"epidemia"}.get(int(r["nivel_alerta"]), "?")
        linhas_atual.append(
            f"  {r['municipio']}: {int(r['casos_estimados'])} casos, nível {int(r['nivel_alerta'])} ({nivel_txt})"
        )

    texto_atual = f"""
Situação atual de DENGUE em todos os municípios (última semana registrada):
{chr(10).join(linhas_atual)}

Municípios em epidemia (nível 4): {', '.join(df_atual[(df_atual['doenca']=='dengue') & (df_atual['nivel_alerta']==4)]['municipio'].tolist()) or 'Nenhum'}
Municípios em alerta alto (nível 3): {', '.join(df_atual[(df_atual['doenca']=='dengue') & (df_atual['nivel_alerta']==3)]['municipio'].tolist()) or 'Nenhum'}
Município com mais casos atualmente: {df_atual[df_atual['doenca']=='dengue'].iloc[0]['municipio']} ({int(df_atual[df_atual['doenca']=='dengue'].iloc[0]['casos_estimados'])} casos)
    """.strip()

    documentos.append(texto_atual)
    metadatas.append({"municipio": "todos", "doenca": "dengue", "tipo": "situacao_atual"})

    # 3. Ranking histórico geral
    df_rank = query("""
        SELECT municipio,
               SUM(casos_estimados) as total_dengue
        FROM mart_arboviroses
        WHERE doenca = 'dengue'
        GROUP BY municipio
        ORDER BY total_dengue DESC
    """)

    ranking_txt = "\n".join([
        f"  {i+1}. {r['municipio']}: {int(r['total_dengue']):,} casos totais (2020-2025)"
        for i, (_, r) in enumerate(df_rank.iterrows())
    ])

    texto_rank = f"""
Ranking de municípios por total de casos de DENGUE (2020-2025):
{ranking_txt}

A cidade mais crítica historicamente é {df_rank.iloc[0]['municipio']} com {int(df_rank.iloc[0]['total_dengue']):,} casos totais.
    """.strip()

    documentos.append(texto_rank)
    metadatas.append({"municipio": "todos", "doenca": "dengue", "tipo": "ranking"})

    # Limpa e reindexar
    import shutil
    if CHROMA_PATH.exists():
        shutil.rmtree(CHROMA_PATH)
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)

    vs = get_vectorstore()
    vs.add_texts(documentos, metadatas=metadatas)

    logger.success(f"{len(documentos)} chunks indexados no Chroma")
    return len(documentos)