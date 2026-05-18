import json
from datetime import datetime
from kafka import KafkaProducer
from loguru import logger
from src.storage.database import query

KAFKA_BROKER = "localhost:9092"
TOPIC_ALERTAS = "arboviroses-alertas"


def get_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8"),
    )


def publicar_alertas() -> int:
    df = query("""
        SELECT municipio, doenca, ano, semana,
               casos_estimados, nivel_alerta, media_movel_4s
        FROM mart_arboviroses
        WHERE (municipio, doenca, semana_epidemiologica) IN (
            SELECT municipio, doenca, MAX(semana_epidemiologica)
            FROM mart_arboviroses GROUP BY municipio, doenca
        )
        AND nivel_alerta >= 3
        ORDER BY nivel_alerta DESC, casos_estimados DESC
    """)

    if df.empty:
        logger.info("Nenhum alerta para publicar")
        return 0

    producer = get_producer()
    total = 0

    for _, row in df.iterrows():
        evento = {
            "municipio":      row["municipio"],
            "doenca":         row["doenca"],
            "ano":            int(row["ano"]),
            "semana":         int(row["semana"]),
            "casos":          int(row["casos_estimados"]),
            "nivel_alerta":   int(row["nivel_alerta"]),
            "media_movel_4s": round(float(row["media_movel_4s"] or 0), 1),
            "timestamp":      datetime.now().isoformat(),
            "nivel_texto": {
                1: "Baixo", 2: "Moderado",
                3: "Alto",  4: "Epidemia"
            }.get(int(row["nivel_alerta"]), "?"),
        }

        producer.send(
            TOPIC_ALERTAS,
            key=f"{row['municipio']}_{row['doenca']}",
            value=evento,
        )
        logger.info(f"📤 Alerta publicado: {row['municipio']}/{row['doenca']} — nível {int(row['nivel_alerta'])}")
        total += 1

    producer.flush()
    producer.close()
    logger.success(f"{total} alertas publicados no Kafka")
    return total