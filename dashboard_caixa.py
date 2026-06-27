"""
Dashboard de Caixa — Streamlit + Excel
Streamlit Cloud: aponta para caixa_demo.xlsx por padrão.
Para uso local, troque EXCEL_PATH pelo caminho do seu arquivo.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os, time

# ─── Configuração ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Caixa",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

EXCEL_PATH = "caixa_demo.xlsx"   # ← troque pelo seu arquivo se necessário

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.kpi-wrap { display:flex; gap:16px; margin-bottom:8px; }
.kpi {
    flex:1; border-radius:14px; padding:20px 24px;
    color:#fff; box-shadow:0 4px 18px rgba(0,0,0,.12);
}
.kpi.green  { background:linear-gradient(135deg,#1a7a3c,#28a745); }
.kpi.red    { background:linear-gradient(135deg,#9e2a00,#e84a1f); }
.kpi.blue   { background:linear-gradient(135deg,#1a3a6c,#2563eb); }
.kpi.purple { background:linear-gradient(135deg,#4a1580,#7c3aed); }
.kpi-label  { font-size:12px; font-weight:600; opacity:.85; letter-spacing:.5px; text-transform:uppercase; }
.kpi-value  { font-size:30px; font-weight:700; margin-top:6px; }
.kpi-sub    { font-size:12px; opacity:.7; margin-top:4px; }

.section-title {
    font-size:15px; font-weight:700; color:#1e293b;
    margin:18px 0 6px; letter-spacing:.2px;
}
.badge-entrada { background:#d1fae5; color:#065f46; padding:2px 10px; border-radius:99px; font-size:12px; font-weight:600; }
.badge-saida   { background:#fee2e2; color:#991b1b; padding:2px 10px; border-radius:99px; font-size:12px; font-weight:600; }
</style>
""", unsafe_allow_html=True)


# ─── Funções ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=5)
def load_data(path: str, _mtime: float) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Caixa")
    df.columns = df.columns.str.strip()
    col_map = {}
    for c in df.columns:
        cl = c.lower()
        if "data" in cl:          col_map[c] = "data"
        elif "escri" in cl:       col_map[c] = "descricao"
        elif "egori" in cl:       col_map[c] = "categoria"
        elif "tipo" in cl:        col_map[c] = "tipo"
        elif "alor" in cl:        col_map[c] = "valor"
        elif "bserv" in cl:       col_map[c] = "obs"
    df = df.rename(columns=col_map)
    df["data"]  = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
    df["tipo"]  = df["tipo"].astype(str).str.strip().str.title()
    df = df.dropna(subset=["data"])
    df["mes"]   = df["data"].dt.to_period("M").astype(str)
    df["dia"]   = df["data"].dt.date
    return df

def get_mtime(path):
    return os.path.getmtime(path) if os.path.exists(path) else 0

def fmt(val):
    return f"R$ {val:,.2f}".replace(",","X").replace(".",",").replace("X",".")

COLORS = {
    "Entrada": "#28a745",
    "Saída":   "#e84a1f",
    "Saldo":   "#2563eb",
}

PIZZA_ENTRADA = px.colors.sequential.Greens_r
PIZZA_SAIDA   = px.colors.sequential.Oranges_r


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💰 Dashboard Caixa")
    st.caption("Análise financeira em tempo real")
    st.divider()

    auto = st.toggle("🔄 Atualização automática", value=True)
    if auto:
        intervalo = st.slider("Intervalo (seg)", 5, 60, 10)
        st.caption(f"Recarregando a cada {intervalo}s")
    else:
        if st.button("↺ Atualizar agora", use_container_width=True):
            st.cache_data.clear()

    st.divider()
    st.subheader("📅 Período")
    periodo = st.selectbox("", [
        "Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias",
        "Este mês", "Mês anterior", "Todo o histórico"
    ], index=1, label_visibility="collapsed")

    hoje = datetime.today().date()
    if   periodo == "Últimos 7 dias":   ini = hoje - timedelta(days=7)
    elif periodo == "Últimos 30 dias":  ini = hoje - timedelta(days=30)
    elif periodo == "Últimos 90 dias":  ini = hoje - timedelta(days=90)
    elif periodo == "Este mês":         ini = hoje.replace(day=1)
    elif periodo == "Mês anterior":
        p   = hoje.replace(day=1)
        ini = (p - timedelta(days=1)).replace(day=1)
        hoje = p - timedelta(days=1)
    else:                               ini = datetime(2000,1,1).date()

    st.divider()
    st.caption(f"📂 `{EXCEL_PATH}`")
    st.caption("Desenvolvido com Streamlit + Plotly")


