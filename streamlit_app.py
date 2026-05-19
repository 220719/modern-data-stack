import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
import folium
import math
from streamlit_folium import st_folium

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
        margin-bottom: 0.3rem;
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
</style>
""", unsafe_allow_html=True)

CORES_NIVEL = {1: "#27ae60", 2: "#f39c12", 3: "#e67e22", 4: "#c0392b"}
LABELS_NIVEL = {1: "🟢 Baixo", 2: "🟡 Moderado", 3: "🟠 Alto", 4: "🔴 Epidemia"}

COORDENADAS = {
    "Curitiba":       {"lat": -25.4284, "lon": -49.2733},
    "Florianópolis":  {"lat": -27.5954, "lon": -48.5480},
    "Porto Alegre":   {"lat": -30.0346, "lon": -51.2177},
    "São Paulo":      {"lat": -23.5505, "lon": -46.6333},
    "Rio de Janeiro": {"lat": -22.9068, "lon": -43.1729},
    "Belo Horizonte": {"lat": -19.9191, "lon": -43.9386},
    "Vitória":        {"lat": -20.3155, "lon": -40.3128},
    "Brasília":       {"lat": -15.7801, "lon": -47.9292},
    "Goiânia":        {"lat": -16.6869, "lon": -49.2648},
    "Campo Grande":   {"lat": -20.4697, "lon": -54.6201},
    "Cuiabá":         {"lat": -15.5989, "lon": -56.0949},
    "Salvador":       {"lat": -12.9714, "lon": -38.5014},
    "Recife":         {"lat": -8.0476,  "lon": -34.8770},
    "Fortaleza":      {"lat": -3.7172,  "lon": -38.5433},
    "Natal":          {"lat": -5.7945,  "lon": -35.2110},
    "João Pessoa":    {"lat": -7.1195,  "lon": -34.8450},
    "Maceió":         {"lat": -9.6658,  "lon": -35.7350},
    "Aracaju":        {"lat": -10.9472, "lon": -37.0731},
    "Teresina":       {"lat": -5.0920,  "lon": -42.8038},
    "São Luís":       {"lat": -2.5307,  "lon": -44.3068},
    "Manaus":         {"lat": -3.1190,  "lon": -60.0217},
    "Belém":          {"lat": -1.4558,  "lon": -48.5044},
    "Porto Velho":    {"lat": -8.7612,  "lon": -63.9004},
    "Macapá":         {"lat": 0.0349,   "lon": -51.0694},
    "Boa Vista":      {"lat": 2.8235,   "lon": -60.6758},
    "Rio Branco":     {"lat": -9.9754,  "lon": -67.8249},
    "Palmas":         {"lat": -10.2491, "lon": -48.3243},
    "Maringá":        {"lat": -23.4205, "lon": -51.9333},
    "Londrina":       {"lat": -23.3045, "lon": -51.1696},
    "Ribeirão Preto": {"lat": -21.1775, "lon": -47.8103},
    "Foz do Iguaçu":  {"lat": -25.5478, "lon": -54.5882},
}

MUNICIPIOS_GEOCODIGOS = {
    "Curitiba": 4106902, "Florianópolis": 4205407, "Porto Alegre": 4314902,
    "São Paulo": 3550308, "Rio de Janeiro": 3304557, "Belo Horizonte": 3106200,
    "Vitória": 3205309, "Brasília": 5300108, "Goiânia": 5208707,
    "Campo Grande": 5002704, "Cuiabá": 5103403, "Salvador": 2927408,
    "Recife": 2611606, "Fortaleza": 2304400, "Natal": 2408102,
    "João Pessoa": 2507507, "Maceió": 2704302, "Aracaju": 2800308,
    "Teresina": 2211001, "São Luís": 2111300, "Manaus": 1302603,
    "Belém": 1501402, "Porto Velho": 1100205, "Macapá": 1600303,
    "Boa Vista": 1400100, "Rio Branco": 1200401, "Palmas": 1721000,
    "Maringá": 4115200, "Londrina": 4113700, "Ribeirão Preto": 3543402,
    "Foz do Iguaçu": 4108304,
}


@st.cache_data(ttl=3600)
def fetch_infodengue(geocodigo: int, doenca: str, ano: int) -> pd.DataFrame:
    url = "https://info.dengue.mat.br/api/alertcity"
    params = {
        "geocode": geocodigo, "disease": doenca,
        "format": "json", "ew_start": 1, "ew_end": 53,
        "ey_start": ano, "ey_end": ano,
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        df = pd.DataFrame(r.json())
        if df.empty:
            return pd.DataFrame()
        nome = [k for k, v in MUNICIPIOS_GEOCODIGOS.items() if v == geocodigo]
        df["municipio"] = nome[0] if nome else str(geocodigo)
        df["doenca"] = doenca
        return df
    except:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def carregar_situacao_atual(doenca: str, ano: int) -> pd.DataFrame:
    registros = []
    progress = st.progress(0, text="Carregando dados do InfoDengue...")
    municipios = list(MUNICIPIOS_GEOCODIGOS.items())
    for i, (municipio, geocodigo) in enumerate(municipios):
        progress.progress((i+1)/len(municipios), text=f"Carregando {municipio}...")
        df = fetch_infodengue(geocodigo, doenca, ano)
        if not df.empty and "casos_est" in df.columns:
            ultimo = df.sort_values("SE").iloc[-1]
            registros.append({
                "municipio":      municipio,
                "casos_estimados": float(ultimo.get("casos_est", 0) or 0),
                "nivel_alerta":   int(ultimo.get("nivel", 1) or 1),
                "semana":         int(str(ultimo.get("SE", 0))[-2:]),
                "ano":            ano,
            })
    progress.empty()
    return pd.DataFrame(registros) if registros else pd.DataFrame()


@st.cache_data(ttl=3600)
def carregar_historico_api(municipio: str, doenca: str, ano_inicio: int, ano_fim: int) -> pd.DataFrame:
    geocodigo = MUNICIPIOS_GEOCODIGOS.get(municipio)
    if not geocodigo:
        return pd.DataFrame()
    dfs = []
    for ano in range(ano_inicio, ano_fim + 1):
        df = fetch_infodengue(geocodigo, doenca, ano)
        if not df.empty:
            dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    df_all = pd.concat(dfs, ignore_index=True)
    if "data_iniSE" in df_all.columns:
        df_all["data"] = pd.to_datetime(df_all["data_iniSE"], unit="ms")
    df_all["casos_estimados"] = pd.to_numeric(df_all.get("casos_est", 0), errors="coerce").fillna(0)
    df_all["nivel_alerta"]    = pd.to_numeric(df_all.get("nivel", 1),     errors="coerce").fillna(1).astype(int)
    return df_all.sort_values("SE")


def treinar_modelo_cloud(municipio: str, doenca: str):
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import r2_score, mean_absolute_error
    import numpy as np

    dfs = []
    geocodigo = MUNICIPIOS_GEOCODIGOS.get(municipio)
    for ano in range(2020, 2026):
        df = fetch_infodengue(geocodigo, doenca, ano)
        if not df.empty:
            dfs.append(df)

    if not dfs:
        return None

    df_all = pd.concat(dfs).sort_values("SE")
    df_all["casos"] = pd.to_numeric(df_all.get("casos_est", 0), errors="coerce").fillna(0)
    df_all["lag1"]  = df_all["casos"].shift(1)
    df_all["lag2"]  = df_all["casos"].shift(2)
    df_all["lag4"]  = df_all["casos"].shift(4)
    df_all["mm4"]   = df_all["casos"].rolling(4).mean()
    df_all = df_all.dropna()

    if len(df_all) < 60:
        return None

    features = ["lag1", "lag2", "lag4", "mm4"]
    X = df_all[features].values
    y = df_all["casos"].values
    n_test = 52
    X_train, X_test = X[:-n_test], X[-n_test:]
    y_train, y_test = y[:-n_test], y[-n_test:]

    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    return {
        "model":   model,
        "r2":      r2_score(y_test, y_pred),
        "mae":     mean_absolute_error(y_test, y_pred),
        "df":      df_all,
        "features": features,
    }


def chat_groq(pergunta: str, contexto: str) -> str:
    from langchain_groq import ChatGroq
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    groq_key = st.secrets.get("GROQ_API_KEY", "")
    if not groq_key:
        return "⚠️ GROQ_API_KEY não configurada nos secrets do Streamlit Cloud."

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",,
        api_key=groq_key,
        temperature=0.1,
    )

    prompt = ChatPromptTemplate.from_template("""
