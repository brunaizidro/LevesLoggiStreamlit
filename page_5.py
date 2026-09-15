"""
page_5.py — Relatórios de devoluções (admin).

Visão consolidada: status das devoluções, divergências (declarado × recebido),
percentual de devolução no período e histórico completo com exportação em CSV.
"""

from __future__ import annotations

import plotly.express as px
import streamlit as st

import data_processing as dp

CORES_STATUS = {
    dp.STATUS_TRANSITO: "#00baff",
    dp.STATUS_RECEBIDO: "#0067fc",
    dp.STATUS_CONFERIDO: "#90EE90",
    dp.STATUS_DIVERGENTE: "#F08080",
    dp.STATUS_CANCELADO: "#c9c9c9",
}


def _fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def _pct(recebido: int, enviado: int) -> float:
    """Percentual de devolução: recebido no período ÷ enviado no período."""
    if enviado <= 0:
        return 0.0
    return (recebido / enviado) * 100.0


def _meses_relatorio(envios, devs) -> list[str]:
    meses = set()

    if not envios.empty:
        meses.update(envios["mes"].dropna().astype(str).tolist())

    if not devs.empty and "data_recebimento" in devs.columns:
        dt = __import__("pandas").to_datetime(devs["data_recebimento"], errors="coerce")
        meses.update(dt.dropna().dt.to_period("M").astype(str).tolist())

    return sorted(meses, reverse=True)


def _recebidos_no_periodo(devs, its, mes: str) -> dict[str, int]:
    """Soma o recebido efetivo por tipo usando a data de recebimento."""
    if devs.empty or its.empty:
        return {}

    import pandas as pd

    d = devs[devs["status"].isin(dp.STATUS_RECEBIDOS)].copy()
    if d.empty or "data_recebimento" not in d.columns:
        return {}

    d["dt_receb"] = pd.to_datetime(d["data_recebimento"], errors="coerce")
    d = d[d["dt_receb"].notna() & (d["dt_receb"].dt.to_period("M").astype(str) == mes)]
    if d.empty:
        return {}

    ids = set(d["id"])
    it = its[its["id_devolucao"].isin(ids)].copy()
    if it.empty:
        return {}

    it["qtd_recebida"] = pd.to_numeric(it["qtd_recebida"], errors="coerce")
    it["qtd_declarada"] = pd.to_numeric(it["qtd_declarada"], errors="coerce").fillna(0)
    it["q"] = it["qtd_recebida"].fillna(it["qtd_declarada"]).fillna(0)
    it["tipo"] = it["tipo"].astype(str).str.upper().str.strip()

    return it.groupby("tipo")["q"].sum().astype(int).to_dict()


