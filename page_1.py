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
</style>
        """,
        unsafe_allow_html=True,
    )


def page_1():
    _injetar_css()

    user = st.session_state.get("usuario") or {}
    eh_admin = user.get("perfil") == "admin"

    # ============================================================
    # Cabeçalho
    # ============================================================
    st.markdown(
        '<div class="leves-breadcrumb">PORTAL LEVES &nbsp;/&nbsp; ENVIOS</div>',
        unsafe_allow_html=True,
    )

    titulo = "Visão geral dos envios" if eh_admin else "Insumos enviados para você"
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
            if eh_admin
            else "Nenhum envio encontrado para a sua operação."
        )
        return

    # ============================================================
    # Filtros
    # ============================================================
    st.markdown('<div class="leves-section-label">Filtros</div>', unsafe_allow_html=True)

    fcol1, fcol2 = st.columns([1, 1.4])
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

    dfx = df.copy()
    if escolha != "Todo o período":
        mes_sel = next(m for m, r in rotulos.items() if r == escolha)
        dfx = dfx[dfx["mes"] == mes_sel]
    if sel_tipos:
        dfx = dfx[dfx["tipo"].isin(sel_tipos)]

    if dfx.empty:
        st.warning("Sem dados para os filtros selecionados.")
        return

    # ============================================================
    # KPIs
    # ============================================================
    st.markdown('<div class="leves-section-label" style="margin-top:20px;">Resumo do período</div>', unsafe_allow_html=True)

    total_geral = int(dfx["total"].sum())
    por_tipo = dfx.groupby("tipo")["total"].sum().to_dict()

    kpis = [("Total de insumos", total_geral, "📦", "no período")]
    for t in tipos_disp:
        # Os cards individuais ficam sem emoji; apenas o total usa ícone.
        kpis.append((str(t).title(), por_tipo.get(t, 0), "", "enviados"))

    cols = st.columns(len(kpis))
    for col, (nome, valor, icone, subtitulo) in zip(cols, kpis):
        with col:
            st.markdown(
                f'<div class="leves-kpi">'
                f'<div class="leves-kpi-top">'
                f'<span class="leves-kpi-icon" style="display:{"inline-flex" if icone else "none"};">{icone}</span>'
                f'{html.escape(nome)}</div>'
                f'<div class="leves-kpi-value">{_fmt(valor)}</div>'
                f'<div class="leves-kpi-sub">{html.escape(subtitulo)}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ============================================================
    # Gráficos
    # ============================================================
    st.markdown('<div style="height:18px"></div>', unsafe_allow_html=True)
    g1, g2 = st.columns(2)

    tdf = (
        dfx.groupby("tipo", as_index=False)["total"]
        .sum()
        .sort_values("total", ascending=False)
    )

    fig_tipo = px.bar(
        tdf,
        x="tipo",
        y="total",
        color="tipo",
        color_discrete_map=dp.CORES_TIPO,
        labels={"tipo": "Tipo", "total": "Total"},
    )
    fig_tipo.update_layout(
        showlegend=False,
        height=285,
        font_family="Montserrat",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=15, b=10),
        xaxis=dict(showgrid=False, title=None),
        yaxis=dict(gridcolor="#edf0f4", title=None),
    )

    with g1:
        with st.container(border=True):
            st.markdown('<div class="leves-chart-title">Total por tipo de insumo</div>', unsafe_allow_html=True)
            st.plotly_chart(fig_tipo, width="stretch", config={"displayModeBar": False})

    ddf = dfx.groupby(["dia", "tipo"], as_index=False)["total"].sum()
    fig_dia = px.bar(
        ddf,
        x="dia",
        y="total",
        color="tipo",
        color_discrete_map=dp.CORES_TIPO,
        labels={"dia": "Data", "total": "Total", "tipo": "Tipo"},
    )
    fig_dia.update_layout(
        height=285,
        font_family="Montserrat",
        legend_title_text="Tipo",
        barmode="stack",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=15, b=10),
        xaxis=dict(showgrid=False, title=None),
        yaxis=dict(gridcolor="#edf0f4", title=None),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    with g2:
        with st.container(border=True):
            st.markdown('<div class="leves-chart-title">Envios por dia</div>', unsafe_allow_html=True)
            st.plotly_chart(fig_dia, width="stretch", config={"displayModeBar": False})

    # ============================================================
    # Admin — ranking
    # ============================================================
    if eh_admin:
        st.markdown('<div style="height:18px"></div>', unsafe_allow_html=True)
        st.markdown('<div class="leves-section-label">Destinos</div>', unsafe_allow_html=True)
        rank = (
            dfx.groupby("destino", as_index=False)["total"]
            .sum()
            .sort_values("total", ascending=True)
            .tail(15)
        )
        fig_dest = px.bar(
            rank,
            x="total",
            y="destino",
            orientation="h",
            labels={"total": "Total", "destino": "Destino"},
        )
        fig_dest.update_traces(marker_color=AZUL)
        fig_dest.update_layout(
            height=400,
            font_family="Montserrat",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=15, b=10),
            xaxis=dict(gridcolor="#edf0f4", title=None),
            yaxis=dict(title=None),
        )
        st.plotly_chart(fig_dest, width="stretch", config={"displayModeBar": False})

    # ============================================================
    # Tabela detalhada
    # ============================================================
    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
    with st.expander("Ver tabela detalhada"):
        cols_tab = ["dt", "tipo", "destino", "total"] if eh_admin else ["dt", "tipo", "total"]
        tab = dfx[cols_tab].sort_values("dt", ascending=False).copy()
        tab["dt"] = tab["dt"].dt.strftime("%d/%m/%Y")
        nomes = {
            "dt": "Data",
            "tipo": "Tipo de insumo",
            "destino": "Destino",
            "total": "Total",
        }
        tab = tab.rename(columns=nomes)
        st.dataframe(tab, width="stretch", hide_index=True)
        st.download_button(
            "Baixar CSV",
            tab.to_csv(index=False).encode("utf-8-sig"),
            file_name="ativos_leves.csv",
            mime="text/csv",
            key="dl_envios",
        )
