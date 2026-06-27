import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time

# ─── Configuração ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Caixa",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ⚠️  Troque pela URL da SUA planilha (veja README)
SHEET_URL = "https://docs.google.com/spreadsheets/d/14EZ1Rh6OIs7fnlMLUV-BRURRQiMDJ2cVEWCPtTIpy50/export?format=csv&gid=0"

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.kpi {
    border-radius:14px; padding:20px 24px; color:#fff;
    box-shadow:0 4px 18px rgba(0,0,0,.12); margin-bottom:4px;
}
.kpi.green  { background:linear-gradient(135deg,#1a7a3c,#28a745); }
.kpi.red    { background:linear-gradient(135deg,#9e2a00,#e84a1f); }
.kpi.blue   { background:linear-gradient(135deg,#1a3a6c,#2563eb); }
.kpi.purple { background:linear-gradient(135deg,#4a1580,#7c3aed); }
.kpi-label  { font-size:11px; font-weight:700; opacity:.8; letter-spacing:.8px; text-transform:uppercase; }
.kpi-value  { font-size:28px; font-weight:700; margin-top:6px; }
.kpi-sub    { font-size:12px; opacity:.65; margin-top:3px; }

.section-title {
    font-size:15px; font-weight:700; color:#1e293b;
    margin:20px 0 6px; border-left:4px solid #2563eb;
    padding-left:10px;
}
.live-badge {
    display:inline-block; background:#dcfce7; color:#166534;
    border-radius:99px; padding:3px 12px; font-size:12px;
    font-weight:700; animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
</style>
""", unsafe_allow_html=True)


# ─── Funções ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=5)
def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    col_map = {}
    for c in df.columns:
        cl = c.lower()
        if   "data"  in cl:             col_map[c] = "data"
        elif "escri" in cl or "desc" in cl: col_map[c] = "descricao"
        elif "egori" in cl:             col_map[c] = "categoria"
        elif "tipo"  in cl:             col_map[c] = "tipo"
        elif "alor"  in cl:             col_map[c] = "valor"
    df = df.rename(columns=col_map)
    df["data"]  = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
    df["valor"] = pd.to_numeric(
        df["valor"].astype(str)
          .str.replace("R$","",regex=False)
          .str.replace(".","",regex=False)
          .str.replace(",",".",regex=False)
          .str.strip(),
        errors="coerce"
    ).fillna(0)
    df["tipo"] = df["tipo"].astype(str).str.strip().str.title()
    df = df.dropna(subset=["data"])
    df["mes"] = df["data"].dt.to_period("M").astype(str)
    df["dia"] = df["data"].dt.date
    return df

def fmt(val: float) -> str:
    return f"R$ {val:,.2f}".replace(",","X").replace(".",",").replace("X",".")


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💰 Dashboard Caixa")
    st.markdown('<span class="live-badge">🟢 AO VIVO</span>', unsafe_allow_html=True)
    st.caption("Conectado ao Google Sheets")
    st.divider()

    auto = st.toggle("🔄 Atualização automática", value=True)
    if auto:
        intervalo = st.slider("Intervalo (seg)", 3, 30, 5)
        st.caption(f"Verificando a cada {intervalo}s")
    else:
        if st.button("↺ Atualizar agora", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

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
    st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}")


# ─── Carrega dados ────────────────────────────────────────────────────────────
try:
    df_all = load_data(SHEET_URL)
except Exception as e:
    st.error("**Erro ao carregar a planilha.**\n\nVerifique se:\n- A URL está correta no código\n- O acesso está como **'Qualquer pessoa com o link'**")
    st.code(str(e))
    st.stop()

df = df_all[(df_all["dia"] >= ini) & (df_all["dia"] <= hoje)].copy()

if df.empty:
    st.warning("Nenhum registro no período. Adicione dados na planilha!")
    st.stop()


# ─── KPIs ─────────────────────────────────────────────────────────────────────
entradas = df[df["tipo"] == "Entrada"]["valor"].sum()
saidas   = df[df["tipo"] == "Saída"]["valor"].sum()
saldo    = entradas - saidas
n_reg    = len(df)

st.markdown(f"""
# 📊 Dashboard de Caixa
<p style='color:#64748b;font-size:13px;margin-top:-10px'>
  Período: <b>{ini.strftime('%d/%m/%Y')}</b> → <b>{hoje.strftime('%d/%m/%Y')}</b>
  &nbsp;|&nbsp; {n_reg} registros &nbsp;|&nbsp; ⏱ {datetime.now().strftime('%H:%M:%S')}
</p>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.markdown(f'<div class="kpi green"><div class="kpi-label">📈 Entradas</div><div class="kpi-value">{fmt(entradas)}</div><div class="kpi-sub">{df[df["tipo"]=="Entrada"].shape[0]} lançamentos</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="kpi red"><div class="kpi-label">📉 Saídas</div><div class="kpi-value">{fmt(saidas)}</div><div class="kpi-sub">{df[df["tipo"]=="Saída"].shape[0]} lançamentos</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="kpi {"blue" if saldo >= 0 else "red"}"><div class="kpi-label">💼 Saldo</div><div class="kpi-value">{fmt(saldo)}</div><div class="kpi-sub">{"✅ Positivo" if saldo >= 0 else "⚠️ Negativo"}</div></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="kpi purple"><div class="kpi-label">📋 Registros</div><div class="kpi-value">{n_reg}</div><div class="kpi-sub">no período</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ─── Fluxo diário ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📅 Fluxo de Caixa Diário</div>', unsafe_allow_html=True)
diario = (
    df.groupby(["dia","tipo"])["valor"].sum().reset_index()
    .pivot(index="dia", columns="tipo", values="valor").fillna(0).reset_index()
)
fig_flux = go.Figure()
for tipo, cor, fill in [
    ("Entrada","#28a745","rgba(40,167,69,.13)"),
    ("Saída",  "#e84a1f","rgba(232,74,31,.13)"),
]:
    if tipo in diario.columns:
        fig_flux.add_trace(go.Scatter(
            x=diario["dia"], y=diario[tipo], name=tipo,
            line=dict(color=cor, width=2.5),
            fill="tozeroy", fillcolor=fill,
            hovertemplate=f"<b>{tipo}</b><br>%{{x}}<br>R$ %{{y:,.2f}}<extra></extra>"
        ))
fig_flux.update_layout(
    height=280, margin=dict(l=0,r=0,t=8,b=0),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    yaxis=dict(tickprefix="R$ ", gridcolor="#f1f5f9"),
    hovermode="x unified"
)
st.plotly_chart(fig_flux, use_container_width=True)


# ─── Pizzas ───────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🍕 Composição por Categoria</div>', unsafe_allow_html=True)
p1, p2 = st.columns(2)

def pizza(df_b, tipo, cores, col):
    d = df_b[df_b["tipo"]==tipo].groupby("categoria")["valor"].sum().reset_index()
    if d.empty:
        col.info(f"Sem registros de {tipo}")
        return
    fig = px.pie(d, values="valor", names="categoria",
                 color_discrete_sequence=cores, hole=0.42,
                 title=f"{'📈' if tipo=='Entrada' else '📉'} {tipo}s por Categoria")
    fig.update_traces(textposition="inside", textinfo="percent+label",
                      hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>")
    fig.update_layout(height=340, margin=dict(l=0,r=0,t=40,b=0),
                      showlegend=False, paper_bgcolor="rgba(0,0,0,0)")
    col.plotly_chart(fig, use_container_width=True)

pizza(df, "Entrada", px.colors.sequential.Greens_r, p1)
pizza(df, "Saída",   px.colors.sequential.Oranges_r, p2)


# ─── Barras ───────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📊 Entradas vs Saídas por Categoria</div>', unsafe_allow_html=True)
comp = df.groupby(["categoria","tipo"])["valor"].sum().reset_index()
fig_bar = px.bar(
    comp, x="categoria", y="valor", color="tipo", barmode="group",
    color_discrete_map={"Entrada":"#28a745","Saída":"#e84a1f"},
    text_auto=".2s", labels={"valor":"Valor (R$)","categoria":"","tipo":""},
)
fig_bar.update_traces(textposition="outside",
                      hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>")
fig_bar.update_layout(
    height=300, margin=dict(l=0,r=0,t=8,b=0),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    yaxis=dict(tickprefix="R$ ", gridcolor="#f1f5f9"),
)
st.plotly_chart(fig_bar, use_container_width=True)


# ─── Mensal ───────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📆 Resumo Mensal + Saldo</div>', unsafe_allow_html=True)
piv = (
    df_all.groupby(["mes","tipo"])["valor"].sum().reset_index()
    .pivot(index="mes", columns="tipo", values="valor").fillna(0).reset_index()
)
piv["Saldo"] = piv.get("Entrada", 0) - piv.get("Saída", 0)
piv = piv.sort_values("mes")

fig_mes = make_subplots(specs=[[{"secondary_y": True}]])
for tipo, cor in [("Entrada","#28a745"),("Saída","#e84a1f")]:
    if tipo in piv.columns:
        fig_mes.add_trace(go.Bar(
            x=piv["mes"], y=piv[tipo], name=tipo,
            marker_color=cor, opacity=.85,
        ), secondary_y=False)
fig_mes.add_trace(go.Scatter(
    x=piv["mes"], y=piv["Saldo"], name="Saldo",
    line=dict(color="#2563eb", width=3, dash="dot"),
    mode="lines+markers+text",
    text=[fmt(v) for v in piv["Saldo"]],
    textposition="top center",
    textfont=dict(size=10, color="#2563eb"),
), secondary_y=True)
fig_mes.update_layout(
    barmode="group", height=320, margin=dict(l=0,r=0,t=8,b=0),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
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
                   color_discrete_sequence=[cor], labels={"valor":"R$","categoria":""})
    fig_h.update_traces(text=[fmt(v) for v in top["valor"]], textposition="outside")
    fig_h.update_layout(height=260, margin=dict(l=0,r=80,t=8,b=0),
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        showlegend=False,
                        xaxis=dict(tickprefix="R$ ", gridcolor="#f1f5f9"))
    col_w.plotly_chart(fig_h, use_container_width=True)


# ─── Últimos lançamentos ───────────────────────────────────────────────────────
st.markdown('<div class="section-title">🕐 Últimos Lançamentos</div>', unsafe_allow_html=True)
cols_show = [c for c in ["data","descricao","categoria","tipo","valor"] if c in df.columns]
show = df[cols_show].copy().sort_values("data", ascending=False).head(15).reset_index(drop=True)
show["data"] = show["data"].dt.strftime("%d/%m/%Y")
show["tipo"] = show["tipo"].apply(lambda x: "✅ Entrada" if x=="Entrada" else "🔴 Saída")
if "valor" in show.columns:
    show["valor"] = show["valor"].apply(fmt)
st.dataframe(show, use_container_width=True, height=300)

with st.expander("🗂️ Ver todos os registros"):
    show_all = df[cols_show].copy().sort_values("data", ascending=False).reset_index(drop=True)
    show_all["data"] = show_all["data"].dt.strftime("%d/%m/%Y")
    show_all["tipo"] = show_all["tipo"].apply(lambda x: "✅ Entrada" if x=="Entrada" else "🔴 Saída")
    if "valor" in show_all.columns:
        show_all["valor"] = show_all["valor"].apply(fmt)
    st.dataframe(show_all, use_container_width=True, height=400)


# ─── Auto-refresh ──────────────────────────────────────────────────────────────
if auto:
    time.sleep(intervalo)
    st.cache_data.clear()
    st.rerun()
