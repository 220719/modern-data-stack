import json
from kafka import KafkaConsumer
from loguru import logger

KAFKA_BROKER  = "localhost:9092"
TOPIC_ALERTAS = "arboviroses-alertas"


def consumir_alertas(max_mensagens: int = 100):
    consumer = KafkaConsumer(
        TOPIC_ALERTAS,
        bootstrap_servers=KAFKA_BROKER,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="arboviroses-monitor",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        consumer_timeout_ms=5000,
    )

    alertas = []
    for msg in consumer:
        alerta = msg.value
        alertas.append(alerta)
        nivel = alerta["nivel_alerta"]
        emoji = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴"}.get(nivel, "⚪")
        logger.info(
            f"{emoji} {alerta['municipio']} / {alerta['doenca']} — "
            f"Nível {nivel} ({alerta['nivel_texto']}) — "
            f"{alerta['casos']:,} casos"
        )
        if len(alertas) >= max_mensagens:
            break

    consumer.close()
    return alertas