Você é um especialista em vigilância epidemiológica de arboviroses no Brasil.
Use APENAS os dados abaixo para responder. Responda em português, de forma clara e objetiva.

Dados epidemiológicos:
{context}

Pergunta: {question}
Resposta:""")

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"context": contexto, "question": pergunta})


# ── SIDEBAR ──────────────────────────────────────────────
st.sidebar.markdown("## 🦟 Filtros")
doenca_sel    = st.sidebar.selectbox("Doença", ["dengue", "chikungunya", "zika"],
                    format_func=lambda x: x.capitalize())
ano_sel       = st.sidebar.selectbox("Ano", [2025, 2024, 2023, 2022, 2021, 2020])
municipio_sel = st.sidebar.selectbox("Município", sorted(MUNICIPIOS_GEOCODIGOS.keys()))
st.sidebar.markdown("---")
st.sidebar.markdown("**Fonte:** InfoDengue (Fiocruz)")
st.sidebar.markdown("**Cobertura:** 31 municípios · 2020–2025")
st.sidebar.markdown("**Stack:** Python · dbt · MLflow · FastAPI · Kafka · RAG · LLM")
st.sidebar.markdown("[📦 GitHub](https://github.com/220719/modern-data-stack)")

# ── HEADER ───────────────────────────────────────────────
st.markdown('<div class="main-header">🦟 Observatório Nacional de Arboviroses</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Vigilância epidemiológica de dengue, chikungunya e zika — 31 municípios brasileiros (2020–2025)</div>', unsafe_allow_html=True)

# ── MÉTRICAS ─────────────────────────────────────────────
with st.spinner("Carregando dados..."):
    df_atual = carregar_situacao_atual(doenca_sel, ano_sel)

if not df_atual.empty:
    total_casos   = int(df_atual["casos_estimados"].sum())
    em_epidemia   = int((df_atual["nivel_alerta"] == 4).sum())
    em_alerta     = int((df_atual["nivel_alerta"] >= 3).sum())
    media_casos   = round(df_atual["casos_estimados"].mean(), 1)
    municipio_top = df_atual.loc[df_atual["casos_estimados"].idxmax(), "municipio"]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🦟 Casos última semana", f"{total_casos:,}")
    c2.metric("🔴 Em epidemia",         f"{em_epidemia} municípios")
    c3.metric("🟠 Em alerta",           f"{em_alerta} municípios")
    c4.metric("📊 Média semanal",       f"{media_casos:,}")
    c5.metric("📍 Maior foco",          municipio_top)

    st.markdown("---")

    # ── MAPA ─────────────────────────────────────────────
    st.subheader(f"🗺️ Mapa de Alertas — {doenca_sel.capitalize()} {ano_sel}")
    m = folium.Map(location=[-14.5, -54.0], zoom_start=4, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager_nolabels/{z}/{x}/{y}{r}.png",
        attr="CartoDB",
    ).add_to(m)

    for _, row in df_atual.iterrows():
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
            radius=radius, color="white", weight=2,
            fill=True, fill_color=cor, fill_opacity=0.9,
            popup=folium.Popup(f"<b>{municipio}</b><br>{LABELS_NIVEL[nivel]}<br>{casos:,} casos", max_width=200),
            tooltip=f"{municipio} — {LABELS_NIVEL[nivel]}",
        ).add_to(m)

    st_folium(m, width=None, height=600, use_container_width=True)
    st.markdown("""
    <div style="display:flex;justify-content:center;gap:2rem;padding:0.8rem;background:#fff8f5;border-radius:8px;font-size:0.9rem;margin-top:0.5rem">
        <span><span style='display:inline-block;width:12px;height:12px;background:#27ae60;border-radius:50%;margin-right:4px'></span><b>Baixo</b></span>
        <span><span style='display:inline-block;width:12px;height:12px;background:#f39c12;border-radius:50%;margin-right:4px'></span><b>Moderado</b></span>
        <span><span style='display:inline-block;width:12px;height:12px;background:#e67e22;border-radius:50%;margin-right:4px'></span><b>Alto</b></span>
        <span><span style='display:inline-block;width:12px;height:12px;background:#c0392b;border-radius:50%;margin-right:4px'></span><b>Epidemia</b></span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── RANKING ──────────────────────────────────────────
    st.subheader(f"🏆 Ranking — {doenca_sel.capitalize()} {ano_sel}")
    df_rank = df_atual.sort_values("casos_estimados", ascending=False)
    df_rank["cor"] = df_rank["nivel_alerta"].map(CORES_NIVEL)
    fig_rank = go.Figure(go.Bar(
        x=df_rank["casos_estimados"], y=df_rank["municipio"],
        orientation="h", marker_color=df_rank["cor"],
        text=df_rank["casos_estimados"].apply(lambda x: f"{int(x):,}"),
        textposition="outside",
    ))
    fig_rank.update_layout(
        height=600, margin=dict(l=0, r=80, t=10, b=0),
        yaxis=dict(autorange="reversed"),
        xaxis_title="Casos estimados",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_rank, use_container_width=True)
    st.markdown("---")

