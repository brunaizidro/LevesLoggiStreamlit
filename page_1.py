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
   ENVIOS — MESMA IDENTIDADE VISUAL DO RECEBIMENTO
   ============================================================ */
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');

html, body, [data-testid="stApp"], [data-testid="stApp"] *,
[data-testid="stDataFrame"], [data-testid="stDataFrame"] * {
    font-family: 'Montserrat', sans-serif !important;
}
[data-testid="stHeader"], [data-testid="stToolbar"] {
    display: none !important;
}
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: #FFFFFF !important;
}
[data-testid="stAppViewBlockContainer"] {
    max-width: 100% !important;
    padding: 18px  clamp(22px, 3.2vw, 54px) 38px !important;
}

/* Cabeçalho no mesmo padrão simples do Recebimento */
.leves-breadcrumb {
    color: #7B8798 !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: .55px !important;
    margin: 0 0 7px !important;
}
.leves-page-title {
    color: #172B4D !important;
    font-size: clamp(28px, 2.3vw, 34px) !important;
    line-height: 1.18 !important;
    font-weight: 800 !important;
    letter-spacing: -.8px !important;
    margin: 0 !important;
}
.leves-page-title span { color: #0067FC !important; }
.leves-page-description {
    color: #7A8493 !important;
    font-size: 14px !important;
    line-height: 1.55 !important;
    margin: 6px 0 18px !important;
}

/* Remove o realce azul de seleção do texto */
::selection { background: transparent !important; color: #000000 !important; }

/* Títulos e textos */
.leves-filter-heading,
.leves-section-label,
.leves-chart-title,
.leves-table-heading {
    color: #172B4D !important;
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 800 !important;
}
.leves-filter-heading { font-size: 17px !important; margin: 0 0 10px !important; }
.leves-section-label { font-size: 16px !important; margin: 18px 0 10px !important; }
.leves-summary-heading { margin-top: 16px !important; }
.leves-filter-heading span,
.leves-summary-heading:first-letter { color: #0067FC !important; }
.leves-chart-title,
.leves-table-heading { font-size: 16px !important; margin: 0 0 8px !important; }

/* Filtros: campos suaves como os campos do Recebimento */
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label {
    color: #172B4D !important;
    font-size: 13px !important;
    font-weight: 700 !important;
}
[data-baseweb="select"] > div {
    background: #F0F2F6 !important;
    border: 1px solid #E7EAF0 !important;
    border-radius: 10px !important;
    min-height: 42px !important;
    box-shadow: none !important;
}
[data-baseweb="select"] > div:focus-within {
    border-color: #0067FC !important;
    box-shadow: 0 0 0 2px rgba(0,103,252,.10) !important;
}
[data-baseweb="tag"] {
    background: #0067FC !important;
    border-radius: 6px !important;
}
[data-baseweb="tag"] *,
[data-baseweb="tag"] span { color: #FFFFFF !important; }

/* Cartão de filtros branco, com borda azul discreta */
.st-key-filters_card {
    background: #FFFFFF !important;
    border: 1px solid #DCE7F6 !important;
    border-radius: 14px !important;
    padding: 14px 16px !important;
    box-shadow: 0 4px 14px rgba(16,43,80,.045) !important;
}
.st-key-filters_card [data-testid="stVerticalBlockBorderWrapper"],
.st-key-filters_card [data-testid="stVerticalBlock"],
.st-key-filters_card [data-testid="stHorizontalBlock"],
.st-key-filters_card [data-testid="stElementContainer"] {
    background: #FFFFFF !important;
}
.st-key-filters_card [data-testid="stVerticalBlockBorderWrapper"] {
    border: 0 !important;
    box-shadow: none !important;
}

/* Indicadores: azul Loggi no total e cartões brancos nos demais */
.leves-kpi {
    background: #FFFFFF !important;
    border: 1px solid #DCE7F6 !important;
    border-radius: 14px !important;
    padding: 16px 18px !important;
    min-height: 108px !important;
    box-shadow: 0 4px 14px rgba(16,43,80,.045) !important;
    box-sizing: border-box !important;
}
.leves-kpi-total {
    background: #0067FC !important;
    border-color: #0067FC !important;
    box-shadow: 0 6px 18px rgba(0,103,252,.16) !important;
}
.leves-kpi-top {
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    color: #526783 !important;
    font-size: 11px !important;
    font-weight: 800 !important;
    letter-spacing: .35px !important;
    text-transform: uppercase !important;
}
.leves-kpi-icon {
    width: 28px !important;
    height: 28px !important;
    border-radius: 50% !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: #EAF2FF !important;
    color: #0067FC !important;
}
.leves-kpi-value {
    color: #172B4D !important;
    font-size: 30px !important;
    line-height: 1.1 !important;
    font-weight: 800 !important;
    margin-top: 8px !important;
}
.leves-kpi-sub {
    color: #7B8798 !important;
    font-size: 11px !important;
    margin-top: 4px !important;
}
.leves-kpi-total .leves-kpi-top,
.leves-kpi-total .leves-kpi-value,
.leves-kpi-total .leves-kpi-sub { color: #FFFFFF !important; }
.leves-kpi-total .leves-kpi-icon {
    background: rgba(255,255,255,.18) !important;
    color: #FFFFFF !important;
}

/* Gráficos e tabelas em cartões brancos, sem moldura cinza pesada */
[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid #DCE7F6 !important;
    border-radius: 14px !important;
    background: #FFFFFF !important;
    box-shadow: 0 4px 14px rgba(16,43,80,.035) !important;
}
.leves-chart-card {
    background: #FFFFFF !important;
    border: 1px solid #DCE7F6 !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 14px rgba(16,43,80,.035) !important;
}
.js-plotly-plot,
.js-plotly-plot text,
.js-plotly-plot .legendtext,
.js-plotly-plot .gtitle,
.js-plotly-plot .xtick text,
.js-plotly-plot .ytick text,
.js-plotly-plot .annotation-text {
    font-family: 'Montserrat', sans-serif !important;
}
.leves-html-table-wrap {
    height: 335px;
    overflow: auto;
    border: 1px solid #DCE7F6;
    border-radius: 10px;
    background: #FFFFFF;
}
.leves-html-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-family: 'Montserrat', sans-serif !important;
    font-size: 13px;
    color: #172B4D;
}
.leves-html-table th {
    position: sticky;
    top: 0;
    z-index: 2;
    background: #0067FC !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    text-align: center;
    padding: 11px 12px;
    white-space: nowrap;
}
.leves-html-table td {
    background: #FFFFFF;
    color: #172B4D;
    font-weight: 500;
    text-align: center;
    padding: 10px 12px;
    border-bottom: 1px solid #E8EEF7;
    white-space: nowrap;
}
.leves-html-table tbody tr:nth-child(even) td { background: #F7FAFF; }
.leves-html-table tbody tr:hover td { background: #EEF5FF; }

/* Botões azuis no mesmo padrão dos botões de ação do Recebimento */
[data-testid="stAppViewContainer"] .stButton > button,
[data-testid="stAppViewContainer"] .stDownloadButton > button,
[data-testid="stFormSubmitButton"] button {
    min-height: 40px !important;
    border-radius: 9px !important;
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 700 !important;
}
[data-testid="stAppViewContainer"] .stButton > button,
[data-testid="stFormSubmitButton"] button {
    background: #0067FC !important;
    border: 1px solid #0067FC !important;
    color: #FFFFFF !important;
}
[data-testid="stAppViewContainer"] .stButton > button:hover,
[data-testid="stFormSubmitButton"] button:hover {
    background: #0058DC !important;
    border-color: #0058DC !important;
}
[data-testid="stDownloadButton"] button {
    background: #EEF5FF !important;
    border: 1px solid #D5E5FF !important;
    color: #075BEA !important;
}
[data-testid="stTextInput"] input {
    border-radius: 9px !important;
    border: 1px solid #DCE7F6 !important;
    background: #F0F2F6 !important;
}
[data-testid="stAlert"] { border-radius: 10px !important; }

/* Sidebar permanece exatamente a do menu padrão do Recebimento */
@media (max-width: 900px) {
    [data-testid="stAppViewBlockContainer"] { padding: 16px 14px 28px !important; }
    .leves-page-title { font-size: 27px !important; }
    .leves-kpi-value { font-size: 26px !important; }
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
                # Reserva a faixa direita para a legenda e fixa o centro do donut.
                fig_tipo.update_traces(domain=dict(x=[0.02, 0.78], y=[0.02, 0.98]))
                fig_tipo.update_layout(
                    height=285, showlegend=True, font=dict(family="Montserrat", color="#243B5B", size=11),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=8, r=8, t=8, b=8),
                    legend=dict(orientation="v", y=0.5, yanchor="middle", x=0.84, xanchor="left"),
                    annotations=[dict(
                        text=f"<b>{_fmt(total_geral)}</b><br><span style='font-size:11px'>insumos</span>",
                        x=0.40, y=0.50, xref="paper", yref="paper",
                        xanchor="center", yanchor="middle", align="center",
                        showarrow=False,
                        font=dict(family="Montserrat", size=20, color="#102B50"),
                    )],
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
                    mode="lines+markers+text",
                    texttemplate="%{y:,.0f}",
                    textposition="top center",
                    textfont=dict(family="Montserrat", size=10, color="#102B50"),
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

    # Ranking de bases por valor financeiro dos insumos
    st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
    if eh_admin:
        rank_col, table_col = st.columns([0.78, 1.22], gap="large")
    else:
        table_col = st.container()
        rank_col = None

    if eh_admin and rank_col is not None:
        with rank_col:
            with st.container(border=True):
                st.markdown('<div class="leves-chart-title" style="color:#000000 !important; background:transparent !important;">Top 10 bases por valor de insumos</div>', unsafe_allow_html=True)
                precos_unitarios = dp.precos()
                rank_base = dfx.copy()
                rank_base["valor_insumo"] = (
                    rank_base["total"] * rank_base["tipo"].map(precos_unitarios).fillna(0)
                )
                rank = (
                    rank_base.groupby("destino", as_index=False)["valor_insumo"]
                    .sum()
                    .nlargest(10, "valor_insumo")
                    .sort_values("valor_insumo", ascending=False, kind="stable")
                )
                if not rank.empty:
                    rank["valor_label"] = rank["valor_insumo"].map(dp.fmt_brl)
                    fig_dest = px.bar(
                        rank, x="valor_insumo", y="destino", orientation="h",
                        text="valor_label",
                        labels={"valor_insumo": "Valor dos insumos", "destino": "Base"},
                    )
                    fig_dest.update_traces(
                        marker=dict(color="#0067FC"),
                        textposition="outside",
                        textfont=dict(family="Montserrat", size=11, color="#243B5B"),
                        cliponaxis=False,
                        hovertemplate="<b>%{y}</b><br>Valor dos insumos: R$ %{x:,.2f}<extra></extra>",
                    )
                    maior_valor = float(rank["valor_insumo"].max() or 0)
                    fig_dest.update_layout(
                        height=335, font=dict(family="Montserrat", color="#536789", size=11),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=8, r=82, t=8, b=8),
                        xaxis=dict(
                            title=None, showgrid=False, zeroline=False, showticklabels=False,
                            range=[0, maior_valor * 1.28 if maior_valor > 0 else 1],
                        ),
                        yaxis=dict(
                            title=None, showgrid=False, zeroline=False,
                            categoryorder="array",
                            categoryarray=rank["destino"].astype(str).tolist(),
                            autorange="reversed",
                        ),
                    )
                    st.plotly_chart(fig_dest, width="stretch", config={"displayModeBar": False})
                    tipos_sem_preco = sorted(
                        tipo for tipo in dfx["tipo"].dropna().unique()
                        if precos_unitarios.get(tipo, 0) <= 0
                    )
                    if tipos_sem_preco:
                        st.caption(
                            "Atenção: tipos sem preço cadastrado não entram no valor do ranking: "
                            + ", ".join(tipos_sem_preco)
                            + "."
                        )
                else:
                    st.info("Não há bases para classificar.")
                
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
            config_tabela = {
                coluna: st.column_config.TextColumn(coluna, alignment="center")
                for coluna in tab.columns if coluna != "Quantidade"
            }
            config_tabela["Quantidade"] = st.column_config.NumberColumn(
                "Quantidade", alignment="center", format="%d"
            )
            tabela_html = tab.to_html(index=False, escape=True, border=0, classes="leves-html-table")
            st.markdown(
                f'<div class="leves-html-table-wrap">{tabela_html}</div>',
                unsafe_allow_html=True,
            )
            st.download_button("Baixar CSV", tab.to_csv(index=False).encode("utf-8-sig"),
                               file_name="ativos_leves.csv", mime="text/csv", key="dl_envios")