def page_5():
    st.subheader("Relatórios de devoluções")

    devs = dp.devolucoes_df()
    its = dp.itens_df()
    envios = dp.envios_df()

    # ============================================================
    # Percentual de devolução no período
    # ============================================================
    st.markdown("#### Percentual de devolução no período")
    st.caption("Percentual = total recebido no período ÷ total enviado no período.")

    meses = _meses_relatorio(envios, devs)
    periodo_opts = ["Todo o período"] + [dp.rotulo_mes(m) for m in meses]
    periodo_sel = st.selectbox("Período", periodo_opts, index=1 if meses else 0, key="rel_periodo")

    env_periodo = envios.copy()
    if periodo_sel != "Todo o período":
        mes_sel = next(m for m in meses if dp.rotulo_mes(m) == periodo_sel)
        env_periodo = env_periodo[env_periodo["mes"] == mes_sel]
    else:
        mes_sel = None

    enviados_tipo = {}
    if not env_periodo.empty:
        env_periodo["tipo"] = env_periodo["tipo"].astype(str).str.upper().str.strip()
        env_periodo["total"] = env_periodo["total"].fillna(0)
        enviados_tipo = env_periodo.groupby("tipo")["total"].sum().astype(int).to_dict()

    recebidos_tipo = {}
    if mes_sel:
        recebidos_tipo = _recebidos_no_periodo(devs, its, mes_sel)
    elif not devs.empty and not its.empty:
        import pandas as pd

        d = devs[devs["status"].isin(dp.STATUS_RECEBIDOS)].copy()
        if not d.empty and "data_recebimento" in d.columns:
            d["dt_receb"] = pd.to_datetime(d["data_recebimento"], errors="coerce")
            d = d[d["dt_receb"].notna()]
            mapa = d.set_index("id").index
            it = its[its["id_devolucao"].isin(set(mapa))].copy()
            if not it.empty:
                it["qtd_recebida"] = pd.to_numeric(it["qtd_recebida"], errors="coerce")
                it["qtd_declarada"] = pd.to_numeric(it["qtd_declarada"], errors="coerce").fillna(0)
                it["q"] = it["qtd_recebida"].fillna(it["qtd_declarada"]).fillna(0)
                it["tipo"] = it["tipo"].astype(str).str.upper().str.strip()
                recebidos_tipo = it.groupby("tipo")["q"].sum().astype(int).to_dict()

    sacas_env = int(enviados_tipo.get("SACA", 0))
    sacas_rec = int(recebidos_tipo.get("SACA", 0))
    gay_env = int(enviados_tipo.get("GAYLORD", 0))
    gay_rec = int(recebidos_tipo.get("GAYLORD", 0))

    total_env = sacas_env + gay_env
    total_rec = sacas_rec + gay_rec

    c1, c2, c3 = st.columns(3)
    c1.metric("Sacas", f"{_pct(sacas_rec, sacas_env):.1f}%", help=f"Recebidas: {_fmt(sacas_rec)} | Enviadas: {_fmt(sacas_env)}")
    c2.metric("Gaylords", f"{_pct(gay_rec, gay_env):.1f}%", help=f"Recebidos: {_fmt(gay_rec)} | Enviados: {_fmt(gay_env)}")
    c3.metric("Total", f"{_pct(total_rec, total_env):.1f}%", help=f"Recebidos: {_fmt(total_rec)} | Enviados: {_fmt(total_env)}")

    resumo_pct = __import__("pandas").DataFrame([
        {"Tipo": "SACA", "Enviado": sacas_env, "Recebido": sacas_rec, "% Devolução": _pct(sacas_rec, sacas_env)},
        {"Tipo": "GAYLORD", "Enviado": gay_env, "Recebido": gay_rec, "% Devolução": _pct(gay_rec, gay_env)},
        {"Tipo": "TOTAL", "Enviado": total_env, "Recebido": total_rec, "% Devolução": _pct(total_rec, total_env)},
    ])
    resumo_pct["Enviado"] = resumo_pct["Enviado"].map(_fmt)
    resumo_pct["Recebido"] = resumo_pct["Recebido"].map(_fmt)
    resumo_pct["% Devolução"] = resumo_pct["% Devolução"].map(lambda x: f"{x:.1f}%")
    st.dataframe(resumo_pct, width="stretch", hide_index=True)

    st.markdown("---")

    # ---- Cartões por status ----
    cont = devs["status"].value_counts().to_dict() if not devs.empty else {}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Em trânsito", cont.get(dp.STATUS_TRANSITO, 0))
    c2.metric(
        "Recebidas/Conferidas",
        cont.get(dp.STATUS_RECEBIDO, 0) + cont.get(dp.STATUS_CONFERIDO, 0),
    )
    c3.metric("Divergentes", cont.get(dp.STATUS_DIVERGENTE, 0))
    c4.metric("Canceladas", cont.get(dp.STATUS_CANCELADO, 0))

    st.markdown("---")

    # ---- Gráfico por status ----
    if not devs.empty:
        sdf = devs["status"].value_counts().reset_index()
        sdf.columns = ["status", "qtd"]
        sdf["rotulo"] = sdf["status"].map(lambda s: dp.STATUS_LABEL.get(s, s))
        fig = px.bar(
            sdf,
            x="rotulo",
            y="qtd",
            color="status",
            color_discrete_map=CORES_STATUS,
            title="Devoluções por status",
            labels={"rotulo": "Status", "qtd": "Quantidade"},
        )
        fig.update_layout(showlegend=False, height=330, font_family="Montserrat")
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Nenhuma devolução registrada ainda.")

    # ---- Divergências ----
    st.markdown("#### Divergências (declarado × recebido)")
    divs = devs[devs["status"] == dp.STATUS_DIVERGENTE] if not devs.empty else devs
    if divs.empty or its.empty:
        st.caption("Nenhuma divergência registrada.")
    else:
        it = its[its["id_devolucao"].isin(set(divs["id"]))].copy()
        it["qtd_recebida"] = it["qtd_recebida"].fillna(0)
        it["diferenca"] = it["qtd_recebida"].astype(int) - it["qtd_declarada"].astype(int)
        it = it[it["diferenca"] != 0]
        tab = it[["id_devolucao", "tipo", "qtd_declarada", "qtd_recebida", "diferenca"]].copy()
        tab.columns = ["Devolução", "Tipo", "Declarado", "Recebido", "Diferença"]
        st.dataframe(tab, width="stretch", hide_index=True)

    # ---- Histórico ----
    if not devs.empty:
        st.markdown("#### Histórico completo")
        hist = devs.copy()
        hist["status"] = hist["status"].map(lambda s: dp.STATUS_LABEL.get(s, s))
        cols = [
            "id",
            "data_criacao",
            "usuario",
            "destino",
            "status",
            "total_declarado",
            "total_recebido",
            "data_recebimento",
            "recebido_por",
        ]
        hist = hist[cols].sort_values("data_criacao", ascending=False)
        hist.columns = [
            "Devolução",
            "Emissão",
            "Operação",
            "Destino",
            "Status",
            "Declarado",
            "Recebido",
            "Data recebimento",
            "Recebido por",
        ]
        st.dataframe(hist, width="stretch", hide_index=True)
        st.download_button(
            "Baixar CSV",
            hist.to_csv(index=False).encode("utf-8-sig"),
            file_name="devolucoes.csv",
            mime="text/csv",
            key="dl_devs",
        )
