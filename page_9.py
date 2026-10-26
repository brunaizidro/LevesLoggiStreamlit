"""Minhas cobranças: valores financeiros por operação e competência, sem quantidades."""
from __future__ import annotations

import pandas as pd
import streamlit as st
import data_extraction as dados
import data_processing as dp


def _valor_numero(valor):
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor or "").replace("R$", "").strip()
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except (TypeError, ValueError):
        return 0.0


def _moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def page_9():
    user = st.session_state.get("usuario") or {}
    destino = str(user.get("destino", "")).strip()

    st.subheader("Minhas cobranças")
    st.markdown(
        "<p class='custom-text'>Valores de cobrança registrados para a sua operação, "
        "organizados por mês de competência.</p>",
        unsafe_allow_html=True,
    )

    try:
        registros = dados._planilha().worksheet("Cobrancas").get_all_records()
    except Exception:
        st.info("A base de cobranças não está disponível. Confira a aba 'Cobrancas' na planilha do portal.")
        return

    if not registros:
        st.info("Ainda não há cobranças cadastradas.")
        return

    base = pd.DataFrame(registros)
    faltantes = [c for c in ["id", "competencia", "destino", "valor"] if c not in base.columns]
    if faltantes:
        st.error("A aba Cobrancas precisa conter as colunas: id, competencia, destino e valor.")
        return

    if not dp._normalizar(destino):
        st.warning("Seu usuário não possui uma operação vinculada. Solicite ao administrador a correção do cadastro.")
        return

    minhas = base[base["destino"].map(dp._normalizar) == dp._normalizar(destino)].copy()
    if minhas.empty:
        st.success("Nenhuma cobrança registrada para a sua operação. 🎉")
        return

    minhas["Valor"] = minhas["valor"].map(_valor_numero)
    minhas["Competência"] = minhas["competencia"].astype(str).map(
        lambda m: dp.rotulo_mes(m) if len(m) == 7 and m[4:5] == "-" else m
    )
    minhas["NC"] = minhas["id"].astype(str)
    if "data" not in minhas.columns:
        minhas["data"] = ""

    st.metric("Valor total fechado", _moeda(minhas["Valor"].sum()))

    st.markdown("#### Por competência")
    resumo = (
        minhas.groupby(["competencia", "Competência"], as_index=False)["Valor"]
        .sum()
        .sort_values("competencia", ascending=False)
    )
    resumo["Valor"] = resumo["Valor"].map(_moeda)
    st.dataframe(resumo[["Competência", "Valor"]], width="stretch", hide_index=True)

    st.markdown("#### Detalhamento")
    det = minhas.sort_values(["competencia", "NC"], ascending=[False, True]).copy()
    det["Valor"] = det["Valor"].map(_moeda)
    det_disp = det[["Competência", "NC", "Valor", "data"]].rename(
        columns={"data": "Data do lançamento"}
    )
    st.dataframe(det_disp, width="stretch", hide_index=True)
    st.download_button(
        "Baixar minhas cobranças (CSV)",
        det_disp.to_csv(index=False).encode("utf-8-sig"),
        file_name="minhas_cobrancas.csv",
        mime="text/csv",
        key="dl_minhas_cob",
    )
