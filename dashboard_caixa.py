import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import hashlib, time

# ─── Configuração da página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="CaixaViva — Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _h(s): return hashlib.sha256(s.encode()).hexdigest()

CLIENTES = {
    "demo": {
        "senha_hash": _h("demo123"),
        "nome": "Empresa Demo",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms/export?format=csv&gid=0",
        "cor": "#2563eb",
    },
    # ── Adicionar clientes reais abaixo ───────────────────────────────────
    # "loja_silva": {
    #     "senha_hash": _h("senha_do_cliente"),
    #     "nome": "Loja Silva & Filhos",
    #     "sheet_url": "https://docs.google.com/spreadsheets/d/ID_DA_PLANILHA_DELES/export?format=csv&gid=0",
    #     "cor": "#16a34a",
    # },
}

# ─── CSS ──────────────────────────────────────────────────────────────────────
def inject_css(cor_cliente: str = "#2563eb"):
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {{ font-family:'Inter',sans-serif; }}

    /* ── Login ── */
    .login-wrap {{
        max-width:420px; margin:80px auto 0;
        background:#fff; border-radius:20px;
        padding:48px 40px; box-shadow:0 8px 40px rgba(0,0,0,.10);
    }}
    .login-logo {{ font-size:40px; text-align:center; margin-bottom:8px; }}
    .login-title {{ font-size:24px; font-weight:700; text-align:center; color:#0f172a; }}
    .login-sub {{ font-size:14px; color:#64748b; text-align:center; margin-bottom:28px; }}

    /* ── KPIs ── */
    .kpi {{
        border-radius:16px; padding:22px 24px; color:#fff;
        box-shadow:0 4px 20px rgba(0,0,0,.10);
    }}
    .kpi.green  {{ background:linear-gradient(135deg,#15803d,#22c55e); }}
    .kpi.red    {{ background:linear-gradient(135deg,#991b1b,#ef4444); }}
    .kpi.blue   {{ background:linear-gradient(135deg,#1e40af,{cor_cliente}); }}
    .kpi.slate  {{ background:linear-gradient(135deg,#334155,#64748b); }}
    .kpi-label  {{ font-size:11px; font-weight:700; opacity:.75; letter-spacing:1px; text-transform:uppercase; }}
    .kpi-value  {{ font-size:30px; font-weight:700; margin-top:6px; line-height:1; }}
    .kpi-sub    {{ font-size:12px; opacity:.65; margin-top:5px; }}

    /* ── Seções ── */
    .sec {{
        font-size:15px; font-weight:700; color:#0f172a;
        margin:24px 0 8px; padding-left:12px;
        border-left:4px solid {cor_cliente};
    }}

    /* ── Live badge ── */
    .live {{
        display:inline-flex; align-items:center; gap:6px;
        background:#dcfce7; color:#15803d; border-radius:99px;
        padding:4px 14px; font-size:12px; font-weight:700;
    }}
    .dot {{ width:8px; height:8px; background:#22c55e;
            border-radius:50%; animation:blink 1.4s infinite; }}
    @keyframes blink {{ 0%,100%{{opacity:1}} 50%{{opacity:.2}} }}

    /* ── Tabela ── */
    [data-testid="stDataFrame"] {{ border-radius:12px; overflow:hidden; }}
    </style>
    """, unsafe_allow_html=True)


# ─── Funções ──────────────────────────────────────────────────────────────────
def load_data(url: str) -> pd.DataFrame:
    # sem cache — sempre busca direto do Sheets
    df = pd.read_csv(url + f"&cachebust={int(time.time())}")
    df.columns = df.columns.str.strip()
    col_map = {}
    for c in df.columns:
        cl = c.lower()
        if   "data"  in cl:                  col_map[c] = "data"
        elif "escri" in cl or "desc" in cl:  col_map[c] = "descricao"
        elif "egori" in cl:                  col_map[c] = "categoria"
        elif "tipo"  in cl:                  col_map[c] = "tipo"
        elif "alor"  in cl:                  col_map[c] = "valor"
    df = df.rename(columns=col_map)
    df["data"]  = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
    df["valor"] = pd.to_numeric(
        df["valor"].astype(str)
          .str.replace("R$","",regex=False).str.replace(".","",regex=False)
          .str.replace(",",".",regex=False).str.strip(),
        errors="coerce").fillna(0)
    df["tipo"] = df["tipo"].astype(str).str.strip().str.title()
    df = df.dropna(subset=["data"])
    df["mes"] = df["data"].dt.to_period("M").astype(str)
    df["dia"] = df["data"].dt.date
    return df

def fmt(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")

def check_login(usuario: str, senha: str) -> bool:
    u = CLIENTES.get(usuario)
    return u is not None and u["senha_hash"] == _h(senha)


# ══════════════════════════════════════════════════════════════════════════════
#  TELA DE LOGIN
# ══════════════════════════════════════════════════════════════════════════════
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.usuario   = ""

inject_css()   # CSS básico para o login

if not st.session_state.logged_in:
    st.markdown("""
    <div class="login-wrap">
        <div class="login-logo">💰</div>
        <div class="login-title">CaixaViva</div>
        <div class="login-sub">Dashboard financeiro em tempo real</div>
    </div>
    """, unsafe_allow_html=True)

    # Centraliza o formulário
    col_l, col_c, col_r = st.columns([1, 1.4, 1])
    with col_c:
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        usuario = st.text_input("Usuário", placeholder="seu_usuario", label_visibility="visible")
        senha   = st.text_input("Senha",   placeholder="••••••••", type="password")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        entrar  = st.button("Entrar →", use_container_width=True, type="primary")

        if entrar:
            if check_login(usuario.strip(), senha.strip()):
                st.session_state.logged_in = True
                st.session_state.usuario   = usuario.strip()
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

        st.markdown(
            "<p style='text-align:center;color:#94a3b8;font-size:12px;margin-top:20px'>"
            "Acesso exclusivo para clientes</p>",
            unsafe_allow_html=True
        )
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD (só chega aqui se estiver logado)
# ══════════════════════════════════════════════════════════════════════════════
cliente = CLIENTES[st.session_state.usuario]
inject_css(cliente["cor"])   # reaplica CSS com cor do cliente

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### 👤 {cliente['nome']}")
    st.markdown('<span class="live"><span class="dot"></span>AO VIVO</span>',
                unsafe_allow_html=True)
    st.caption("Conectado ao Google Sheets")
    st.divider()

    auto = st.toggle("🔄 Atualização automática", value=True)
    if auto:
        intervalo = st.slider("Intervalo (seg)", 3, 30, 5)
    else:
        if st.button("↺ Atualizar agora", use_container_width=True):
            st.cache_data.clear(); st.rerun()

    st.divider()
    st.subheader("📅 Período")
    periodo = st.selectbox("", [
        "Hoje", "Últimos 7 dias", "Últimos 30 dias",
        "Últimos 90 dias", "Este mês", "Mês anterior", "Todo o histórico"
    ], index=2, label_visibility="collapsed")

    hoje = datetime.today().date()
    if   periodo == "Hoje":             ini = hoje
    elif periodo == "Últimos 7 dias":   ini = hoje - timedelta(days=7)
    elif periodo == "Últimos 30 dias":  ini = hoje - timedelta(days=30)
    elif periodo == "Últimos 90 dias":  ini = hoje - timedelta(days=90)
    elif periodo == "Este mês":         ini = hoje.replace(day=1)
    elif periodo == "Mês anterior":
        p = hoje.replace(day=1)
        ini  = (p - timedelta(days=1)).replace(day=1)
        hoje = p - timedelta(days=1)
    else:                               ini = datetime(2000,1,1).date()

    st.divider()
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.usuario   = ""
        st.cache_data.clear()
        st.rerun()

    st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}")


# ─── Carrega dados ────────────────────────────────────────────────────────────
try:
    df_all = load_data(cliente["sheet_url"])
except Exception as e:
    st.error("**Erro ao carregar a planilha.**\n\n"
             "Verifique se o acesso está como **'Qualquer pessoa com o link'**.")
    st.code(str(e))
    st.stop()

# ─── DEBUG ────────────────────────────────────────────────────────────────────
with st.expander("🔍 Debug — clique aqui se os dados não aparecerem"):
    st.write(f"**Total de linhas lidas:** `{len(df_all)}`")
    st.write(f"**Colunas detectadas:** `{list(df_all.columns)}`")
    if "tipo" in df_all.columns:
        st.write(f"**Valores únicos em Tipo:** `{df_all['tipo'].unique().tolist()}`")
        st.caption("⚠️ Tipo precisa ser exatamente `Entrada` ou `Saída` (com acento)")
    if "data" in df_all.columns:
        st.write(f"**Datas — mín/máx:** `{df_all['dia'].min()}` → `{df_all['dia'].max()}`")
    st.write("**Primeiras 10 linhas:**")
    st.dataframe(df_all.head(10))

df = df_all[(df_all["dia"] >= ini) & (df_all["dia"] <= hoje)].copy()

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown(f"""
# 📊 Dashboard de Caixa
<p style='color:#64748b;font-size:13px;margin-top:-10px'>
  {cliente['nome']} &nbsp;|&nbsp;
  {ini.strftime('%d/%m/%Y')} → {hoje.strftime('%d/%m/%Y')} &nbsp;|&nbsp;
  ⏱ {datetime.now().strftime('%H:%M:%S')}
</p>
""", unsafe_allow_html=True)

if df.empty:
    st.warning("Nenhum registro no período. Adicione dados na planilha!")
    st.stop()

# ─── KPIs ─────────────────────────────────────────────────────────────────────
entradas = df[df["tipo"] == "Entrada"]["valor"].sum()
saidas   = df[df["tipo"] == "Saída"]["valor"].sum()
saldo    = entradas - saidas
n_reg    = len(df)

c1, c2, c3, c4 = st.columns(4)
c1.markdown(f'<div class="kpi green"><div class="kpi-label">📈 Entradas</div><div class="kpi-value">{fmt(entradas)}</div><div class="kpi-sub">{df[df["tipo"]=="Entrada"].shape[0]} lançamentos</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="kpi red"><div class="kpi-label">📉 Saídas</div><div class="kpi-value">{fmt(saidas)}</div><div class="kpi-sub">{df[df["tipo"]=="Saída"].shape[0]} lançamentos</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="kpi {"blue" if saldo >= 0 else "red"}"><div class="kpi-label">💼 Saldo</div><div class="kpi-value">{fmt(saldo)}</div><div class="kpi-sub">{"✅ Positivo" if saldo >= 0 else "⚠️ Negativo"}</div></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="kpi slate"><div class="kpi-label">📋 Registros</div><div class="kpi-value">{n_reg}</div><div class="kpi-sub">no período</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Fluxo diário ─────────────────────────────────────────────────────────────
st.markdown('<div class="sec">📅 Fluxo de Caixa Diário</div>', unsafe_allow_html=True)
diario = (
    df.groupby(["dia","tipo"])["valor"].sum().reset_index()
    .pivot(index="dia", columns="tipo", values="valor").fillna(0).reset_index()
)
fig_flux = go.Figure()
for tipo, cor, fill in [
    ("Entrada","#22c55e","rgba(34,197,94,.13)"),
    ("Saída",  "#ef4444","rgba(239,68,68,.13)"),
]:
    if tipo in diario.columns:
        fig_flux.add_trace(go.Scatter(
            x=diario["dia"], y=diario[tipo], name=tipo,
            line=dict(color=cor, width=2.5),
            fill="tozeroy", fillcolor=fill,
            hovertemplate=f"<b>{tipo}</b><br>%{{x}}<br>R$ %{{y:,.2f}}<extra></extra>"
        ))
fig_flux.update_layout(
    height=270, margin=dict(l=0,r=0,t=8,b=0),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    yaxis=dict(tickprefix="R$ ", gridcolor="#f1f5f9"),
    hovermode="x unified"
)
st.plotly_chart(fig_flux, use_container_width=True)

# ─── Pizzas ───────────────────────────────────────────────────────────────────
st.markdown('<div class="sec">🍕 Composição por Categoria</div>', unsafe_allow_html=True)
p1, p2 = st.columns(2)

def pizza(df_b, tipo, cores, col):
    d = df_b[df_b["tipo"]==tipo].groupby("categoria")["valor"].sum().reset_index()
    if d.empty:
        col.info(f"Sem registros de {tipo} no período.")
        return
    fig = px.pie(d, values="valor", names="categoria",
                 color_discrete_sequence=cores, hole=0.44,
                 title=f"{'📈' if tipo=='Entrada' else '📉'} {tipo}s")
    fig.update_traces(textposition="inside", textinfo="percent+label",
                      hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>")
    fig.update_layout(height=320, margin=dict(l=0,r=0,t=36,b=0),
                      showlegend=False, paper_bgcolor="rgba(0,0,0,0)")
    col.plotly_chart(fig, use_container_width=True)

pizza(df, "Entrada", px.colors.sequential.Greens_r, p1)
pizza(df, "Saída",   px.colors.sequential.Reds_r,   p2)

# ─── Barras ───────────────────────────────────────────────────────────────────
st.markdown('<div class="sec">📊 Entradas vs Saídas por Categoria</div>', unsafe_allow_html=True)
comp = df.groupby(["categoria","tipo"])["valor"].sum().reset_index()
if not comp.empty:
    fig_bar = px.bar(
        comp, x="categoria", y="valor", color="tipo", barmode="group",
        color_discrete_map={"Entrada":"#22c55e","Saída":"#ef4444"},
        text_auto=".2s", labels={"valor":"","categoria":"","tipo":""},
    )
    fig_bar.update_traces(textposition="outside",
                          hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>")
    fig_bar.update_layout(
        height=290, margin=dict(l=0,r=0,t=8,b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        yaxis=dict(tickprefix="R$ ", gridcolor="#f1f5f9"),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ─── Mensal ───────────────────────────────────────────────────────────────────
st.markdown('<div class="sec">📆 Resumo Mensal + Saldo</div>', unsafe_allow_html=True)
piv = (
    df_all.groupby(["mes","tipo"])["valor"].sum().reset_index()
    .pivot(index="mes", columns="tipo", values="valor").fillna(0).reset_index()
)
piv["Saldo"] = piv.get("Entrada", 0) - piv.get("Saída", 0)
piv = piv.sort_values("mes")

fig_mes = make_subplots(specs=[[{"secondary_y": True}]])
for tipo, cor in [("Entrada","#22c55e"),("Saída","#ef4444")]:
    if tipo in piv.columns:
        fig_mes.add_trace(go.Bar(x=piv["mes"], y=piv[tipo], name=tipo,
                                 marker_color=cor, opacity=.85), secondary_y=False)
fig_mes.add_trace(go.Scatter(
    x=piv["mes"], y=piv["Saldo"], name="Saldo",
    line=dict(color=cliente["cor"], width=3, dash="dot"),
    mode="lines+markers+text",
    text=[fmt(v) for v in piv["Saldo"]],
    textposition="top center", textfont=dict(size=10, color=cliente["cor"]),
), secondary_y=True)
fig_mes.update_layout(
    barmode="group", height=310, margin=dict(l=0,r=0,t=8,b=0),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
)
fig_mes.update_yaxes(tickprefix="R$ ", gridcolor="#f1f5f9", secondary_y=False)
fig_mes.update_yaxes(tickprefix="R$ ", showgrid=False, secondary_y=True)
st.plotly_chart(fig_mes, use_container_width=True)

# ─── Top categorias ───────────────────────────────────────────────────────────
st.markdown('<div class="sec">🏆 Top Categorias</div>', unsafe_allow_html=True)
ta, tb = st.columns(2)
for col_w, tipo, cor in [(ta,"Entrada","#22c55e"),(tb,"Saída","#ef4444")]:
    top = (df[df["tipo"]==tipo].groupby("categoria")["valor"]
           .sum().sort_values(ascending=True).tail(6).reset_index())
    if top.empty:
        col_w.info(f"Sem dados de {tipo}")
        continue
    fig_h = px.bar(top, x="valor", y="categoria", orientation="h",
                   color_discrete_sequence=[cor], labels={"valor":"","categoria":""})
    fig_h.update_traces(text=[fmt(v) for v in top["valor"]], textposition="outside")
    fig_h.update_layout(height=240, margin=dict(l=0,r=80,t=8,b=0),
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        showlegend=False,
                        xaxis=dict(tickprefix="R$ ", gridcolor="#f1f5f9"))
    col_w.plotly_chart(fig_h, use_container_width=True)

# ─── Últimos lançamentos ───────────────────────────────────────────────────────
st.markdown('<div class="sec">🕐 Últimos Lançamentos</div>', unsafe_allow_html=True)
cols_show = [c for c in ["data","descricao","categoria","tipo","valor"] if c in df.columns]
show = df[cols_show].copy().sort_values("data", ascending=False).head(15).reset_index(drop=True)
show["data"]  = show["data"].dt.strftime("%d/%m/%Y")
show["tipo"]  = show["tipo"].apply(lambda x: "✅ Entrada" if x=="Entrada" else "🔴 Saída")
if "valor" in show.columns:
    show["valor"] = show["valor"].apply(fmt)
st.dataframe(show, use_container_width=True, height=310)

with st.expander("🗂️ Ver todos os registros do período"):
    all_show = df[cols_show].copy().sort_values("data", ascending=False).reset_index(drop=True)
    all_show["data"] = all_show["data"].dt.strftime("%d/%m/%Y")
    all_show["tipo"] = all_show["tipo"].apply(lambda x: "✅ Entrada" if x=="Entrada" else "🔴 Saída")
    if "valor" in all_show.columns:
        all_show["valor"] = all_show["valor"].apply(fmt)
    st.dataframe(all_show, use_container_width=True, height=400)

# ─── Auto-refresh ──────────────────────────────────────────────────────────────
if auto:
    time.sleep(intervalo)
    st.cache_data.clear()
    st.rerun()