# ─── Carrega dados ────────────────────────────────────────────────────────────
if not os.path.exists(EXCEL_PATH):
    st.error(f"Arquivo **{EXCEL_PATH}** não encontrado na raiz do repositório.")
    st.stop()

df_all = load_data(EXCEL_PATH, get_mtime(EXCEL_PATH))
df     = df_all[(df_all["dia"] >= ini) & (df_all["dia"] <= hoje)].copy()

if df.empty:
    st.warning("Nenhum registro no período selecionado.")
    st.stop()


# ─── KPIs ─────────────────────────────────────────────────────────────────────
entradas  = df[df["tipo"] == "Entrada"]["valor"].sum()
saidas    = df[df["tipo"] == "Saída"]["valor"].sum()
saldo     = entradas - saidas
n_reg     = len(df)

st.markdown(f"""
# 📊 Dashboard de Caixa
<p style='color:#64748b;font-size:13px;margin-top:-12px'>
  Período: <b>{ini.strftime('%d/%m/%Y')}</b> → <b>{hoje.strftime('%d/%m/%Y')}</b>
  &nbsp;|&nbsp; {n_reg} registros &nbsp;|&nbsp;
  Atualizado: {datetime.now().strftime('%H:%M:%S')}
</p>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.markdown(f'<div class="kpi green"><div class="kpi-label">📈 Entradas</div><div class="kpi-value">{fmt(entradas)}</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="kpi red"><div class="kpi-label">📉 Saídas</div><div class="kpi-value">{fmt(saidas)}</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="kpi {"blue" if saldo >= 0 else "red"}"><div class="kpi-label">💼 Saldo</div><div class="kpi-value">{fmt(saldo)}</div></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="kpi purple"><div class="kpi-label">📋 Registros</div><div class="kpi-value">{n_reg}</div><div class="kpi-sub">no período</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ─── Fluxo diário ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📅 Fluxo de Caixa Diário</div>', unsafe_allow_html=True)

diario = (
    df.groupby(["dia","tipo"])["valor"].sum().reset_index()
    .pivot(index="dia", columns="tipo", values="valor").fillna(0).reset_index()
)
fig_flux = go.Figure()
for tipo, cor, fill_cor in [
    ("Entrada","#28a745","rgba(40,167,69,.12)"),
    ("Saída",  "#e84a1f","rgba(232,74,31,.12)"),
]:
    if tipo in diario.columns:
        fig_flux.add_trace(go.Scatter(
            x=diario["dia"], y=diario[tipo], name=tipo,
            line=dict(color=cor, width=2.5),
            fill="tozeroy", fillcolor=fill_cor,
            hovertemplate=f"<b>{tipo}</b><br>%{{x}}<br>R$ %{{y:,.2f}}<extra></extra>"
        ))
fig_flux.update_layout(
    height=280, margin=dict(l=0,r=0,t=8,b=0),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    yaxis=dict(tickprefix="R$ ", gridcolor="#f1f5f9"),
    xaxis=dict(gridcolor="#f1f5f9"),
    hovermode="x unified"
)
st.plotly_chart(fig_flux, use_container_width=True)


# ─── Pizzas ───────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🍕 Composição por Categoria</div>', unsafe_allow_html=True)
p1, p2 = st.columns(2)

def pizza(df_base, tipo, cores, col):
    dados = df_base[df_base["tipo"]==tipo].groupby("categoria")["valor"].sum().reset_index()
    if dados.empty:
        col.info(f"Sem registros de {tipo}")
        return
    fig = px.pie(dados, values="valor", names="categoria",
                 color_discrete_sequence=cores, hole=0.42,
                 title=f"{'📈' if tipo=='Entrada' else '📉'} {tipo}s")
    fig.update_traces(textposition="inside", textinfo="percent+label",
                      hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>")
    fig.update_layout(height=340, margin=dict(l=0,r=0,t=40,b=0),
                      showlegend=False, paper_bgcolor="rgba(0,0,0,0)")
    col.plotly_chart(fig, use_container_width=True)

pizza(df, "Entrada", PIZZA_ENTRADA, p1)
pizza(df, "Saída",   PIZZA_SAIDA,   p2)


# ─── Barras por categoria ──────────────────────────────────────────────────────
st.markdown('<div class="section-title">📊 Entradas vs Saídas por Categoria</div>', unsafe_allow_html=True)
comp = df.groupby(["categoria","tipo"])["valor"].sum().reset_index()
fig_bar = px.bar(
    comp, x="categoria", y="valor", color="tipo", barmode="group",
    color_discrete_map={"Entrada":"#28a745","Saída":"#e84a1f"},
    text_auto=".2s",
    labels={"valor":"Valor (R$)","categoria":"Categoria","tipo":"Tipo"},
)
fig_bar.update_traces(textposition="outside", hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>")
fig_bar.update_layout(
    height=320, margin=dict(l=0,r=0,t=8,b=0),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    yaxis=dict(tickprefix="R$ ", gridcolor="#f1f5f9"),
    xaxis=dict(gridcolor="rgba(0,0,0,0)"),
)
st.plotly_chart(fig_bar, use_container_width=True)


# ─── Resumo mensal ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📆 Resumo Mensal + Saldo</div>', unsafe_allow_html=True)
piv = (
    df_all.groupby(["mes","tipo"])["valor"].sum().reset_index()
    .pivot(index="mes", columns="tipo", values="valor").fillna(0).reset_index()
)
piv["Saldo"] = piv.get("Entrada",0) - piv.get("Saída",0)
piv = piv.sort_values("mes")

fig_mes = make_subplots(specs=[[{"secondary_y":True}]])
for tipo, cor in [("Entrada","#28a745"),("Saída","#e84a1f")]:
    if tipo in piv.columns:
        fig_mes.add_trace(go.Bar(
            x=piv["mes"], y=piv[tipo], name=tipo,
            marker_color=cor, opacity=.85,
            hovertemplate=f"<b>{tipo}</b><br>%{{x}}<br>R$ %{{y:,.2f}}<extra></extra>"
        ), secondary_y=False)
fig_mes.add_trace(go.Scatter(
    x=piv["mes"], y=piv["Saldo"], name="Saldo",
    line=dict(color="#2563eb", width=3, dash="dot"),
    mode="lines+markers+text",
    text=[fmt(v) for v in piv["Saldo"]],
    textposition="top center",
    textfont=dict(size=10, color="#2563eb"),
    hovertemplate="<b>Saldo</b><br>%{x}<br>R$ %{y:,.2f}<extra></extra>"
), secondary_y=True)
fig_mes.update_layout(
    barmode="group", height=340, margin=dict(l=0,r=0,t=8,b=0),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
)
fig_mes.update_yaxes(tickprefix="R$ ", gridcolor="#f1f5f9", secondary_y=False)
fig_mes.update_yaxes(tickprefix="R$ ", showgrid=False, secondary_y=True)
st.plotly_chart(fig_mes, use_container_width=True)


# ─── Top categorias ───────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🏆 Top Categorias</div>', unsafe_allow_html=True)
ta, tb = st.columns(2)
for col_w, tipo, cor in [(ta,"Entrada","#28a745"),(tb,"Saída","#e84a1f")]:
    top = (df[df["tipo"]==tipo].groupby("categoria")["valor"]
           .sum().sort_values(ascending=True).tail(6).reset_index())
    if top.empty:
        col_w.info(f"Sem dados de {tipo}")
        continue
    fig_h = px.bar(top, x="valor", y="categoria", orientation="h",
                   color_discrete_sequence=[cor],
                   labels={"valor":"R$","categoria":""})
    fig_h.update_traces(text=[fmt(v) for v in top["valor"]], textposition="outside")
    fig_h.update_layout(height=260, margin=dict(l=0,r=60,t=8,b=0),
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        showlegend=False,
                        xaxis=dict(tickprefix="R$ ", gridcolor="#f1f5f9"),
                        yaxis=dict(gridcolor="rgba(0,0,0,0)"))
    col_w.plotly_chart(fig_h, use_container_width=True)


# ─── Tabela ────────────────────────────────────────────────────────────────────
with st.expander("🗂️ Registros detalhados"):
    cols_show = [c for c in ["data","descricao","categoria","tipo","valor"] if c in df.columns]
    show = df[cols_show].copy()
    show["data"] = show["data"].dt.strftime("%d/%m/%Y")
    show["tipo"] = show["tipo"].apply(
        lambda x: f"✅ {x}" if x=="Entrada" else f"🔴 {x}"
    )
    st.dataframe(
        show.sort_values("data", ascending=False).reset_index(drop=True),
        height=380, use_container_width=True
    )


# ─── Auto-refresh ──────────────────────────────────────────────────────────────
if auto:
    time.sleep(intervalo)
    st.rerun()
