"""
page_5.py — Relatório mensal de envios e valores por insumo.
Usa somente a base de Envios e os preços unitários já configurados no portal.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

import data_processing as dp


TIPOS = ["SACA", "GAYLORD", "PALLET"]
NOMES = {"SACA": "Sacas", "GAYLORD": "Gaylords", "PALLET": "Pallets"}
CORES = {"SACA": "#0866F5", "GAYLORD": "#00A9E8", "PALLET": "#B5651D"}


def _fmt_qtd(v) -> str:
    return f"{float(v):,.0f}".replace(",", ".")


def _fmt_brl(v) -> str:
    return "R$ " + f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _estilo():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
    [data-testid="stAppViewContainer"],[data-testid="stAppViewContainer"] * {font-family:'Montserrat',sans-serif}
    .rel-breadcrumb {color:#8290A5;font-size:11px;font-weight:700;letter-spacing:.6px;margin:0 0 7px}
    .rel-title {color:#172B4D;font-size:35px;line-height:1.2;font-weight:800;letter-spacing:-.6px;margin:0}
    .rel-subtitle {color:#627895;font-size:14px;font-weight:600;line-height:1.55;margin:5px 0 20px}
    .rel-section {color:#172B4D;font-size:18px;font-weight:800;margin:8px 0 4px}
    .rel-caption {color:#71829A;font-size:12px;margin:0 0 12px}
    [data-testid="stMetric"] {background:#F5F8FE;border:1px solid #E0EAF8;border-radius:12px;padding:13px 15px}
    [data-testid="stMetricLabel"] p {color:#60738E!important;font-size:12px!important;font-weight:700!important}
    [data-testid="stMetricValue"] {color:#17385F!important;font-size:24px!important;font-weight:800!important}
    [data-testid="stDataFrame"] {border:1px solid #DCE7F6;border-radius:10px}
    </style>
    <div>
      <div class="rel-breadcrumb">PORTAL LEVES &nbsp;/&nbsp; RELATÓRIOS</div>
      <div class="rel-title">Relatórios de devoluções</div>
      <p class="rel-subtitle">Visão mensal dos volumes enviados e dos valores movimentados por tipo de insumo: saca, gaylord e pallet.</p>
    </div>
    """, unsafe_allow_html=True)


