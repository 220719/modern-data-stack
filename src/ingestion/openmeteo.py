import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from src.config import settings

COORDENADAS = {
    # Sul
    "Curitiba":          {"lat": -25.4284, "lon": -49.2733},
    "Florianópolis":     {"lat": -27.5954, "lon": -48.5480},
    "Porto Alegre":      {"lat": -30.0346, "lon": -51.2177},
    # Sudeste
    "São Paulo":         {"lat": -23.5505, "lon": -46.6333},
    "Rio de Janeiro":    {"lat": -22.9068, "lon": -43.1729},
    "Belo Horizonte":    {"lat": -19.9191, "lon": -43.9386},
    "Vitória":           {"lat": -20.3155, "lon": -40.3128},
    # Centro-Oeste
    "Brasília":          {"lat": -15.7801, "lon": -47.9292},
    "Goiânia":           {"lat": -16.6869, "lon": -49.2648},
    "Campo Grande":      {"lat": -20.4697, "lon": -54.6201},
    "Cuiabá":            {"lat": -15.5989, "lon": -56.0949},
    # Nordeste
    "Salvador":          {"lat": -12.9714, "lon": -38.5014},
    "Recife":            {"lat": -8.0476,  "lon": -34.8770},
    "Fortaleza":         {"lat": -3.7172,  "lon": -38.5433},
    "Natal":             {"lat": -5.7945,  "lon": -35.2110},
    "João Pessoa":       {"lat": -7.1195,  "lon": -34.8450},
    "Maceió":            {"lat": -9.6658,  "lon": -35.7350},
    "Aracaju":           {"lat": -10.9472, "lon": -37.0731},
    "Teresina":          {"lat": -5.0920,  "lon": -42.8038},
    "São Luís":          {"lat": -2.5307,  "lon": -44.3068},
    # Norte
    "Manaus":            {"lat": -3.1190,  "lon": -60.0217},
    "Belém":             {"lat": -1.4558,  "lon": -48.5044},
    "Porto Velho":       {"lat": -8.7612,  "lon": -63.9004},
    "Macapá":            {"lat": 0.0349,   "lon": -51.0694},
    "Boa Vista":         {"lat": 2.8235,   "lon": -60.6758},
    "Rio Branco":        {"lat": -9.9754,  "lon": -67.8249},
    "Palmas":            {"lat": -10.2491, "lon": -48.3243},
    # Bonus — maiores focos históricos de dengue
    "Maringá":           {"lat": -23.4205, "lon": -51.9333},
    "Londrina":          {"lat": -23.3045, "lon": -51.1696},
    "Ribeirão Preto":    {"lat": -21.1775, "lon": -47.8103},
    "Foz do Iguaçu":     {"lat": -25.5478, "lon": -54.5882},
}

VARIAVEIS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "relative_humidity_2m_max",
    "relative_humidity_2m_min",
]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def fetch_clima(
    municipio: str,
    lat: float,
    lon: float,
    data_inicio: str,
    data_fim: str,
) -> list[dict]:
    url = settings.openmeteo_base_url
    params = {
        "latitude":   lat,
        "longitude":  lon,
        "start_date": data_inicio,
        "end_date":   data_fim,
        "daily":      ",".join(VARIAVEIS),
        "timezone":   "America/Sao_Paulo",
    }
    logger.info(f"Coletando clima | {municipio} | {data_inicio} → {data_fim}")
    with httpx.Client(timeout=30) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    datas = data["daily"]["time"]
    registros = []
    for i, dt in enumerate(datas):
        registro = {"municipio": municipio, "data": dt}
        for var in VARIAVEIS:
            valores = data["daily"].get(var, [])
            registro[var] = valores[i] if i < len(valores) else None
        registros.append(registro)

    logger.success(f"  {len(registros)} dias coletados para {municipio}")
    return registros


def coletar_clima_todos(
    data_inicio: str = "2020-01-01",
    data_fim: str = "2025-12-31",
) -> list[dict]:
    todos = []
    for municipio, coords in COORDENADAS.items():
        try:
            dados = fetch_clima(
                municipio=municipio,
                lat=coords["lat"],
                lon=coords["lon"],
                data_inicio=data_inicio,
                data_fim=data_fim,
            )
            todos.extend(dados)
        except Exception as e:
            logger.error(f"Erro em {municipio}: {e}")
    logger.info(f"Total clima: {len(todos)} registros")
    return todos