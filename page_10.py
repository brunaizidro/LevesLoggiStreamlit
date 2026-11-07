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
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
        .cob-page, .cob-page * {font-family:'Montserrat',sans-serif!important;}
        .cob-breadcrumb{color:#7B8798;font-size:11px;font-weight:600;letter-spacing:.65px;margin:0 0 7px;}
        .cob-title{color:#172B4D;font-size:clamp(30px,2.4vw,36px);line-height:1.18;font-weight:800;letter-spacing:-.8px;margin:0 0 4px;}
        .cob-description{color:#718096;font-size:16px;font-weight:600;line-height:1.35;margin:0 0 22px;}
        .cob-card{background:#EAF3FF;border:1px solid #D6E6FF;border-radius:16px;padding:17px 20px;min-height:104px;display:flex;align-items:center;gap:15px;}
        .cob-icon{width:42px;height:42px;display:flex;align-items:center;justify-content:center;color:#0067FC;flex:0 0 42px;}
        .cob-icon svg{width:34px;height:34px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;}
        .cob-label{color:#49698F;font-size:13px;font-weight:650;margin-bottom:5px;}
        .cob-value{color:#102B50;font-size:clamp(21px,2vw,29px);font-weight:800;letter-spacing:-.5px;white-space:nowrap;}
        .cob-filter-title{background:#EAF3FF;border:1px solid #D6E6FF;border-radius:12px 12px 0 0;color:#102B50;font-size:17px;font-weight:750;padding:11px 16px;margin:22px 0 0;}
        .cob-filter-body{background:#F7FAFF;border:1px solid #D6E6FF;border-top:0;border-radius:0 0 12px 12px;padding:12px 16px 4px;margin-bottom:16px;}
        .cob-summary{display:flex;align-items:center;gap:14px;background:#EAF3FF;border:1px solid #D6E6FF;border-radius:12px;padding:12px 18px;margin:12px 0 8px;}
        .cob-summary-label{color:#49698F;font-size:14px;font-weight:700;}
        .cob-summary-value{color:#102B50;font-size:25px;font-weight:800;margin-left:auto;}
        .cob-table-wrap{height:335px;overflow:auto;border:1px solid #DCE7F6;border-radius:10px;background:#FFFFFF;margin-bottom:8px;}
        .cob-html-table{width:100%;border-collapse:separate;border-spacing:0;font-family:'Montserrat',sans-serif!important;font-size:13px;color:#172B4D;}
        .cob-html-table th{position:sticky;top:0;z-index:2;background:#0067FC!important;color:#FFFFFF!important;font-weight:700!important;text-align:center;padding:11px 12px;white-space:nowrap;}
        .cob-html-table td{background:#FFFFFF;color:#172B4D;font-weight:500;text-align:center;padding:10px 12px;border-bottom:1px solid #E8EEF7;white-space:nowrap;}
        .cob-html-table tbody tr:nth-child(even) td{background:#F7FAFF;}
        .cob-html-table tbody tr:hover td{background:#EEF5FF;}
        div[data-testid="stDownloadButton"] button{background:#EAF3FF!important;color:#0067FC!important;border:1px solid #D6E6FF!important;border-radius:10px!important;font-weight:700!important;padding:9px 16px!important;}
        div[data-testid="stDownloadButton"] button:hover{background:#DCEBFF!important;border-color:#B8D5FF!important;}
        </style>
        <div class="cob-page">
          <div class="cob-breadcrumb">PORTAL LEVES &nbsp;/&nbsp; COBRANÇAS</div>
          <div class="cob-title">Cobranças</div>
          <div class="cob-description">Consulta financeira das cobranças registradas, separada da conciliação de envios e devoluções.</div>
        </div>
        """,
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
    cards = [
        ("Valor total registrado", _moeda(base["Valor"].sum()), '<svg viewBox="0 0 24 24"><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v5c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 10v5c0 1.7 3.6 3 8 3s8-1.3 8-3v-5"/><path d="M4 15v4c0 1.7 3.6 3 8 3s8-1.3 8-3v-4"/></svg>'),
        ("Notas de débito", str(len(base)), '<svg viewBox="0 0 24 24"><path d="M6 2h9l5 5v15H6z"/><path d="M14 2v6h6M9 13h8M9 17h8M9 9h2"/></svg>'),
        ("Operações", str(base["Sigla"].nunique()), '<svg viewBox="0 0 24 24"><path d="m3 8 9-5 9 5v9l-9 5-9-5z"/><path d="m3 8 9 5 9-5M12 13v9M7.5 5.5l9 5"/></svg>'),
    ]
    for col, (label, value, icon) in zip((c1, c2, c3), cards):
        col.markdown(
            f'<div class="cob-card"><div class="cob-icon">{icon}</div>'
            f'<div><div class="cob-label">{label}</div><div class="cob-value">{value}</div></div></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="cob-filter-title">⌕ &nbsp; Filtros</div>', unsafe_allow_html=True)
    with st.container(border=True):
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

    st.markdown(
        f'<div class="cob-summary"><span style="color:#0067FC;font-size:22px;">◆</span>'
        f'<span class="cob-summary-label">Valor no filtro selecionado</span>'
        f'<span class="cob-summary-value">{_moeda(filtrada["Valor"].sum())}</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="cob-filter-title" style="border-radius:12px;margin:0 0 6px;">▤ &nbsp; Detalhamento</div>', unsafe_allow_html=True)
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
    tabela_html = exibicao.to_html(
        index=False, escape=True, border=0, classes="cob-html-table"
    )
    st.markdown(
        f'<div class="cob-table-wrap">{tabela_html}</div>',
        unsafe_allow_html=True,
    )
    st.download_button(
        "Baixar cobranças (CSV)",
        exibicao.to_csv(index=False).encode("utf-8-sig"),
        file_name="cobrancas.csv",
        mime="text/csv",
        key="dl_cobrancas_admin",
    )
