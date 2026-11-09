"""
page_5.py — Relatórios detalhados de devoluções.
Acompanha o ciclo de SACA, GAYLORD e PALLET usando Envios,
Devolucoes e Devolucoes_Itens já existentes na planilha.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

import data_processing as dp


CORES_TIPO = {"SACA": "#0067FC", "GAYLORD": "#00BAFF", "PALLET": "#B5651D"}
CORES_STATUS = {
    dp.STATUS_TRANSITO: "#00BAFF",
    dp.STATUS_RECEBIDO: "#3987F5",
    dp.STATUS_CONFERIDO: "#22A06B",
    dp.STATUS_DIVERGENTE: "#E5A000",
    dp.STATUS_CANCELADO: "#9AA7B8",
}
TIPOS = ["SACA", "GAYLORD", "PALLET"]


def _fmt(n) -> str:
    try:
        return f"{int(round(float(n))):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "0"


def _competencia_dev(devs: pd.DataFrame) -> pd.Series:
    """Competência da devolução; usa a data de criação nos registros antigos."""
    if "competencia" in devs.columns:
        comp = devs["competencia"].fillna("").astype(str).str.strip()
    else:
        comp = pd.Series("", index=devs.index, dtype="object")
    datas = pd.to_datetime(devs.get("data_criacao", pd.Series(index=devs.index)), errors="coerce", dayfirst=True)
    fallback = datas.dt.strftime("%Y-%m").fillna("")
    valid = comp.str.match(r"^\d{4}-\d{2}$", na=False)
    return comp.where(valid, fallback)


def _rotulo_mes(mes: str) -> str:
    try:
        return dp.rotulo_mes(mes)
    except Exception:
        return mes


def _estilo():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
    .modulo-header,.modulo-header * {font-family:'Montserrat',sans-serif!important}
    .modulo-breadcrumb {color:#7B8798!important;font-size:11px!important;font-weight:700!important;letter-spacing:.6px!important;margin:0 0 7px!important}
    .modulo-title {color:#172B4D!important;font-size:36px!important;line-height:1.2!important;font-weight:800!important;letter-spacing:-.7px!important;margin:0!important}
    .modulo-subtitle {color:#627895!important;font-size:14px!important;font-weight:600!important;line-height:1.55!important;margin:5px 0 18px!important}
    [data-testid="stAppViewContainer"],[data-testid="stAppViewContainer"] * {font-family:'Montserrat',sans-serif}
    [data-testid="stMetric"] {background:#F5F8FE;border:1px solid #E0EAF8;border-radius:12px;padding:13px 15px}
    [data-testid="stMetricLabel"] p {color:#60738E!important;font-size:12px!important;font-weight:700!important}
    [data-testid="stMetricValue"] {color:#17385F!important;font-size:25px!important;font-weight:800!important}
    [data-testid="stDataFrame"] {border:1px solid #DCE7F6;border-radius:10px}
    [data-baseweb="select"] > div {border-radius:9px!important;border-color:#D5E1F0!important}
    .rel-section {color:#172B4D;font-size:18px;font-weight:800;margin:8px 0 4px}
    .rel-caption {color:#71829A;font-size:12px;font-weight:500;margin:0 0 12px}
    .rel-chip {display:inline-flex;align-items:center;gap:7px;background:#EFF5FF;border:1px solid #DCEAFF;border-radius:20px;padding:6px 11px;color:#23456F;font-size:11px;font-weight:700;margin:0 5px 7px 0}
    .rel-dot {width:8px;height:8px;border-radius:50%;display:inline-block}
    [data-testid="stDownloadButton"] button,[data-testid="stButton"] button {border-radius:9px!important;font-weight:700!important}
    </style>
    <div class="modulo-header">
      <div class="modulo-breadcrumb">PORTAL LEVES &nbsp;/&nbsp; RELATÓRIOS</div>
      <div class="modulo-title">Relatórios de devoluções</div>
      <p class="modulo-subtitle">Acompanhe o caminho de cada insumo: enviado, declarado para devolução, recebido, divergente ou cancelado.</p>
    </div>
    """, unsafe_allow_html=True)


