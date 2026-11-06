"""
page_1.py — Visão de Envios do Portal LEVES.

V7 — renovação visual da área interna, mantendo a mesma lógica de dados,
filtros, gráficos, multi-tenant e exportação CSV.
"""

from __future__ import annotations

import html
import plotly.express as px
import streamlit as st

import data_processing as dp

AZUL = "#0067fc"
FUNDO = "#f7f9fc"
BORDA = "#e5eaf1"
TEXTO = "#172033"
CINZA = "#6f7b8c"


def _fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")

def _icone_tipo(tipo: str) -> str:
    mapa = {
        "gaylord": "📦",
        "pallet": "▦",
        "saca": "👜",
        "caixa": "📦",
        "etiqueta": "🏷️",
    }
    return mapa.get(str(tipo).strip().lower(), "📦")


def _injetar_css():
    st.markdown(
        """
<style>
/* ============================================================
   PORTAL LEVES — ÁREA INTERNA V7
   ============================================================ */
/* Remove a barra superior padrão do Streamlit */
[data-testid="stHeader"] {
    display: none !important;
}

[data-testid="stToolbar"] {
    display: none !important;
}

[data-testid="stAppViewContainer"] {
    background: #f7f9fc !important;
}

[data-testid="stAppViewBlockContainer"] {
    padding-top: 12px !important;
    padding-bottom: 40px !important;
}
/* Cabeçalho */
.leves-breadcrumb {
    color: #8a95a5;
    font-family: Montserrat, sans-serif;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: .3px;
    margin-bottom: 7px;
}

.leves-page-title {
    color: #172033;
    font-family: Montserrat, sans-serif;
    font-size: 32px;
    line-height: 1.15;
    font-weight: 800;
    letter-spacing: -1px;
    margin: 0;
}

.leves-page-title span {
    color: #0067fc;
}
.leves-page-description {
    color: #697587;
    font-family: Montserrat, sans-serif;
    font-size: 14px;
    line-height: 1.6;
    margin-top: 8px;
    margin-bottom: 20px;
}

/* Blocos */
.leves-section-label {
    color: #253044;
    font-family: Montserrat, sans-serif;
    font-size: 14px;
    font-weight: 700;
    margin: 4px 0 10px 0;
}
/* KPIs */
.leves-kpi {
    background: #ffffff;
    border: 1px solid #e5eaf1;
    border-radius: 16px;
    padding: 15px 17px 14px 17px;
    min-height: 96px;
    box-shadow: 0 5px 18px rgba(23, 32, 51, .035);
    box-sizing: border-box;
}

.leves-kpi-top {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #788497;
    font-family: Montserrat, sans-serif;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .45px;
}
.leves-kpi-icon {
    width: 25px;
    height: 25px;
    border-radius: 8px;
    background: #eef6ff;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
}

.leves-kpi-value {
    color: #172033;
    font-family: Montserrat, sans-serif;
    font-size: 28px;
    line-height: 1;
    font-weight: 700;
    margin-top: 11px;
}

.leves-kpi-sub {
    color: #a0a9b6;
    font-family: Montserrat, sans-serif;
    font-size: 10px;
    margin-top: 5px;
}
/* Espaçamento dos widgets */
div[data-testid="stHorizontalBlock"] {
    gap: 16px;
}

/* Selectbox / multiselect */
[data-baseweb="select"] > div {
    border-color: #dfe5ed !important;
    border-radius: 10px !important;
    background: #ffffff !important;
}

[data-baseweb="select"] > div:hover {
    border-color: #b9c7d8 !important;
}
[data-testid="stWidgetLabel"] p {
    color: #536074 !important;
    font-family: Montserrat, sans-serif !important;
    font-size: 12px !important;
    font-weight: 600 !important;
}

/* Dashboard de envios — visual compacto e corporativo */
.leves-chart-title { color:#102B50 !important; font-family:Montserrat,sans-serif !important; font-size:17px !important; font-weight:800 !important; margin:0 0 8px 0 !important; }
.leves-kpi { min-height:112px !important; display:flex; flex-direction:column; justify-content:center; }
.leves-kpi-total { background:linear-gradient(135deg,#0873F9 0%,#0758DB 100%) !important; border-color:#0873F9 !important; }
.leves-kpi-total .leves-kpi-top,.leves-kpi-total .leves-kpi-value,.leves-kpi-total .leves-kpi-sub { color:#FFFFFF !important; }
.leves-kpi-total .leves-kpi-icon { color:#FFFFFF !important; background:rgba(255,255,255,.18) !important; }
.leves-table-heading { color:#102B50; font-family:Montserrat,sans-serif; font-size:17px; font-weight:800; margin:0 0 10px 0; }
[data-testid="stDataFrame"] { border:1px solid #E0EAF8; border-radius:12px; overflow:hidden; }
[data-testid="stTextInput"] input { border-radius:10px !important; border-color:#D6E2F2 !important; }
[data-testid="stDownloadButton"] button { border-radius:10px !important; border:1px solid #D6E2F2 !important; color:#075BEA !important; font-weight:700 !important; }

/* Cards dos gráficos */
.leves-chart-card {
    background: #ffffff;
    border: 1px solid #e5eaf1;
    border-radius: 16px;
    padding: 13px 14px 5px 14px;
    box-shadow: 0 5px 18px rgba(23, 32, 51, .035);
    min-height: 345px;
}
.leves-chart-title {
    color: #253044;
    font-family: Montserrat, sans-serif;
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 2px;
}

/* Tabela */
[data-testid="stExpander"] {
    border: 1px solid #e5eaf1 !important;
    border-radius: 14px !important;
    background: #ffffff !important;
}

[data-testid="stExpander"] summary {
    color: #334056 !important;
    font-family: Montserrat, sans-serif !important;
    font-weight: 600 !important;
}
/* Avisos */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    font-family: Montserrat, sans-serif !important;
}

@media (max-width: 900px) {
    .leves-page-title { font-size: 29px; }
    .leves-kpi { min-height: 96px; }
}

/* Identidade visual Loggi — painel de envios */
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 35% 24% at 100% 0%, rgba(0,185,238,.10), transparent 72%),
        #F3F7FD !important;
}
[data-testid="stAppViewBlockContainer"] {
    max-width: 100% !important;
    padding: 26px clamp(24px, 3vw, 54px) 42px !important;
}
.leves-breadcrumb {
    color: #7386A3 !important;
    font-size: 11px !important;
    letter-spacing: .55px !important;
    margin-bottom: 9px !important;
}
.leves-page-title {
    color: #102B50 !important;
    font-size: clamp(29px, 2.3vw, 36px) !important;
    letter-spacing: -1.2px !important;
}
.leves-page-description {
    color: #647895 !important;
    font-size: 13px !important;
    margin-top: 5px !important;
    margin-bottom: 22px !important;
}
.leves-filter-heading {
    color: #102B50;
    font-family: Montserrat, sans-serif;
    font-size: 17px;
    font-weight: 800;
    margin: 0 0 12px 0;
}
.leves-filter-heading span,
.leves-summary-heading:first-letter {
    color: #0866F5;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF !important;
    border: 1px solid #DFE9F7 !important;
    border-radius: 17px !important;
    box-shadow: 0 7px 22px rgba(22, 65, 125, .055) !important;
}
.leves-section-label {
    color: #102B50 !important;
    font-size: 16px !important;
    font-weight: 800 !important;
    margin: 18px 0 12px !important;
}
.leves-summary-heading {
    margin-top: 18px !important;
}
.leves-kpi {
    border: 1px solid #E0EAF8 !important;
    border-radius: 17px !important;
    padding: 17px 19px 15px !important;
    min-height: 116px !important;
    box-shadow: 0 7px 20px rgba(24, 70, 130, .055) !important;
}
.leves-kpi-total {
    background: linear-gradient(135deg, #DDF1FF 0%, #C6E5FF 100%) !important;
    border-color: #C8E5FF !important;
}
.leves-kpi-top {
    color: #496486 !important;
    font-size: 11px !important;
    letter-spacing: .35px !important;
}
.leves-kpi-icon {
    color: #0875F5 !important;
    background: rgba(255,255,255,.72) !important;
    width: 30px !important;
    height: 30px !important;
    border-radius: 50% !important;
}
.leves-kpi-value {
    color: #102B50 !important;
    font-size: 32px !important;
    font-weight: 800 !important;
    margin-top: 9px !important;
}
.leves-kpi-sub {
    color: #7186A4 !important;
    font-size: 11px !important;
}
.leves-chart-title {
    color: #102B50 !important;
    font-size: 16px !important;
    font-weight: 800 !important;
    margin: 1px 0 7px !important;
}
[data-baseweb="select"] > div {
    border: 1px solid #D6E2F2 !important;
    border-radius: 10px !important;
    min-height: 42px !important;
    box-shadow: none !important;
}
[data-baseweb="select"] > div:focus-within {
    border-color: #0866F5 !important;
    box-shadow: 0 0 0 2px rgba(8,102,245,.10) !important;
}
[data-testid="stWidgetLabel"] p {
    color: #344B6B !important;
    font-size: 12px !important;
    font-weight: 700 !important;
}
[data-testid="stExpander"] {
    border-color: #DFE9F7 !important;
    box-shadow: 0 5px 16px rgba(24,70,130,.035) !important;
}
@media (max-width: 900px) {
    [data-testid="stAppViewBlockContainer"] {
        padding: 20px 16px 32px !important;
    }
    .leves-kpi-value { font-size: 27px !important; }
}

/* Ajustes finais: conteúdo mais alto, filtros destacados e paleta 100% azul. */
[data-testid="stAppViewBlockContainer"] {
    padding-top: 7px !important;
    padding-bottom: 32px !important;
}
.leves-breadcrumb {
    margin-top: 0 !important;
    margin-bottom: 5px !important;
}
.leves-page-title {
    margin-top: 0 !important;
    line-height: 1.08 !important;
}
.leves-page-description {
    margin-top: 4px !important;
    margin-bottom: 13px !important;
    line-height: 1.4 !important;
}
/* O cartão que contém os filtros fica branco, separado do fundo da página. */
[data-testid="stVerticalBlockBorderWrapper"]:has(.leves-filter-heading) {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    border: 1px solid #DCE8F8 !important;
    border-radius: 16px !important;
    box-shadow: 0 7px 22px rgba(22,65,125,.07) !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:has(.leves-filter-heading) > div {
    background: #FFFFFF !important;
}
.leves-filter-heading {
    margin-bottom: 8px !important;
}
.leves-section-label {
    margin-top: 12px !important;
    margin-bottom: 9px !important;
}
.leves-summary-heading {
    margin-top: 13px !important;
}
/* Evita excesso de espaço antes dos gráficos após os KPIs. */
.leves-kpi {
    min-height: 108px !important;
}

/* Remove o contorno cinza que envolve toda a área principal. */
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewBlockContainer"],
section.main,
section.main > div,
.main .block-container {
    border: 0 !important;
    outline: 0 !important;
    box-shadow: none !important;
}
/* O fundo branco é exclusivo do cartão de filtros. */
.st-key-filters_card,
.st-key-filters_card [data-testid="stVerticalBlockBorderWrapper"],
.st-key-filters_card [data-testid="stVerticalBlock"],
.st-key-filters_card [data-testid="stHorizontalBlock"],
.st-key-filters_card [data-testid="stElementContainer"] {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
}
.st-key-filters_card {
    border: 1px solid #DCE8F8 !important;
    border-radius: 16px !important;
    padding: 14px 16px !important;
    box-shadow: 0 7px 22px rgba(22,65,125,.07) !important;
}
.st-key-filters_card [data-testid="stVerticalBlockBorderWrapper"] {
    border: 0 !important;
    box-shadow: none !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def page_1():
    _injetar_css()

    user = st.session_state.get("usuario") or {}
    eh_admin = user.get("perfil") == "admin"
    eh_gdl = user.get("perfil") == "gdl"
    # ============================================================
    # Cabeçalho
    # ============================================================
    st.markdown(
        '<div class="leves-breadcrumb">PORTAL LEVES &nbsp;/&nbsp; ENVIOS</div>',
        unsafe_allow_html=True,
    )

    titulo = "Visão geral dos envios" if (eh_admin or eh_gdl) else "Insumos enviados para você"
    st.markdown(
        f'<div class="leves-page-title">{html.escape(titulo)}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="leves-page-description">'
        "Consulte e acompanhe os insumos enviados para sua operação. "
        "Use os filtros abaixo para analisar o período desejado."
        "</div>",
        unsafe_allow_html=True,
    )

    df = dp.envios_do_usuario(user)
    if df.empty:
        st.info(
            "Nenhum envio encontrado."
            if (eh_admin or eh_gdl)
            else "Nenhum envio encontrado para a sua operação."
        )
        return
    # ============================================================
    # Filtros
    # ============================================================
    with st.container(border=True, key="filters_card"):
        st.markdown(
            '<div class="leves-filter-heading"><span>⚙</span> Filtros</div>',
            unsafe_allow_html=True,
        )
        fcol1, fcol2, fcol3 = st.columns([1, 1.1, 1.4])
        meses = sorted(df["mes"].unique(), reverse=True)
        rotulos = {m: dp.rotulo_mes(m) for m in meses}
        opcoes = ["Todo o período"] + [rotulos[m] for m in meses]
        escolha = fcol1.selectbox(
            "Período",
            opcoes,
            index=1 if meses else 0,
        )
    
        tipos_disp = sorted(df["tipo"].unique())
        sel_tipos = fcol2.multiselect(
            "Tipo de insumo",
            tipos_disp,
            default=tipos_disp,
        )
    
        if eh_admin or eh_gdl:
            operacoes_disp = sorted(df["destino"].dropna().astype(str).unique())
            sel_operacoes = fcol3.multiselect(
                "Operação",
                operacoes_disp,
                default=operacoes_disp,
            )
        else:
            sel_operacoes = []
    
    dfx = df.copy()
    if escolha != "Todo o período":
        mes_sel = next(m for m, r in rotulos.items() if r == escolha)
        dfx = dfx[dfx["mes"] == mes_sel]
    if sel_tipos:
        dfx = dfx[dfx["tipo"].isin(sel_tipos)]
    if eh_admin or eh_gdl:
        if sel_operacoes:
            dfx = dfx[dfx["destino"].isin(sel_operacoes)]
    if dfx.empty:
        st.warning("Sem dados para os filtros selecionados.")
        return

    # ============================================================
    # KPIs
    # ============================================================
    st.markdown('<div class="leves-section-label leves-summary-heading">▦ &nbsp; Resumo do período</div>', unsafe_allow_html=True)

    total_geral = int(dfx["total"].sum())
    por_tipo = dfx.groupby("tipo")["total"].sum().to_dict()
    ordem_tipos = ["SACA", "GAYLORD", "PALLET"]
    tipos_kpi = [t for t in ordem_tipos if t in set(dfx["tipo"])]
    tipos_kpi += [t for t in sorted(dfx["tipo"].unique()) if t not in tipos_kpi]
    nomes_tipo = {"SACA": "Sacas", "GAYLORD": "Gaylords", "PALLET": "Pallets"}
    kpis = [("Total de insumos", total_geral, "🚚", "no período")]
    for t in tipos_kpi:
        kpis.append((nomes_tipo.get(t, str(t).title()), por_tipo.get(t, 0), "", "enviados"))

    cols = st.columns(len(kpis))
    for idx, (col, (nome, valor, icone, subtitulo)) in enumerate(zip(cols, kpis)):
        with col:
            classe_total = "leves-kpi-total" if idx == 0 else ""
            st.markdown(
                f'<div class="leves-kpi {classe_total}"><div class="leves-kpi-top">'
                f'<span class="leves-kpi-icon" style="display:{"inline-flex" if icone else "none"};">{icone}</span>'
                f'{html.escape(nome)}</div><div class="leves-kpi-value">{_fmt(valor)}</div>'
                f'<div class="leves-kpi-sub">{html.escape(subtitulo)}</div></div>',
                unsafe_allow_html=True,
            )

    # Distribuição por tipo e evolução diária
    st.markdown('<div style="height:15px"></div>', unsafe_allow_html=True)
    g1, g2 = st.columns([0.88, 1.22], gap="large")
    paleta = {"SACA": "#0866F5", "GAYLORD": "#16B9ED", "PALLET": "#8DD8FA"}
    for tipo in dfx["tipo"].unique():
        paleta.setdefault(tipo, "#6D9FE8")

    tdf = dfx.groupby("tipo", as_index=False)["total"].sum().query("total > 0").sort_values("total", ascending=False)
    with g1:
        with st.container(border=True):
            st.markdown('<div class="leves-chart-title">Distribuição por tipo de insumo</div>', unsafe_allow_html=True)
            if not tdf.empty:
                fig_tipo = px.pie(tdf, names="tipo", values="total", hole=0.66, color="tipo", color_discrete_map=paleta)
                fig_tipo.update_traces(
                    texttemplate="%{percent:.1%}", textposition="inside",
                    textfont=dict(family="Montserrat", size=12, color="#FFFFFF"),
                    hovertemplate="<b>%{label}</b><br>Quantidade: %{value:,.0f}<br>Participação: %{percent}<extra></extra>",
                    sort=False,
                )
                fig_tipo.update_layout(
                    height=285, showlegend=True, font=dict(family="Montserrat", color="#243B5B", size=11),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=8, r=8, t=8, b=8),
                    legend=dict(orientation="v", y=0.5, yanchor="middle", x=1.02, xanchor="left"),
                    annotations=[dict(text=f"<b>{_fmt(total_geral)}</b><br><span style='font-size:11px'>insumos</span>",
                                      x=0.39, y=0.5, showarrow=False,
                                      font=dict(family="Montserrat", size=20, color="#102B50"))],
                )
                st.plotly_chart(fig_tipo, width="stretch", config={"displayModeBar": False})
            else:
                st.info("Não há quantidades para exibir.")

    ddf = dfx.groupby(["dia", "tipo"], as_index=False)["total"].sum()
    with g2:
        with st.container(border=True):
            st.markdown('<div class="leves-chart-title">Evolução dos envios (por dia)</div>', unsafe_allow_html=True)
            if not ddf.empty:
                fig_dia = px.line(ddf, x="dia", y="total", color="tipo", markers=True,
                                  color_discrete_map=paleta,
                                  labels={"dia": "Data", "total": "Quantidade", "tipo": "Tipo"})
                fig_dia.update_traces(
                    line=dict(width=3), marker=dict(size=7, line=dict(width=1.5, color="#FFFFFF")),
                    hovertemplate="<b>%{fullData.name}</b><br>%{x|%d/%m/%Y}<br>Quantidade: %{y:,.0f}<extra></extra>",
                )
                fig_dia.update_layout(
                    height=285, font=dict(family="Montserrat", color="#536789", size=11),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=12, r=12, t=8, b=8), hovermode="x unified",
                    xaxis=dict(title=None, showgrid=False, zeroline=False, tickformat="%d/%m", linecolor="#DCE6F3"),
                    yaxis=dict(title=None, rangemode="tozero", gridcolor="#E8EFF8", zeroline=False),
                    legend=dict(orientation="h", y=1.12, yanchor="bottom", x=1, xanchor="right",
                                font=dict(family="Montserrat", size=10, color="#344766")),
                )
                st.plotly_chart(fig_dia, width="stretch", config={"displayModeBar": False})
            else:
                st.info("Não há envios diários para exibir.")

    # Ranking de destinos + tabela detalhada
    st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
    if eh_admin:
        rank_col, table_col = st.columns([0.78, 1.22], gap="large")
    else:
        table_col = st.container()
        rank_col = None

    if eh_admin and rank_col is not None:
        with rank_col:
            with st.container(border=True):
                st.markdown('<div class="leves-chart-title">Top 10 destinos</div>', unsafe_allow_html=True)
                rank = (dfx.groupby("destino", as_index=False)["total"].sum()
                        .sort_values("total", ascending=False).head(10).sort_values("total", ascending=True))
                if not rank.empty:
                    fig_dest = px.bar(rank, x="total", y="destino", orientation="h", text="total",
                                      labels={"total": "Quantidade", "destino": "Destino"})
                    fig_dest.update_traces(
                        marker=dict(color=["#9CCBFF", "#8ABFFF", "#78B3FF", "#66A7FF", "#559BFF",
                                           "#438DFA", "#327FF2", "#2072E9", "#1166E0", "#075BEA"][-len(rank):]),
                        texttemplate="%{x:,.0f}", textposition="outside",
                        textfont=dict(family="Montserrat", size=11, color="#102B50"), cliponaxis=False,
                        hovertemplate="<b>%{y}</b><br>Quantidade: %{x:,.0f}<extra></extra>",
                    )
                    fig_dest.update_layout(
                        height=335, font=dict(family="Montserrat", color="#536789", size=11),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=8, r=32, t=8, b=8),
                        xaxis=dict(title=None, showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(title=None, showgrid=False, zeroline=False, autorange="reversed"),
                    )
                    st.plotly_chart(fig_dest, width="stretch", config={"displayModeBar": False})
                else:
                    st.info("Não há destinos para classificar.")

    with table_col:
        with st.container(border=True):
            st.markdown('<div class="leves-table-heading">Detalhamento dos envios</div>', unsafe_allow_html=True)
            busca = st.text_input("Buscar destino, operação ou tipo", placeholder="Buscar destino...",
                                  label_visibility="collapsed", key="busca_envios_detalhados")
            cols_tab = ["dt", "destino", "tipo", "total"] if (eh_admin or eh_gdl) else ["dt", "tipo", "total"]
            tab = dfx[cols_tab].copy()
            if busca.strip():
                termo = busca.strip().lower()
                colunas_busca = [col for col in ["destino", "tipo"] if col in tab.columns]
                mask = False
                for coluna in colunas_busca:
                    mask = mask | tab[coluna].astype(str).str.lower().str.contains(termo, na=False)
                tab = tab[mask]
            tab = tab.sort_values("dt", ascending=False).copy()
            tab["dt"] = tab["dt"].dt.strftime("%d/%m/%Y")
            tab = tab.rename(columns={"dt": "Data", "tipo": "Tipo de insumo",
                                      "destino": "Destino", "total": "Quantidade"})
            st.dataframe(tab, width="stretch", hide_index=True, height=335)
            st.download_button("Baixar CSV", tab.to_csv(index=False).encode("utf-8-sig"),
                               file_name="ativos_leves.csv", mime="text/csv", key="dl_envios")

