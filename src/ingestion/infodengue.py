import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from src.config import settings

MUNICIPIOS = {
    # Sul
    "Curitiba":       4106902,
    "Florianópolis":  4205407,
    "Porto Alegre":   4314902,
    # Sudeste
    "São Paulo":      3550308,
    "Rio de Janeiro": 3304557,
    "Belo Horizonte": 3106200,
    "Vitória":        3205309,
    # Centro-Oeste
    "Brasília":       5300108,
    "Goiânia":        5208707,
    "Campo Grande":   5002704,
    "Cuiabá":         5103403,
    # Nordeste
    "Salvador":       2927408,
    "Recife":         2611606,
    "Fortaleza":      2304400,
    "Natal":          2408102,
    "João Pessoa":    2507507,
    "Maceió":         2704302,
    "Aracaju":        2800308,
    "Teresina":       2211001,
    "São Luís":       2111300,
    # Norte
    "Manaus":         1302603,
    "Belém":          1501402,
    "Porto Velho":    1100205,
    "Macapá":         1600303,
    "Boa Vista":      1400100,
    "Rio Branco":     1200401,
    "Palmas":         1721000,
    # Bonus
    "Maringá":        4115200,
    "Londrina":       4113700,
    "Ribeirão Preto": 3543402,
    "Foz do Iguaçu":  4108304,
}

DOENCAS = {
    "dengue":      "dengue",
    "chikungunya": "chikungunya",
    "zika":        "zika",
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def fetch_alertas(
    geocodigo: int,
    doenca: str,
    ew_start: int,
    ew_end: int,
    ano_start: int,
    ano_end: int,
) -> list[dict]:
    url = settings.infodengue_base_url
    params = {
        "geocode":   geocodigo,
        "disease":   doenca,
        "format":    "json",
        "ew_start":  ew_start,
        "ew_end":    ew_end,
        "ey_start":  ano_start,
        "ey_end":    ano_end,
    }
    logger.info(f"Coletando {doenca} | geocódigo={geocodigo} | {ano_start}SE{ew_start} → {ano_end}SE{ew_end}")
    with httpx.Client(timeout=30) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        logger.success(f"  {len(data)} registros recebidos")
        return data


def coletar_municipio(
    nome: str,
    geocodigo: int,
    ano_start: int = 2020,
    ano_end: int = 2025,
) -> list[dict]:
    registros = []
    for doenca in DOENCAS:
        try:
            dados = fetch_alertas(
                geocodigo=geocodigo,
                doenca=doenca,
                ew_start=1,
                ew_end=53,
                ano_start=ano_start,
                ano_end=ano_end,
            )
            for r in dados:
                r["municipio"] = nome
                r["geocodigo"] = geocodigo
                r["doenca"]    = doenca
            registros.extend(dados)
        except Exception as e:
            logger.error(f"Erro em {nome}/{doenca}: {e}")
    return registros


def coletar_todos(ano_start: int = 2020, ano_end: int = 2025) -> list[dict]:
    todos = []
    for nome, geocodigo in MUNICIPIOS.items():
        dados = coletar_municipio(nome, geocodigo, ano_start, ano_end)
        todos.extend(dados)
        logger.info(f"Total acumulado: {len(todos)} registros")
    return todos