def page_5():
    _estilo()
    envios = dp.envios_df()
    devs = dp.devolucoes_df()
    itens = dp.itens_df()

    if not envios.empty:
        envios = envios.copy()
        envios["tipo"] = envios["tipo"].astype(str).str.upper().str.strip()
        envios["destino"] = envios["destino"].astype(str).str.strip()
    if not devs.empty:
        devs = devs.copy()
        devs["status"] = devs["status"].astype(str).str.upper().str.strip()
        devs["competencia_relatorio"] = _competencia_dev(devs)
        devs["destino"] = devs["destino"].astype(str).str.strip()
        devs["dt_criacao"] = pd.to_datetime(devs["data_criacao"], errors="coerce", dayfirst=True)
    if not itens.empty:
        itens = itens.copy()
        itens["tipo"] = itens["tipo"].astype(str).str.upper().str.strip()
        itens["qtd_declarada"] = pd.to_numeric(itens["qtd_declarada"], errors="coerce").fillna(0)
        itens["qtd_recebida"] = pd.to_numeric(itens["qtd_recebida"], errors="coerce")

    # Filtros globais
    meses = set()
    if not envios.empty:
        meses.update(envios["mes"].dropna().astype(str))
    if not devs.empty:
        meses.update(devs["competencia_relatorio"].loc[devs["competencia_relatorio"].astype(str).str.match(r"^\d{4}-\d{2}$", na=False)])
    meses = sorted(meses, reverse=True)
    destinos = set()
    if not envios.empty:
        destinos.update(envios["destino"].dropna().astype(str))
    if not devs.empty:
        destinos.update(devs["destino"].dropna().astype(str))
    destinos = sorted(d for d in destinos if d.strip())

    with st.container(border=True):
        st.markdown("**Filtros do relatório**")
        f1, f2, f3 = st.columns([1.1, 1.5, 1])
        with f1:
            periodo_opts = ["Todo o período"] + [_rotulo_mes(m) for m in meses]
            periodo = st.selectbox("Competência", periodo_opts, key="rel5_periodo")
        with f2:
            operacao = st.selectbox("Operação / destino", ["Todas"] + destinos, key="rel5_operacao")
        with f3:
            tipo_filtro = st.selectbox("Insumo", ["Todos"] + TIPOS, key="rel5_tipo")

    mes_sel = None
    if periodo != "Todo o período":
        mes_sel = next((m for m in meses if _rotulo_mes(m) == periodo), None)

    env_f = envios.copy()
    dev_f = devs.copy()
    if mes_sel:
        if not env_f.empty:
            env_f = env_f[env_f["mes"] == mes_sel]
        if not dev_f.empty:
            dev_f = dev_f[dev_f["competencia_relatorio"] == mes_sel]
    if operacao != "Todas":
        if not env_f.empty:
            env_f = env_f[env_f["destino"].map(dp._normalizar) == dp._normalizar(operacao)]
        if not dev_f.empty:
            dev_f = dev_f[dev_f["destino"].map(dp._normalizar) == dp._normalizar(operacao)]
    if tipo_filtro != "Todos":
        if not env_f.empty:
            env_f = env_f[env_f["tipo"] == tipo_filtro]

    ids_visiveis = set(dev_f["id"].astype(str)) if not dev_f.empty else set()
    it_f = itens[itens["id_devolucao"].astype(str).isin(ids_visiveis)].copy() if not itens.empty else pd.DataFrame()
    if tipo_filtro != "Todos" and not it_f.empty:
        it_f = it_f[it_f["tipo"] == tipo_filtro]

    # Resumo quantitativo do ciclo
    enviados = env_f.groupby("tipo")["total"].sum().to_dict() if not env_f.empty else {}
    dev_map = dev_f.set_index("id")["status"].to_dict() if not dev_f.empty else {}
    if not it_f.empty:
        it_f["status"] = it_f["id_devolucao"].astype(str).map({str(k): v for k, v in dev_map.items()})
        em_transito = it_f[it_f["status"] == dp.STATUS_TRANSITO].groupby("tipo")["qtd_declarada"].sum().to_dict()
        recebidos = it_f[it_f["status"].isin(dp.STATUS_RECEBIDOS)].copy()
        recebidos["qtd_efetiva"] = recebidos["qtd_recebida"].fillna(recebidos["qtd_declarada"])
        recebidos_tipo = recebidos.groupby("tipo")["qtd_efetiva"].sum().to_dict()
        divergentes = it_f[it_f["status"] == dp.STATUS_DIVERGENTE].copy()
        divergentes["diferenca_abs"] = (divergentes["qtd_recebida"].fillna(0) - divergentes["qtd_declarada"]).abs()
        divergencia_tipo = divergentes.groupby("tipo")["diferenca_abs"].sum().to_dict()
        cancelados = it_f[it_f["status"] == dp.STATUS_CANCELADO].groupby("tipo")["qtd_declarada"].sum().to_dict()
        declarados_comprometidos = it_f[it_f["status"].isin(dp.STATUS_COMPROMETIDOS)].groupby("tipo")["qtd_declarada"].sum().to_dict()
    else:
        em_transito, recebidos_tipo, divergencia_tipo, cancelados, declarados_comprometidos = {}, {}, {}, {}, {}

    qtd_enviada = sum(enviados.values())
    qtd_transito = sum(em_transito.values())
    qtd_recebida = sum(recebidos_tipo.values())
    qtd_divergente = sum(divergencia_tipo.values())

    st.markdown('<div class="rel-section">Visão geral do período</div>', unsafe_allow_html=True)
    st.markdown('<div class="rel-caption">As quantidades são calculadas a partir dos registros de envios e das conferências de devolução existentes.</div>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total enviado", _fmt(qtd_enviada))
    k2.metric("Em trânsito para devolução", _fmt(qtd_transito))
    k3.metric("Recebido na conferência", _fmt(qtd_recebida))
    k4.metric("Diferença em divergências", _fmt(qtd_divergente))

    st.markdown("---")
    st.markdown('<div class="rel-section">Detalhamento por insumo</div>', unsafe_allow_html=True)
    st.markdown('<div class="rel-caption">Compare o volume enviado com o que está em trânsito, foi recebido ou apresentou divergência. Pallet segue a regra de derivação já aplicada na base de envios quando não existe lançamento próprio.</div>', unsafe_allow_html=True)

    tipos_visiveis = [tipo_filtro] if tipo_filtro != "Todos" else TIPOS
    linhas_tipo = []
    for tipo in tipos_visiveis:
        enviado = float(enviados.get(tipo, 0))
        transito = float(em_transito.get(tipo, 0))
        recebido = float(recebidos_tipo.get(tipo, 0))
        divergencia = float(divergencia_tipo.get(tipo, 0))
        cancelado = float(cancelados.get(tipo, 0))
        declarado = float(declarados_comprometidos.get(tipo, 0))
        linhas_tipo.append({
            "Insumo": tipo.title(),
            "Enviado": _fmt(enviado),
            "Declarado em devolução": _fmt(declarado),
            "Em trânsito": _fmt(transito),
            "Recebido": _fmt(recebido),
            "Diferença": _fmt(divergencia),
            "Cancelado": _fmt(cancelado),
            "Envios sem devolução registrada": _fmt(max(enviado - declarado, 0)),
        })
    st.dataframe(pd.DataFrame(linhas_tipo), width="stretch", hide_index=True, height=190)

    # Comparativo visual
    comparativo = []
    for tipo in tipos_visiveis:
        comparativo.extend([
            {"Insumo": tipo.title(), "Etapa": "Enviado", "Quantidade": float(enviados.get(tipo, 0))},
            {"Insumo": tipo.title(), "Etapa": "Em trânsito", "Quantidade": float(em_transito.get(tipo, 0))},
            {"Insumo": tipo.title(), "Etapa": "Recebido", "Quantidade": float(recebidos_tipo.get(tipo, 0))},
        ])
    if comparativo and any(x["Quantidade"] for x in comparativo):
        fig = px.bar(
            pd.DataFrame(comparativo), x="Insumo", y="Quantidade", color="Etapa",
            barmode="group", color_discrete_map={"Enviado": "#B9D4FF", "Em trânsito": "#00BAFF", "Recebido": "#0067FC"},
        )
        fig.update_layout(
            height=330, margin=dict(l=12, r=12, t=18, b=12),
            font_family="Montserrat", paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", legend_title_text="",
            xaxis_title="", yaxis_title="Quantidade",
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    else:
        st.info("Ainda não há movimentações para os filtros selecionados.")

    st.markdown("---")
    st.markdown('<div class="rel-section">Histórico detalhado por devolução</div>', unsafe_allow_html=True)
    st.markdown('<div class="rel-caption">Cada linha mostra um insumo dentro de uma devolução, permitindo rastrear o que foi declarado e o resultado da conferência.</div>', unsafe_allow_html=True)

    if dev_f.empty or it_f.empty:
        st.info("Não há itens de devolução registrados para os filtros selecionados.")
    else:
        meta = dev_f[["id", "data_criacao", "usuario", "destino", "status", "data_recebimento", "recebido_por", "placa", "local_devolucao", "obs"]].copy()
        detalhe = it_f.merge(meta, left_on="id_devolucao", right_on="id", how="left")
        detalhe["qtd_recebida_exibida"] = detalhe["qtd_recebida"].fillna(detalhe["qtd_declarada"])
        detalhe["diferenca"] = detalhe["qtd_recebida_exibida"] - detalhe["qtd_declarada"]
        detalhe["status_label"] = detalhe["status"].map(dp.STATUS_LABEL).fillna(detalhe["status"])
        detalhe["data_criacao"] = pd.to_datetime(detalhe["data_criacao"], errors="coerce", dayfirst=True).dt.strftime("%d/%m/%Y %H:%M")
        colunas = detalhe[[
            "id_devolucao", "data_criacao", "destino", "tipo", "qtd_declarada",
            "qtd_recebida_exibida", "diferenca", "status_label", "placa",
        ]].copy()
        colunas.columns = ["Devolução", "Data", "Operação", "Insumo", "Declarado", "Recebido", "Diferença", "Status", "Placa"]
        st.dataframe(colunas, width="stretch", hide_index=True, height=360)
        st.download_button(
            "Baixar relatório detalhado (CSV)",
            colunas.to_csv(index=False).encode("utf-8-sig"),
            file_name="relatorio_detalhado_devolucoes.csv",
            mime="text/csv",
            key="rel5_csv",
        )

        st.markdown("**Consultar uma devolução específica**")
        opcoes_dev = sorted(detalhe["id_devolucao"].dropna().astype(str).unique(), reverse=True)
        id_escolhido = st.selectbox("Registro de devolução", opcoes_dev, key="rel5_dev_escolhida")
        registro = dev_f[dev_f["id"].astype(str) == str(id_escolhido)].iloc[0]
        itens_registro = detalhe[detalhe["id_devolucao"].astype(str) == str(id_escolhido)].copy()
        status_label = dp.STATUS_LABEL.get(registro["status"], registro["status"])
        st.markdown(
            f"**{id_escolhido}**  ·  {status_label}  ·  **Operação:** {registro['destino']}  ·  **Placa:** {registro.get('placa') or '—'}"
        )
        a, b, c = st.columns(3)
        a.metric("Declarado", _fmt(itens_registro["qtd_declarada"].sum()))
        b.metric("Recebido", _fmt(itens_registro["qtd_recebida_exibida"].sum()))
        c.metric("Diferença", _fmt(itens_registro["diferenca"].sum()))
        tab_itens = itens_registro[["tipo", "qtd_declarada", "qtd_recebida_exibida", "diferenca"]].copy()
        tab_itens.columns = ["Insumo", "Declarado", "Recebido", "Diferença"]
        st.dataframe(tab_itens, width="stretch", hide_index=True)
        if str(registro.get("obs") or "").strip():
            st.caption(f"Observação: {registro['obs']}")
