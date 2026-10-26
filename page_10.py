"""Módulo administrativo de cobranças financeiras por operação e competência."""
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


def page_10():
    st.subheader("Cobranças")
    st.markdown(
        "<p class='custom-text'>Consulta financeira das cobranças registradas, "
        "separada da conciliação de envios e devoluções.</p>",
        unsafe_allow_html=True,
    )

    try:
        registros = dados._planilha().worksheet("Cobrancas").get_all_records()
    except Exception:
        st.error("Não foi possível acessar a aba 'Cobrancas' da planilha configurada no portal.")
        return

    if not registros:
        st.info("A aba Cobrancas está vazia.")
        return

    base = pd.DataFrame(registros)
    obrigatorias = ["id", "competencia", "destino", "valor"]
    faltantes = [col for col in obrigatorias if col not in base.columns]
    if faltantes:
        st.error("A aba Cobrancas precisa conter as colunas: " + ", ".join(obrigatorias))
        return

    base["Valor"] = base["valor"].map(_valor_numero)
    base["NC"] = base["id"].astype(str)
    base["Sigla"] = base["destino"].astype(str)
    base["Competência"] = base["competencia"].astype(str).map(
        lambda m: dp.rotulo_mes(m) if len(m) == 7 and m[4:5] == "-" else m
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Valor total registrado", _moeda(base["Valor"].sum()))
    c2.metric("Notas de débito", str(len(base)))
    c3.metric("Operações", str(base["Sigla"].nunique()))

    st.markdown("#### Filtros")
    f1, f2 = st.columns(2)
    competencias = sorted(base["Competência"].dropna().astype(str).unique(), reverse=True)
    siglas = sorted(base["Sigla"].dropna().astype(str).unique())
    comp_sel = f1.selectbox("Competência", ["Todas"] + competencias)
    sigla_sel = f2.selectbox("Operação", ["Todas"] + siglas)

    filtrada = base.copy()
    if comp_sel != "Todas":
        filtrada = filtrada[filtrada["Competência"] == comp_sel]
    if sigla_sel != "Todas":
        filtrada = filtrada[filtrada["Sigla"] == sigla_sel]

    st.metric("Valor no filtro selecionado", _moeda(filtrada["Valor"].sum()))
    st.markdown("#### Detalhamento")
    colunas = ["Sigla", "NC", "Competência", "Valor"]
    if "data" in filtrada.columns:
        colunas.append("data")
    if "tipo" in filtrada.columns:
        colunas.append("tipo")
    if "gerado_por" in filtrada.columns:
        colunas.append("gerado_por")
    exibicao = filtrada[colunas].rename(columns={
        "data": "Data do lançamento",
        "tipo": "Tipo",
        "gerado_por": "Gerado por",
    }).copy()
    exibicao["Valor"] = filtrada["Valor"].map(_moeda).values
    st.dataframe(exibicao, width="stretch", hide_index=True)
    st.download_button(
        "Baixar cobranças (CSV)",
        exibicao.to_csv(index=False).encode("utf-8-sig"),
        file_name="cobrancas.csv",
        mime="text/csv",
        key="dl_cobrancas_admin",
    )
