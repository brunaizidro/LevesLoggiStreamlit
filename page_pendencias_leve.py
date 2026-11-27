"""
page_pendencias_leve.py — Pendências da própria operação (perfil Leve/operação).

Mostra, mês a mês, o que a operação ainda tem a devolver, o prazo e a
situação. Não mostra outras bases (o painel gerencial é o page_8, só admin/GDL).
"""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

import data_processing as dp
import tema

_SITUACAO = {
    "No prazo": ("lv-transito", "ti-clock-hour-4"),
    "Prazo encerrado": ("lv-div", "ti-alert-triangle"),
    "Cobrado": ("lv-cancel", "ti-receipt"),
    "Em dia": ("lv-ok", "ti-circle-check"),
}


def _fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def _selo(situacao: str) -> str:
    cls, ico = _SITUACAO.get(situacao, ("lv-transito", "ti-point"))
    return f"<span class='lv-selo {cls}'><i class='ti {ico}'></i>{html.escape(situacao)}</span>"


def page_pendencias_leve():
    user = st.session_state.get("usuario") or {}
    destino = str(user.get("destino", "")).strip()

    tema.aplicar_tema()
    tema.cabecalho(
        "PORTAL LEVES / PENDÊNCIAS", "Pendências",
        "O que a sua operação ainda precisa devolver, mês a mês, com o prazo de cada um.",
        atualizado_ate=dp.envios_atualizados_ate(),
    )

    pend = dp.pendencias_da_operacao(destino)
    if pend.empty:
        st.info("Nenhum envio encontrado para a sua operação.")
        return

    abertos = pend[pend["situacao"].isin(["No prazo", "Prazo encerrado"])]
    total_itens = int(abertos["saldo"].sum())
    total_valor = float(abertos["valor"].sum())
    vencidos = pend[pend["situacao"] == "Prazo encerrado"]

    c1, c2, c3 = st.columns(3)
    c1.markdown(
        f"<div class='lv-card'><div class='lv-lbl'>Itens a devolver</div>"
        f"<div class='lv-num'>{_fmt(total_itens)}</div></div>", unsafe_allow_html=True)
    c2.markdown(
        f"<div class='lv-card'><div class='lv-lbl'>Valor em aberto</div>"
        f"<div class='lv-num'>{dp.fmt_brl(total_valor)}</div></div>", unsafe_allow_html=True)
    c3.markdown(
        f"<div class='lv-card'><div class='lv-lbl'>Meses com prazo encerrado</div>"
        f"<div class='lv-num' style='color:{'#8a5a00' if len(vencidos) else 'inherit'}'>"
        f"{vencidos['mes'].nunique()}</div></div>", unsafe_allow_html=True)

    if not vencidos.empty:
        st.warning(
            "Há saldo com **prazo encerrado**. Esses itens não podem mais ser devolvidos "
            "e entram na cobrança quando a competência for fechada."
        )

    tema.titulo_secao("Mês a mês", "ti-calendar-month")
    for mes, g in pend.groupby("mes", sort=False):
        situacao = g["situacao"].iloc[0]
        prazo = g["prazo"].iloc[0]
        saldo = int(g["saldo"].sum())
        valor = float(g["valor"].sum())
        detalhe = " · ".join(
            f"{_fmt(r['saldo'])} {r['tipo'].lower()}{'s' if r['saldo'] != 1 else ''}"
            for _, r in g.iterrows() if r["saldo"] > 0
        ) or "Nada a devolver"
        prazo_txt = f"Prazo: {prazo.strftime('%d/%m/%Y')}"
        if situacao == "No prazo":
            dias = tema.dias_uteis_ate(prazo, dp.agora_sp())
            prazo_txt += f" · {'falta 1 dia útil' if dias == 1 else f'faltam {dias} dias úteis'}"
        st.markdown(
            f"<div class='lv-card' style='margin-bottom:10px;display:flex;align-items:center;gap:16px;flex-wrap:wrap'>"
            f"<div style='flex:1;min-width:200px' class='lv-reg'><b>{html.escape(g['rotulo'].iloc[0])}</b>"
            f"<span>{html.escape(detalhe)}</span><span>{html.escape(prazo_txt)}</span></div>"
            f"<div style='text-align:right;min-width:120px'><div class='lv-num' style='font-size:22px'>{_fmt(saldo)}</div>"
            f"<div class='lv-lbl'>{dp.fmt_brl(valor) if valor else 'itens em aberto'}</div></div>"
            f"<div style='min-width:150px;text-align:right'>{_selo(situacao)}</div></div>",
            unsafe_allow_html=True,
        )

    with st.expander("Ver detalhe por insumo"):
        det = pend.assign(Prazo=pend["prazo"].dt.strftime("%d/%m/%Y"))
        det = det.rename(columns={
            "rotulo": "Mês", "tipo": "Insumo", "enviado": "Enviado", "devolvido": "Devolvido",
            "cobrado": "Já cobrado", "saldo": "Saldo", "situacao": "Situação",
        })[["Mês", "Insumo", "Enviado", "Devolvido", "Já cobrado", "Saldo", "Prazo", "Situação"]]
        st.dataframe(det, hide_index=True, width="stretch")
        st.caption("Devolvido inclui devoluções em trânsito e já recebidas no CD. "
                   "Pallet: 1 para cada gaylord enviado.")

    if st.button("Registrar uma devolução", type="primary"):
        st.session_state["pagina_navegacao_leves"] = "Devoluções"
        st.rerun()