# ── SÉRIE TEMPORAL ────────────────────────────────────────
st.subheader(f"📈 Série Temporal — {municipio_sel} / {doenca_sel.capitalize()}")
with st.spinner("Carregando histórico..."):
    df_hist = carregar_historico_api(municipio_sel, doenca_sel, 2020, 2025)

if not df_hist.empty and "data" in df_hist.columns:
    df_hist["media_movel"] = df_hist["casos_estimados"].rolling(4).mean()
    pico_idx   = df_hist["casos_estimados"].idxmax()
    pico_data  = df_hist.loc[pico_idx, "data"]
    pico_casos = int(df_hist.loc[pico_idx, "casos_estimados"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_hist["data"], y=df_hist["casos_estimados"],
        mode="lines", name="Casos estimados",
        line=dict(color="#e67e22", width=1.5),
        fill="tozeroy", fillcolor="rgba(230,126,34,0.12)",
    ))
    fig.add_trace(go.Scatter(
        x=df_hist["data"], y=df_hist["media_movel"],
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
        hovermode="x unified",
        plot_bgcolor="rgba(255,248,245,0.5)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── SIMULADOR ML ─────────────────────────────────────────
st.subheader("🤖 Simulador de Previsão — Machine Learning")
st.markdown("O modelo Random Forest é treinado com dados reais do InfoDengue (2020–2025).")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**📍 Localização**")
    mun_prev = st.selectbox("Município", sorted(MUNICIPIOS_GEOCODIGOS.keys()), key="ml_mun")
    doe_prev = st.selectbox("Doença", ["dengue", "chikungunya", "zika"], key="ml_doe",
                 format_func=lambda x: x.capitalize())
with col2:
    st.markdown("**🦟 Casos recentes**")
    casos_lag1 = st.number_input("Casos semana passada",  min_value=0, value=100, step=10)
    casos_lag2 = st.number_input("Casos 2 semanas atrás", min_value=0, value=120, step=10)
    casos_lag4 = st.number_input("Casos 4 semanas atrás", min_value=0, value=80,  step=10)
with col3:
    st.markdown("**📊 Tendência**")
    media_mov = st.number_input("Média móvel 4 semanas", min_value=0, value=100, step=10)

if st.button("🔮 Gerar Previsão", type="primary", use_container_width=True):
    with st.spinner("Treinando modelo com dados reais..."):
        resultado = treinar_modelo_cloud(mun_prev, doe_prev)

    if resultado:
        modelo = resultado["model"]
        inp = pd.DataFrame([{"lag1": casos_lag1, "lag2": casos_lag2, "lag4": casos_lag4, "mm4": media_mov}])
        previsao = int(modelo.predict(inp)[0])
        nivel_prev = 1 if previsao < 50 else 2 if previsao < 200 else 3 if previsao < 500 else 4

        cp1, cp2, cp3, cp4 = st.columns(4)
        cp1.metric("🔮 Casos previstos",  f"{previsao:,}")
        cp2.metric("📊 Nível estimado",   LABELS_NIVEL[nivel_prev])
        cp3.metric("✅ R² do modelo",     f"{resultado['r2']:.3f}")
        cp4.metric("📏 Erro médio (MAE)", f"{resultado['mae']:.1f} casos")

        st.markdown("""
        <div style="background:#f8f9fa;border-left:3px solid #95a5a6;padding:0.7rem 1rem;border-radius:6px;margin-top:0.5rem;font-size:0.82rem;color:#555">
        ℹ️ <b>R²</b>: quanto mais próximo de 1, melhor o modelo explica a variação dos casos. &nbsp;|&nbsp;
        ℹ️ <b>MAE</b>: erro médio absoluto em número de casos por semana.
        </div>
        """, unsafe_allow_html=True)

        # Projeção 4 semanas
        st.markdown("**Projeção para as próximas 4 semanas:**")
        projecoes = []
        l1, l2, l4, mm = casos_lag1, casos_lag2, casos_lag4, media_mov
        for s in range(1, 5):
            p = int(modelo.predict(pd.DataFrame([{"lag1": l1, "lag2": l2, "lag4": l4, "mm4": mm}]))[0])
            projecoes.append({"Semana": f"+{s}s", "Casos": p})
            l4, l2, l1 = l2, l1, p
            mm = (mm * 3 + p) / 4

        df_proj = pd.DataFrame(projecoes)
        fig_proj = px.bar(df_proj, x="Semana", y="Casos", text="Casos",
                          color="Casos", color_continuous_scale=["#27ae60","#f39c12","#e67e22","#c0392b"],
                          height=280)
        fig_proj.update_layout(margin=dict(l=0,r=0,t=10,b=0), coloraxis_showscale=False,
                               plot_bgcolor="rgba(255,248,245,0.5)", paper_bgcolor="rgba(0,0,0,0)")
        fig_proj.update_traces(textposition="outside")
        st.plotly_chart(fig_proj, use_container_width=True)
    else:
        st.warning("Dados insuficientes para esse município/doença.")

st.markdown("---")

# ── ALERTAS ──────────────────────────────────────────────
st.markdown("---")
st.subheader("⚡ Alertas Epidemiológicos")

if not df_atual.empty:
    df_alertas_show = df_atual[df_atual["nivel_alerta"] >= 3].sort_values(
        ["nivel_alerta", "casos_estimados"], ascending=[False, False]
    )

    if df_alertas_show.empty:
        st.success("✅ Nenhum município em nível de alerta elevado no momento.")
    else:
        for _, row in df_alertas_show.iterrows():
            nivel = int(row["nivel_alerta"])
            cor   = CORES_NIVEL.get(nivel, "#95a5a6")
            emoji = {3: "🟠", 4: "🔴"}.get(nivel, "⚪")
            st.markdown(f"""
            <div style="
                background:{cor}15;
                border-left:4px solid {cor};
                padding:0.6rem 1rem;
                border-radius:6px;
                margin-bottom:0.5rem;
                font-size:0.9rem;
            ">
                {emoji} <b>{row['municipio']}</b> / {doenca_sel.capitalize()} —
                Nível {nivel} ({LABELS_NIVEL[nivel]}) —
                <b>{int(row['casos_estimados']):,} casos</b>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("Selecione uma doença e ano para ver os alertas.")

# ── CHAT RAG COM GROQ ────────────────────────────────────
st.subheader("💬 Assistente Epidemiológico — RAG + Llama 3 (Groq)")
st.markdown("Perguntas em linguagem natural sobre os dados de arboviroses.")

col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    if st.button("🔴 Municípios em epidemia?"):
        st.session_state.pergunta_rag = "Quais municípios estão em nível de epidemia de dengue?"
with col_s2:
    if st.button("📊 Ranking histórico de dengue"):
        st.session_state.pergunta_rag = "Qual é o município com mais casos de dengue no histórico?"
with col_s3:
    if st.button("🌡️ Tendência atual"):
        st.session_state.pergunta_rag = "Como está a situação atual da dengue no Brasil?"

pergunta = st.text_input(
    "Digite sua pergunta:",
    value=st.session_state.get("pergunta_rag", ""),
    placeholder="Ex: Qual município tem mais casos de dengue em 2025?",
)

if st.button("🔍 Perguntar", type="primary") and pergunta:
    with st.spinner("🤖 Consultando Llama 3 via Groq..."):
        # Monta contexto com dados reais
        if not df_atual.empty:
            top5 = df_atual.sort_values("casos_estimados", ascending=False).head(5)
            contexto = f"Situação atual ({doenca_sel}, {ano_sel}):\n"
            for _, r in top5.iterrows():
                contexto += f"- {r['municipio']}: {int(r['casos_estimados'])} casos, nível {int(r['nivel_alerta'])} ({LABELS_NIVEL[int(r['nivel_alerta'])]})\n"
            contexto += f"\nTotal de casos: {total_casos:,}\nMunicípios em epidemia: {em_epidemia}\nMunicípios em alerta: {em_alerta}"
        else:
            contexto = "Dados não disponíveis no momento."

        resposta = chat_groq(pergunta, contexto)

    st.markdown(f"""
    <div style="background:#f8f9fa;border-left:4px solid #e67e22;padding:1rem 1.2rem;border-radius:8px;font-size:0.95rem;line-height:1.6;">
    🤖 {resposta}
    </div>
    """, unsafe_allow_html=True)
    st.caption("Resposta gerada por Llama 3 70B via Groq com base nos dados reais do InfoDengue")

st.markdown("---")
st.caption("Dados: InfoDengue (Fiocruz) | Stack: Python · dbt · MLflow · FastAPI · Streamlit · Docker · Airflow · Kafka · RAG · LLM")