import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from src.storage.database import query
from src.ingestion.infodengue import MUNICIPIOS
from src.ingestion.openmeteo import COORDENADAS
from src.ml.features import carregar_features, preparar_xy
from src.ml.modelo import walk_forward_validation

st.set_page_config(
    page_title="Arboviroses Brasil",
    page_icon="🦟",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem; font-weight: 900;
        color: #d35400; text-align: center;
        margin-bottom: 0.3rem; letter-spacing: -1px;
    }
    .sub-header {
        font-size: 1.05rem; color: #7f8c8d;
        text-align: center; margin-bottom: 1.5rem;
    }
    div[data-testid="stMetric"] {
        background: #fff8f5;
        border-left: 4px solid #e67e22;
        padding: 0.8rem 1rem; border-radius: 8px;
    }
    section[data-testid="stSidebar"] { background-color: #fff8f5; }
    .previsao-box {
        background: linear-gradient(135deg, #fff8f5, #fdebd0);
        border: 2px solid #e67e22; border-radius: 12px;
        padding: 1.5rem; margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

CORES_NIVEL = {1: "#27ae60", 2: "#f39c12", 3: "#e67e22", 4: "#c0392b"}
LABELS_NIVEL = {1: "🟢 Baixo", 2: "🟡 Moderado", 3: "🟠 Alto", 4: "🔴 Epidemia"}


@st.cache_data(ttl=300)
def carregar_ultimo_alerta():
    return query("""
        SELECT municipio, doenca, ano, semana,
               casos_estimados, nivel_alerta, media_movel_4s
        FROM mart_arboviroses
        WHERE (municipio, doenca, semana_epidemiologica) IN (
            SELECT municipio, doenca, MAX(semana_epidemiologica)
            FROM mart_arboviroses GROUP BY municipio, doenca
        )
        ORDER BY municipio, doenca
    """)


@st.cache_data(ttl=300)
def carregar_historico(municipio, doenca):
    return query(f"""
        SELECT ano, semana, semana_epidemiologica, data_inicio_se,
               casos_estimados, nivel_alerta, media_movel_4s,
               temp_min_lag2, precipitacao_lag2
        FROM mart_arboviroses
        WHERE municipio = '{municipio}' AND doenca = '{doenca}'
        ORDER BY semana_epidemiologica
    """)


@st.cache_data(ttl=300)
def carregar_ranking(doenca, ano):
    return query(f"""
        SELECT municipio,
               SUM(casos_estimados) as total_casos,
               ROUND(AVG(casos_estimados), 1) as media_semanal,
               MAX(nivel_alerta) as nivel_max
        FROM mart_arboviroses
        WHERE doenca = '{doenca}' AND ano = {ano}
        GROUP BY municipio ORDER BY total_casos DESC
    """)


@st.cache_data(ttl=300)
def carregar_comparativo(municipio):
    return query(f"""
        SELECT doenca, ano, SUM(casos_estimados) as total
        FROM mart_arboviroses
        WHERE municipio = '{municipio}'
        GROUP BY doenca, ano ORDER BY ano
    """)


# ── SIDEBAR ──────────────────────────────────────────────
st.sidebar.markdown("## 🦟 Filtros")
doenca_sel    = st.sidebar.selectbox("Doença", ["dengue", "chikungunya", "zika"],
                    format_func=lambda x: x.capitalize())
ano_sel       = st.sidebar.selectbox("Ano", [2025, 2024, 2023, 2022, 2021, 2020])
municipio_sel = st.sidebar.selectbox("Município", sorted(MUNICIPIOS.keys()))
st.sidebar.markdown("---")
st.sidebar.markdown("**Fonte:** InfoDengue (Fiocruz) + OpenMeteo")
st.sidebar.markdown("**Cobertura:** 31 municípios · 2020–2025")
st.sidebar.markdown("**Atualização:** semanal")

# ── HEADER ───────────────────────────────────────────────
st.markdown('<div class="main-header">🦟 Observatório Nacional de Arboviroses</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Vigilância epidemiológica de dengue, chikungunya e zika — 31 municípios brasileiros (2020–2025)</div>', unsafe_allow_html=True)

# ── MÉTRICAS ─────────────────────────────────────────────
df_alertas   = carregar_ultimo_alerta()
df_doenca    = df_alertas[df_alertas["doenca"] == doenca_sel]
total_casos  = int(df_doenca["casos_estimados"].sum())
em_epidemia  = int((df_doenca["nivel_alerta"] == 4).sum())
em_alerta    = int((df_doenca["nivel_alerta"] >= 3).sum())
media_casos  = round(df_doenca["casos_estimados"].mean(), 1)
municipio_topo = df_doenca.loc[df_doenca["casos_estimados"].idxmax(), "municipio"] if not df_doenca.empty else "—"

def metrica_card(emoji, titulo, valor, tooltip):
    st.markdown(f"""
    <div title="{tooltip}" style="
        background:#fff8f5;
        border-left:4px solid #e67e22;
        padding:0.8rem 1rem;
        border-radius:8px;
        cursor:help;
    ">
        <div style="font-size:1.6rem; line-height:1">{emoji}</div>
        <div style="font-size:0.72rem; color:#7f8c8d; margin-top:4px; font-weight:600; text-transform:uppercase; letter-spacing:0.5px">{titulo}</div>
        <div style="font-size:1.4rem; font-weight:800; color:#2c3e50; margin-top:2px">{valor}</div>
        <div style="font-size:0.65rem; color:#bdc3c7; margin-top:4px">ℹ️ {tooltip[:60]}...</div>
    </div>
    """, unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    metrica_card("🦟", "Casos última semana", f"{total_casos:,}",
        "Soma dos casos estimados de todos os municípios monitorados na semana mais recente disponível")
with c2:
    metrica_card("🔴", "Em epidemia", f"{em_epidemia} municípios",
        "Municípios em nível 4 de alerta — situação crítica com transmissão intensa")
with c3:
    metrica_card("🟠", "Em alerta", f"{em_alerta} municípios",
        "Municípios em nível 3 ou 4 — requer atenção e mobilização das equipes de saúde")
with c4:
    metrica_card("📊", "Média semanal", f"{media_casos:,}",
        "Média de casos estimados por município na última semana registrada")
with c5:
    metrica_card("📍", "Maior foco", municipio_topo,
        "Município com maior número de casos estimados na semana mais recente")

st.markdown("---")

# ── MAPA EM DESTAQUE ──────────────────────────────────────
st.subheader(f"🗺️ Mapa de Alertas — {doenca_sel.capitalize()}")

import math
import requests

@st.cache_data(ttl=86400)
def carregar_geojson_brasil():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    return requests.get(url, timeout=15).json()

brasil_geojson = carregar_geojson_brasil()

m = folium.Map(
    location=[-14.5, -54.0],
    zoom_start=4,
    tiles=None,
    min_zoom=4,
    max_zoom=7,
    max_bounds=True,
)

# Fundo neutro
folium.TileLayer(
    tiles="https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png",
    attr="CartoDB",
    name="Light",
    opacity=0.4,
).add_to(m)

# Destaque do Brasil em laranja claro
folium.GeoJson(
    brasil_geojson,
    name="Brasil",
    style_function=lambda x: {
        "fillColor": "#fdebd0",
        "color":     "#d35400",
        "weight":    1.5,
        "fillOpacity": 0.85,
    },
    highlight_function=lambda x: {
        "fillColor": "#f5cba7",
        "color":     "#a04000",
        "weight":    2,
        "fillOpacity": 0.95,
    },
).add_to(m)

# Marcadores
for _, row in df_doenca.iterrows():
    municipio = row["municipio"]
    if municipio not in COORDENADAS:
        continue
    coords = COORDENADAS[municipio]
    nivel  = int(row["nivel_alerta"])
    cor    = CORES_NIVEL.get(nivel, "#95a5a6")
    casos  = int(row["casos_estimados"])
    radius = max(8, min(35, 8 + math.log1p(casos) * 3))

    folium.CircleMarker(
        location=[coords["lat"], coords["lon"]],
        radius=radius + 4,
        color=cor,
        weight=0,
        fill=True,
        fill_color=cor,
        fill_opacity=0.25,
    ).add_to(m)

    folium.CircleMarker(
        location=[coords["lat"], coords["lon"]],
        radius=radius,
        color="white",
        weight=2.5,
        fill=True,
        fill_color=cor,
        fill_opacity=0.95,
        popup=folium.Popup(
            f"<div style='font-family:sans-serif; min-width:180px'>"
            f"<b style='font-size:16px; color:{cor}'>{municipio}</b><br>"
            f"<hr style='margin:6px 0; border-color:#eee'>"
            f"<b>Nível:</b> {LABELS_NIVEL[nivel]}<br>"
            f"<b>Casos:</b> {casos:,}<br>"
            f"<b>Média 4 semanas:</b> {int(row['media_movel_4s'] or 0):,}"
            f"</div>",
            max_width=240,
        ),
        tooltip=folium.Tooltip(
            f"<b>{municipio}</b><br>{LABELS_NIVEL[nivel]} — {casos:,} casos",
            style="font-size:13px; font-family:sans-serif",
        ),
    ).add_to(m)

st_folium(m, width=None, height=650, use_container_width=True)

# Legenda visual
st.markdown("""
<div style="
    display:flex;
    justify-content:center;
    gap:2rem;
    margin-top:0.5rem;
    padding:0.8rem;
    background:#fff8f5;
    border-radius:8px;
    font-size:0.9rem;
">
    <span><span style='display:inline-block;width:14px;height:14px;background:#27ae60;border-radius:50%;margin-right:6px;vertical-align:middle'></span><b>Baixo</b></span>
    <span><span style='display:inline-block;width:14px;height:14px;background:#f39c12;border-radius:50%;margin-right:6px;vertical-align:middle'></span><b>Moderado</b></span>
    <span><span style='display:inline-block;width:14px;height:14px;background:#e67e22;border-radius:50%;margin-right:6px;vertical-align:middle'></span><b>Alto</b></span>
    <span><span style='display:inline-block;width:14px;height:14px;background:#c0392b;border-radius:50%;margin-right:6px;vertical-align:middle'></span><b>Epidemia</b></span>
    <span style="color:#7f8c8d">— tamanho proporcional aos casos</span>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── RANKING ───────────────────────────────────────────────
st.subheader(f"🏆 Ranking de Municípios — {doenca_sel.capitalize()} {ano_sel}")
df_rank = carregar_ranking(doenca_sel, ano_sel)
if not df_rank.empty:
    df_rank["cor"] = df_rank["nivel_max"].map(CORES_NIVEL)
    fig_rank = go.Figure(go.Bar(
        x=df_rank.head(20)["total_casos"],
        y=df_rank.head(20)["municipio"],
        orientation="h",
        marker_color=df_rank.head(20)["cor"],
        text=df_rank.head(20)["total_casos"].apply(lambda x: f"{int(x):,}"),
        textposition="outside",
        textfont=dict(size=12),
    ))
    fig_rank.update_layout(
        height=600,
        margin=dict(l=0, r=80, t=10, b=0),
        yaxis=dict(autorange="reversed"),
        xaxis_title="Total de casos no ano",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    st.plotly_chart(fig_rank, use_container_width=True)

st.markdown("---")

# ── SÉRIE TEMPORAL ────────────────────────────────────────
st.subheader(f"📈 Série Temporal — {municipio_sel} / {doenca_sel.capitalize()}")
df_hist = carregar_historico(municipio_sel, doenca_sel)

if not df_hist.empty:
    df_hist["data_inicio_se"] = pd.to_datetime(df_hist["data_inicio_se"])
    pico_idx   = df_hist["casos_estimados"].idxmax()
    pico_data  = df_hist.loc[pico_idx, "data_inicio_se"]
    pico_casos = int(df_hist.loc[pico_idx, "casos_estimados"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_hist["data_inicio_se"], y=df_hist["casos_estimados"],
        mode="lines", name="Casos estimados",
        line=dict(color="#e67e22", width=1.5),
        fill="tozeroy", fillcolor="rgba(230,126,34,0.12)",
    ))
    fig.add_trace(go.Scatter(
        x=df_hist["data_inicio_se"], y=df_hist["media_movel_4s"],
        mode="lines", name="Média móvel 4s",
        line=dict(color="#c0392b", width=2.5, dash="dot"),
    ))
    fig.add_annotation(
        x=pico_data, y=pico_casos,
        text=f"🔴 Pico: {pico_casos:,}",
        showarrow=True, arrowhead=2,
        bgcolor="white", bordercolor="#c0392b",
    )
    fig.update_layout(
        height=350, margin=dict(l=0, r=0, t=20, b=0),
        legend=dict(orientation="h", y=1.08),
        xaxis_title="Semana epidemiológica",
        yaxis_title="Casos estimados",
        hovermode="x unified",
        plot_bgcolor="rgba(255,248,245,0.5)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── COMPARATIVO ───────────────────────────────────────────
col_comp, col_clima = st.columns(2)

with col_comp:
    st.subheader(f"📊 Comparativo de Doenças — {municipio_sel}")
    df_comp = carregar_comparativo(municipio_sel)
    if not df_comp.empty:
        fig_comp = px.bar(
            df_comp, x="ano", y="total", color="doenca",
            barmode="group",
            color_discrete_map={
                "dengue": "#e74c3c",
                "chikungunya": "#e67e22",
                "zika": "#3498db",
            },
            labels={"total": "Total de casos", "ano": "Ano", "doenca": "Doença"},
            height=350,
        )
        fig_comp.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", y=1.08),
            plot_bgcolor="rgba(255,248,245,0.5)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickmode="linear", dtick=1),
        )
        st.plotly_chart(fig_comp, use_container_width=True)

with col_clima:
    st.subheader(f"🌡️ Clima × Casos — {municipio_sel}")
    if not df_hist.empty:
        fig_clima = go.Figure()
        fig_clima.add_trace(go.Scatter(
            x=df_hist["data_inicio_se"], y=df_hist["casos_estimados"],
            name="Casos", yaxis="y1",
            line=dict(color="#e67e22", width=2),
        ))
        fig_clima.add_trace(go.Scatter(
            x=df_hist["data_inicio_se"], y=df_hist["temp_min_lag2"],
            name="Temp. mín. lag2 (°C)", yaxis="y2",
            line=dict(color="#c0392b", width=1.5, dash="dot"),
        ))
        fig_clima.add_trace(go.Bar(
            x=df_hist["data_inicio_se"], y=df_hist["precipitacao_lag2"],
            name="Precipitação lag2 (mm)", yaxis="y3",
            marker_color="rgba(52,152,219,0.3)",
        ))
        fig_clima.update_layout(
            height=350,
            margin=dict(l=0, r=60, t=10, b=0),
            legend=dict(orientation="h", y=1.08),
            yaxis=dict(title="Casos", side="left"),
            yaxis2=dict(title="Temp (°C)", overlaying="y", side="right", showgrid=False),
            yaxis3=dict(overlaying="y", side="right", showgrid=False, visible=False),
            hovermode="x unified",
            plot_bgcolor="rgba(255,248,245,0.5)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_clima, use_container_width=True)

st.markdown("---")

# ── PREVISÃO ML ───────────────────────────────────────────
st.subheader("🤖 Simulador de Previsão — Machine Learning")
st.markdown("Ajuste os parâmetros abaixo e veja a previsão do modelo Random Forest para as próximas semanas.")

with st.container():
    col_inp1, col_inp2, col_inp3 = st.columns(3)

    with col_inp1:
        st.markdown("**📍 Localização e doença**")
        mun_prev   = st.selectbox("Município", sorted(MUNICIPIOS.keys()), key="prev_mun")
        doe_prev   = st.selectbox("Doença", ["dengue", "chikungunya", "zika"], key="prev_doe",
                        format_func=lambda x: x.capitalize())

    with col_inp2:
        st.markdown("**🦟 Casos recentes**")
        casos_lag1 = st.number_input("Casos semana passada",     min_value=0, value=100, step=10)
        casos_lag2 = st.number_input("Casos 2 semanas atrás",    min_value=0, value=120, step=10)
        casos_lag4 = st.number_input("Casos 4 semanas atrás",    min_value=0, value=80,  step=10)
        media_mov  = st.number_input("Média móvel 4 semanas",    min_value=0, value=100, step=10)

    with col_inp3:
        st.markdown("**🌡️ Condições climáticas**")
        temp_min   = st.slider("Temperatura mínima lag 2 (°C)", 10.0, 35.0, 22.0, 0.5)
        precip     = st.slider("Precipitação lag 2 (mm)",       0.0,  200.0, 50.0, 5.0)
        umidade    = st.slider("Umidade relativa lag 4 (%)",    40.0, 100.0, 75.0, 1.0)

    if st.button("🔮 Gerar Previsão", type="primary", use_container_width=True):
        with st.spinner("Treinando modelo e gerando previsão..."):
            try:
                df_feat = carregar_features(mun_prev, doe_prev)
                if len(df_feat) < 104:
                    st.warning("Dados insuficientes para esse município/doença.")
                else:
                    X, y = preparar_xy(df_feat)
                    resultado = walk_forward_validation(X, y, n_test=52)
                    modelo = resultado["model"]

                    input_df = pd.DataFrame([{
                        "casos_lag1":        casos_lag1,
                        "casos_lag2":        casos_lag2,
                        "casos_lag4":        casos_lag4,
                        "temp_min_lag2":     temp_min,
                        "precipitacao_lag2": precip,
                        "umidade_lag4":      umidade,
                        "media_movel_4s":    media_mov,
                    }])

                    previsao = int(modelo.predict(input_df)[0])
                    r2       = resultado["r2"]
                    mae      = resultado["mae"]

                    if previsao < 50:     nivel_prev = 1
                    elif previsao < 200:  nivel_prev = 2
                    elif previsao < 500:  nivel_prev = 3
                    else:                 nivel_prev = 4

                    st.markdown("---")
                    cp1, cp2, cp3, cp4 = st.columns(4)
                    cp1.metric("🔮 Casos previstos",    f"{previsao:,}")
                    cp2.metric("📊 Nível estimado",     LABELS_NIVEL[nivel_prev])
                    cp3.metric("✅ R² do modelo",       f"{r2:.3f}")
                    cp4.metric("📏 Erro médio (MAE)",   f"{mae:.1f} casos")

                    # Projeção 4 semanas
                    st.markdown("**Projeção para as próximas 4 semanas:**")
                    projecoes = []
                    c_lag1, c_lag2, c_lag4 = casos_lag1, casos_lag2, casos_lag4
                    mm = media_mov

                    for semana in range(1, 5):
                        inp = pd.DataFrame([{
                            "casos_lag1":        c_lag1,
                            "casos_lag2":        c_lag2,
                            "casos_lag4":        c_lag4,
                            "temp_min_lag2":     temp_min,
                            "precipitacao_lag2": precip,
                            "umidade_lag4":      umidade,
                            "media_movel_4s":    mm,
                        }])
                        prev = int(modelo.predict(inp)[0])
                        projecoes.append({"Semana": f"+{semana}s", "Casos previstos": prev,
                                          "Nível": LABELS_NIVEL[min(4, max(1,
                                              1 if prev < 50 else 2 if prev < 200 else 3 if prev < 500 else 4))]})
                        c_lag4, c_lag2, c_lag1 = c_lag2, c_lag1, prev
                        mm = (mm * 3 + prev) / 4

                    df_proj = pd.DataFrame(projecoes)
                    fig_proj = px.bar(
                        df_proj, x="Semana", y="Casos previstos",
                        text="Casos previstos",
                        color="Casos previstos",
                        color_continuous_scale=["#27ae60", "#f39c12", "#e67e22", "#c0392b"],
                        height=300,
                    )
                    fig_proj.update_layout(
                        margin=dict(l=0, r=0, t=10, b=0),
                        coloraxis_showscale=False,
                        plot_bgcolor="rgba(255,248,245,0.5)",
                        paper_bgcolor="rgba(0,0,0,0)",
                    )
                    fig_proj.update_traces(textposition="outside")
                    st.plotly_chart(fig_proj, use_container_width=True)

            except Exception as e:
                st.error(f"Erro na previsão: {e}")

st.markdown("---")

# ── CHAT RAG ─────────────────────────────────────────────
st.markdown("---")
st.subheader("💬 Assistente Epidemiológico — RAG + Llama 3")
st.markdown("Faça perguntas em linguagem natural sobre os dados de arboviroses.")

# Sugestões de perguntas
st.markdown("**💡 Exemplos de perguntas:**")
col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    if st.button("🔴 Quais municípios estão em epidemia?"):
        st.session_state.pergunta_rag = "Quais municípios estão em nível de epidemia de dengue?"
with col_s2:
    if st.button("📊 Compare dengue 2024 vs 2023 em Maringá"):
        st.session_state.pergunta_rag = "Compare os casos de dengue em 2024 versus 2023 em Maringá"
with col_s3:
    if st.button("🌡️ Clima e dengue em Fortaleza"):
        st.session_state.pergunta_rag = "Qual a relação entre temperatura e casos de dengue em Fortaleza?"

pergunta = st.text_input(
    "Digite sua pergunta:",
    value=st.session_state.get("pergunta_rag", ""),
    placeholder="Ex: Qual município tem mais casos de chikungunya em 2025?",
    key="input_rag"
)

if st.button("🔍 Perguntar", type="primary") and pergunta:
    with st.spinner("🤖 Consultando dados e gerando resposta..."):
        try:
            from src.rag.chat import responder_stream
            resposta_container = st.empty()
            resposta_completa = ""
            for chunk in responder_stream(pergunta):
                resposta_completa += chunk
                resposta_container.markdown(f"""
                <div style="
                    background:#f8f9fa;
                    border-left:4px solid #e67e22;
                    padding:1rem 1.2rem;
                    border-radius:8px;
                    font-size:0.95rem;
                    line-height:1.6;
                ">
                🤖 {resposta_completa}▌
                </div>
                """, unsafe_allow_html=True)
            resposta_container.markdown(f"""
            <div style="
                background:#f8f9fa;
                border-left:4px solid #e67e22;
                padding:1rem 1.2rem;
                border-radius:8px;
                font-size:0.95rem;
                line-height:1.6;
            ">
            🤖 {resposta_completa}
            </div>
            """, unsafe_allow_html=True)
            st.caption("Resposta gerada por Llama 3 com base nos dados reais do InfoDengue")
        except Exception as e:
            st.error(f"Erro: {e}")
            
st.caption("Dados: InfoDengue (Fiocruz) + OpenMeteo | Modelos: Random Forest · dbt · MLflow · FastAPI · Streamlit")