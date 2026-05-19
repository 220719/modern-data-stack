# 🦟 Observatório Nacional de Arboviroses

[![CI Pipeline](https://github.com/220719/modern-data-stack/actions/workflows/ci.yml/badge.svg)](https://github.com/220719/modern-data-stack/actions)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit)](https://modern-data-stack-esap3ujuz6qen2mjso4prh.streamlit.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://www.docker.com/)
[![Airflow](https://img.shields.io/badge/Apache_Airflow-2.9-017CEE?logo=apacheairflow)](https://airflow.apache.org/)
[![Kafka](https://img.shields.io/badge/Apache_Kafka-7.5-231F20?logo=apachekafka)](https://kafka.apache.org/)

---

> **Plataforma completa de vigilância epidemiológica** de dengue, chikungunya e zika em 31 municípios brasileiros, construída com uma Modern Data Stack 100% open source.

## 🌐 [Acesse o Dashboard ao Vivo](https://modern-data-stack-esap3ujuz6qen2mjso4prh.streamlit.app/)

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Stack Tecnológica](#-stack-tecnológica)
- [Funcionalidades](#-funcionalidades)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Como Rodar](#-como-rodar)
- [Ondas de Desenvolvimento](#-ondas-de-desenvolvimento)
- [Resultados dos Modelos ML](#-resultados-dos-modelos-ml)
- [API REST](#-api-rest)
- [Testes](#-testes)
- [Dados](#-dados)
- [Autor](#-autor)

---

## 🎯 Sobre o Projeto

O **Observatório Nacional de Arboviroses** é uma plataforma end-to-end de ciência de dados aplicada à saúde pública brasileira. Cobre todas as camadas de um pipeline de dados profissional moderno.

| Camada | O que foi feito |
|---|---|
| **Ingestão** | Coleta automática de casos (InfoDengue/Fiocruz) + clima (OpenMeteo) |
| **Armazenamento** | DuckDB local + MinIO (S3-compatible) |
| **Transformação** | dbt com staging views e mart table com feature engineering |
| **ML** | 93 modelos Random Forest com walk-forward validation + MLflow tracking |
| **Serving** | FastAPI REST + Streamlit dashboard |
| **Streaming** | Apache Kafka para alertas em tempo real |
| **Orquestração** | Apache Airflow com DAGs semanais |
| **GenAI** | RAG com Chroma + Llama 3 (local) e Groq API (cloud) |
| **Infraestrutura** | Docker Compose + GitHub Actions CI/CD |

---

## 🛠️ Stack Tecnológica

### Dados e Storage

| Ferramenta | Versão | Uso |
|---|---|---|
| **Python** | 3.12 | Linguagem principal |
| **DuckDB** | 1.5 | Banco de dados analítico local |
| **MinIO** | latest | Data lake S3-compatible |
| **dbt** | 1.11 | Transformações SQL versionadas |
| **Polars** | 1.40 | Processamento de dados |

### Machine Learning

| Ferramenta | Versão | Uso |
|---|---|---|
| **scikit-learn** | 1.8 | Random Forest, métricas |
| **MLflow** | 3.12 | Experiment tracking, Model Registry |
| **pandas** | 2.3 | Manipulação de dados |

### Serving e APIs

| Ferramenta | Versão | Uso |
|---|---|---|
| **FastAPI** | 0.136 | API REST |
| **Streamlit** | 1.57 | Dashboard interativo |
| **uvicorn** | 0.47 | ASGI server |

### Streaming e Orquestração

| Ferramenta | Versão | Uso |
|---|---|---|
| **Apache Kafka** | 7.5 | Streaming de alertas |
| **Apache Airflow** | 2.9 | Orquestração de pipelines |

### GenAI e RAG

| Ferramenta | Versão | Uso |
|---|---|---|
| **Chroma** | 1.5 | Vector database |
| **LangChain** | 1.3 | Framework RAG |
| **Ollama** | latest | LLM local (Llama 3) |
| **Groq API** | latest | LLM cloud (Llama 3 70B) |

### Infraestrutura

| Ferramenta | Versão | Uso |
|---|---|---|
| **Docker** | 29.5 | Containerização |
| **Docker Compose** | 5.1 | Orquestração local |
| **GitHub Actions** | — | CI/CD automático |

---

## ✨ Funcionalidades

### 🗺️ Mapa Interativo
- Visualização de 31 municípios brasileiros
- Cores por nível de alerta (🟢 Baixo 🟡 Moderado 🟠 Alto 🔴 Epidemia)
- Tamanho dos círculos proporcional aos casos
- Tooltip com detalhes ao hover

### 📈 Análise Temporal
- Série histórica 2020-2025
- Média móvel de 4 semanas
- Marcação automática do pico histórico
- Comparativo entre doenças por ano

### 🤖 Simulador ML
- Modelo Random Forest treinado com dados reais
- Inputs: casos recentes + tendência
- Previsão + projeção 4 semanas
- Métricas R² e MAE exibidas

### 💬 Chat RAG
- Perguntas em linguagem natural
- Llama 3 70B via Groq API
- Contexto com dados reais do InfoDengue
- Respostas em português

### ⚡ Alertas Epidemiológicos
- Municípios em nível 3 (Alto) e 4 (Epidemia)
- Atualização automática semanal via Airflow

---

## 📁 Estrutura do Projeto

    modern-data-stack/
    ├── src/
    │   ├── ingestion/          # ETL: InfoDengue + OpenMeteo
    │   │   ├── infodengue.py   # Coleta de casos (31 municípios x 3 doenças)
    │   │   ├── openmeteo.py    # Coleta de clima (6 variáveis x 2192 dias)
    │   │   └── pipeline.py     # Pipeline completo de ingestão
    │   ├── storage/
    │   │   └── database.py     # DuckDB: casos_raw + clima_raw
    │   ├── ml/
    │   │   ├── features.py     # Feature engineering
    │   │   ├── modelo.py       # Walk-forward validation
    │   │   └── treinar.py      # MLflow tracking + Model Registry
    │   ├── api/
    │   │   └── main.py         # FastAPI: 6 endpoints REST
    │   ├── dashboard/
    │   │   └── app.py          # Streamlit: versão local completa
    │   ├── streaming/
    │   │   ├── producer.py     # Kafka producer de alertas
    │   │   └── consumer.py     # Kafka consumer
    │   └── rag/
    │       ├── indexador.py    # Chroma: indexação de dados
    │       └── chat.py         # LangChain + Ollama/Groq
    ├── infra/
    │   ├── docker/             # Dockerfiles API + Streamlit
    │   ├── airflow/dags/       # DAGs semanais
    │   └── dbt/models/         # Staging + Marts
    ├── tests/                  # 23 testes automatizados
    ├── streamlit_app.py        # Dashboard cloud (Streamlit Cloud)
    ├── docker-compose.yml      # 7 serviços containerizados
    └── .github/workflows/      # GitHub Actions CI

---

## 🚀 Como Rodar

### Pré-requisitos
- Python 3.12+
- uv (https://docs.astral.sh/uv/)
- Docker + Docker Compose

### 1. Clone o repositório

    git clone https://github.com/220719/modern-data-stack.git
    cd modern-data-stack

### 2. Instala dependências

    uv sync

### 3. Sobe a infraestrutura

    docker compose up -d

### 4. Executa o pipeline

    # Ingestão
    uv run python -c "from src.ingestion.pipeline import executar_pipeline; executar_pipeline()"

    # Transformações dbt
    cd infra/dbt && uv run dbt run

    # Treina modelos ML
    uv run python -c "from src.ml.treinar import treinar_todos; treinar_todos()"

### 5. Sobe o dashboard

    uv run streamlit run src/dashboard/app.py

### Serviços disponíveis

| Serviço | URL |
|---|---|
| Dashboard | http://localhost:8501 |
| FastAPI docs | http://localhost:8000/docs |
| MLflow UI | http://localhost:5000 |
| Airflow | http://localhost:8080 |
| MinIO Console | http://localhost:9001 |

---

## 🌊 Ondas de Desenvolvimento

| Onda | Tecnologia | Descrição |
|---|---|---|
| 1 | Python + DuckDB | Ingestão de 26.164 casos + 68.318 dias de clima |
| 2 | dbt | Transformações SQL: staging + mart com lags e features |
| 3 | scikit-learn + MLflow | 93 modelos Random Forest com walk-forward validation |
| 4 | FastAPI | 6 endpoints REST com documentação automática |
| 5 | Streamlit | Dashboard com mapa, ML, RAG e alertas |
| 6 | Docker | 7 containers orquestrados com um comando |
| 7 | Apache Airflow | 2 DAGs semanais automatizando o pipeline |
| 8 | Chroma + Llama 3 | RAG com vector database e LLM local |
| 9 | Apache Kafka | Streaming de alertas epidemiológicos |
| 10 | GitHub Actions | CI/CD com 23 testes a cada push |
| Deploy | Streamlit Cloud | URL pública com dados reais e LLM via Groq |

---

## 📊 Resultados dos Modelos ML

### Top 10 Modelos por R²

| # | Município | Doença | R² | MAE | RMSE |
|---|---|---|---|---|---|
| 🥇 | Londrina | Dengue | **0.962** | 57.5 | 77.1 |
| 🥈 | Ribeirão Preto | Dengue | **0.942** | 100.1 | 184.4 |
| 🥉 | Maringá | Dengue | **0.934** | 60.9 | 95.9 |
| 4 | Florianópolis | Dengue | 0.927 | 45.3 | 61.7 |
| 5 | Maceió | Dengue | 0.918 | 12.7 | 18.0 |
| 6 | Rio Branco | Dengue | 0.899 | 49.0 | 75.8 |
| 7 | Goiânia | Dengue | 0.893 | 129.0 | 187.6 |
| 8 | Rio de Janeiro | Dengue | 0.885 | 89.0 | 131.6 |
| 9 | São Paulo | Dengue | 0.879 | 1239.4 | 1958.7 |
| 10 | Campo Grande | Dengue | 0.874 | 15.4 | 20.9 |

### Resumo Geral (93 modelos)

| Métrica | Valor |
|---|---|
| R² médio | 0.508 |
| Melhor R² | 0.962 (Londrina/dengue) |
| MAE médio | 35.6 casos/semana |
| Feature mais importante | casos_lag1 (importância ~ 0.97) |

---

## 🔌 API REST

Base URL: `http://localhost:8000`

| Endpoint | Método | Descrição |
|---|---|---|
| `/health` | GET | Status da API |
| `/municipios` | GET | Lista de municípios |
| `/doencas` | GET | Lista de doenças |
| `/historico/{municipio}/{doenca}` | GET | Série histórica |
| `/alertas` | GET | Municípios em alerta |
| `/ranking/{doenca}` | GET | Ranking por ano |
| `/resumo` | GET | Resumo geral |

Documentação interativa: `http://localhost:8000/docs`

---

## ✅ Testes

    uv run pytest tests/ -v

    tests/test_api.py          9 passed
    tests/test_config.py       3 passed
    tests/test_database.py     6 passed
    tests/test_infodengue.py   5 passed
    TOTAL                     23 passed

---

## 📦 Dados

| Dado | Volume |
|---|---|
| Municípios monitorados | 31 capitais + cidades do PR |
| Doenças | Dengue, Chikungunya, Zika |
| Período | 2020-2025 |
| Registros de casos | 26.164 |
| Registros de clima | 68.318 dias |
| Modelos treinados | 93 (31 x 3) |
| Chunks RAG indexados | 95 |

---

## 📄 Licença

MIT License

---

## 👤 Autor

<div align="center">

### Anuar Mincache

**PhD Physics | Data Science | Machine Learning | Research & Development | Data-Driven Decision Making**

📧 fisicanuar@gmail.com | 🔗 [GitHub](https://github.com/220719)

---

**Construído com dados reais do InfoDengue/Fiocruz**

🌐 [Dashboard ao Vivo](https://modern-data-stack-esap3ujuz6qen2mjso4prh.streamlit.app/) | 📦 [GitHub](https://github.com/220719/modern-data-stack)

</div>