def page_5():
    _estilo()
    env = dp.envios_df()
    if env.empty:
        st.info("Ainda não existem envios registrados para montar o relatório.")
        return

    env = env.copy()
    env["tipo"] = env["tipo"].astype(str).str.upper().str.strip()
    env["destino"] = env["destino"].astype(str).str.strip()
    env["total"] = pd.to_numeric(env["total"], errors="coerce").fillna(0)
    env = env[env["tipo"].isin(TIPOS)].copy()
    if env.empty:
        st.info("Não há envios de sacas, gaylords ou pallets no período.")
        return

    precos = dp.precos()
    env["preco_unitario"] = env["tipo"].map(precos).fillna(0).astype(float)
    env["valor_total"] = env["total"] * env["preco_unitario"]
    env["ano"] = env["dt"].dt.year.astype(str)

    meses_disponiveis = sorted(env["mes"].dropna().unique().tolist())
    anos = sorted(env["ano"].unique().tolist(), reverse=True)
    destinos = sorted([d for d in env["destino"].dropna().unique().tolist() if d.strip()])

    with st.container(border=True):
        st.markdown("**Filtros do relatório**")
        c1, c2, c3 = st.columns([1, 1.4, 1])
        with c1:
            ano_sel = st.selectbox("Ano", ["Todos"] + anos, index=0, key="rel5_ano")
        with c2:
            destino_sel = st.selectbox("Operação / destino", ["Todos"] + destinos, key="rel5_destino")
        with c3:
            tipo_sel = st.selectbox("Insumo", ["Todos", "Saca", "Gaylord", "Pallet"], key="rel5_tipo_mensal")

    dados = env.copy()
    if ano_sel != "Todos":
        dados = dados[dados["ano"] == ano_sel]
    if destino_sel != "Todos":
        dados = dados[dados["destino"].map(dp._normalizar) == dp._normalizar(destino_sel)]
    if tipo_sel != "Todos":
        dados = dados[dados["tipo"] == tipo_sel.upper()]

    if dados.empty:
        st.info("Nenhum envio encontrado para os filtros selecionados.")
        return

    total_qtd = dados["total"].sum()
    total_valor = dados["valor_total"].sum()
    meses_no_filtro = dados["mes"].nunique()
    preco_faltante = [t for t in dados["tipo"].unique() if precos.get(t, 0) <= 0]

    st.markdown('<div class="rel-section">Resumo do período</div>', unsafe_allow_html=True)
    st.markdown('<div class="rel-caption">Valores calculados pela quantidade enviada multiplicada pelo preço unitário cadastrado nas configurações do portal.</div>', unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)
    k1.metric("Quantidade enviada", _fmt_qtd(total_qtd))
    k2.metric("Valor total enviado", _fmt_brl(total_valor))
    k3.metric("Meses com movimentação", str(meses_no_filtro))

    if preco_faltante:
        nomes = ", ".join(NOMES.get(t, t) for t in preco_faltante)
        st.warning(f"Preço unitário não configurado para: {nomes}. O valor desses itens aparece como R$ 0,00 até o cadastro do preço.")

    st.markdown("---")
    st.markdown('<div class="rel-section">Detalhamento mensal por insumo</div>', unsafe_allow_html=True)
    st.markdown('<div class="rel-caption">Quantidade enviada e valor financeiro de cada mês, separado por saca, gaylord e pallet.</div>', unsafe_allow_html=True)

    ordem_meses = sorted(dados["mes"].unique().tolist())
    rotulos = {m: dp.rotulo_mes(m) for m in ordem_meses}
    resumo = (
        dados.groupby(["mes", "tipo"], as_index=False)
        .agg(quantidade=("total", "sum"), valor=("valor_total", "sum"))
    )
    tabela = []
    for mes in ordem_meses:
        linha = {"Mês": rotulos[mes]}
        total_mes_qtd = 0
        total_mes_valor = 0
        for tipo in TIPOS:
            parte = resumo[(resumo["mes"] == mes) & (resumo["tipo"] == tipo)]
            qtd = float(parte["quantidade"].sum()) if not parte.empty else 0
            valor = float(parte["valor"].sum()) if not parte.empty else 0
            linha[f"{NOMES[tipo]} (Qtd.)"] = _fmt_qtd(qtd)
            linha[f"{NOMES[tipo]} (Valor)"] = _fmt_brl(valor)
            total_mes_qtd += qtd
            total_mes_valor += valor
        linha["Total do mês (Qtd.)"] = _fmt_qtd(total_mes_qtd)
        linha["Total do mês (Valor)"] = _fmt_brl(total_mes_valor)
        tabela.append(linha)

    st.dataframe(pd.DataFrame(tabela), width="stretch", hide_index=True, height=min(560, 42 + 42 * len(tabela)))

    st.markdown("---")
    st.markdown('<div class="rel-section">Evolução mensal de quantidade</div>', unsafe_allow_html=True)
    graf_qtd = resumo.copy()
    graf_qtd["Mês"] = graf_qtd["mes"].map(rotulos)
    graf_qtd["Insumo"] = graf_qtd["tipo"].map(NOMES)
    fig_qtd = px.bar(
        graf_qtd, x="Mês", y="quantidade", color="Insumo", barmode="group",
        color_discrete_map={"Sacas": CORES["SACA"], "Gaylords": CORES["GAYLORD"], "Pallets": CORES["PALLET"]},
        category_orders={"Mês": [rotulos[m] for m in ordem_meses], "Insumo": ["Sacas", "Gaylords", "Pallets"]},
    )
    fig_qtd.update_layout(height=330, margin=dict(l=10,r=10,t=15,b=10), font_family="Montserrat",
                         paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         legend_title_text="", xaxis_title="", yaxis_title="Quantidade")
    st.plotly_chart(fig_qtd, width="stretch", config={"displayModeBar": False})

    st.markdown('<div class="rel-section">Evolução mensal de valores</div>', unsafe_allow_html=True)
    fig_valor = px.line(
        graf_qtd, x="Mês", y="valor", color="Insumo", markers=True,
        color_discrete_map={"Sacas": CORES["SACA"], "Gaylords": CORES["GAYLORD"], "Pallets": CORES["PALLET"]},
        category_orders={"Mês": [rotulos[m] for m in ordem_meses], "Insumo": ["Sacas", "Gaylords", "Pallets"]},
    )
    fig_valor.update_layout(height=330, margin=dict(l=10,r=10,t=15,b=10), font_family="Montserrat",
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            legend_title_text="", xaxis_title="", yaxis_title="Valor (R$)")
    fig_valor.update_traces(hovertemplate="%{x}<br>%{fullData.name}: R$ %{y:,.2f}<extra></extra>")
    st.plotly_chart(fig_valor, width="stretch", config={"displayModeBar": False})

    st.markdown("---")
    st.markdown('<div class="rel-section">Consolidado por insumo</div>', unsafe_allow_html=True)
    consolidado = (
        dados.groupby("tipo", as_index=False)
        .agg(quantidade=("total", "sum"), valor=("valor_total", "sum"), preco=("preco_unitario", "first"))
    )
    linhas = []
    for tipo in TIPOS:
        parte = consolidado[consolidado["tipo"] == tipo]
        qtd = float(parte["quantidade"].sum()) if not parte.empty else 0
        valor = float(parte["valor"].sum()) if not parte.empty else 0
        preco = float(precos.get(tipo, 0))
        linhas.append({"Insumo": NOMES[tipo], "Preço unitário": _fmt_brl(preco), "Quantidade enviada": _fmt_qtd(qtd), "Valor total": _fmt_brl(valor)})
    st.dataframe(pd.DataFrame(linhas), width="stretch", hide_index=True, height=165)

    csv = dados.assign(
        mes_label=dados["mes"].map(dp.rotulo_mes),
        tipo_label=dados["tipo"].map(NOMES),
    )[["mes_label", "dt", "destino", "tipo_label", "total", "preco_unitario", "valor_total"]].copy()
    csv.columns = ["Mês", "Data do envio", "Operação / destino", "Insumo", "Quantidade enviada", "Preço unitário (R$)", "Valor total (R$)"]
    st.download_button(
        "Baixar relatório mensal (CSV)",
        csv.to_csv(index=False).encode("utf-8-sig"),
        file_name="relatorio_mensal_envios_valores.csv",
        mime="text/csv",
        key="rel5_csv_mensal",
    )
