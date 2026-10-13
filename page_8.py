"""
page_8.py — Pendências de devolução por competência (admin).

Exibe e envia lembretes somente para a competência selecionada, sem misturar
os saldos de meses diferentes.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

import data_processing as dp
import emailer


def _fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def _grupos(pend, competencia_label):
    grupos = []
    for destino, g in pend.groupby("destino"):
        itens = [{"tipo": r["tipo"], "pendente": int(r["cobravel"])} for _, r in g.iterrows()]
        grupos.append({
            "destino": destino,
            "itens": itens,
            "total": int(g["cobravel"].sum()),
            "emails": dp.emails_por_destino(destino),
            "competencia_label": competencia_label,
        })
    return grupos


def page_8():
    st.subheader("Pendências de devolução")
    st.markdown(
        "<p class='custom-text'>Consulte as pendências por mês e envie lembretes "
        "de cobrança somente da competência selecionada.</p>",
        unsafe_allow_html=True,
    )

    envios = dp.envios_df()
    if envios.empty or "mes" not in envios.columns:
        st.info("Ainda não há envios registrados para consultar.")
        return

    meses = sorted(envios["mes"].dropna().astype(str).unique().tolist(), reverse=True)
    if not meses:
        st.info("Não foram encontradas competências nos envios.")
        return

    mes = st.selectbox(
        "Mês de competência",
        options=meses,
        index=0,
        format_func=dp.rotulo_mes,
        key="pendencias_competencia",
    )
    competencia_label = dp.rotulo_mes(mes)

    # A conciliação limita enviados, devolvidos e cobranças à competência selecionada.
    pend = dp.conciliacao(mes)
    if pend.empty:
        st.info(f"Não há envios registrados para {competencia_label}.")
        return
    pend = pend[pd.to_numeric(pend["cobravel"], errors="coerce").fillna(0) > 0].copy()

    if pend.empty:
        st.success(f"Nenhuma pendência em aberto para {competencia_label}. 🎉")
        return

    grupos = _grupos(pend, competencia_label)
    total_geral = sum(x["total"] for x in grupos)
    pr = dp.precos()
    usa_valor = dp.tem_precos()
    for x in grupos:
        x["valor"] = sum(it["pendente"] * pr.get(it["tipo"], 0) for it in x["itens"])
    valor_geral = sum(x["valor"] for x in grupos)

    st.caption(f"Os totais e os e-mails abaixo consideram somente a competência {competencia_label}.")
    cols = st.columns(3 if usa_valor else 2)
    cols[0].metric("Operações com pendência", len(grupos))
    cols[1].metric("Total de ativos pendentes", _fmt(total_geral))
    if usa_valor:
        cols[2].metric("Valor total pendente", dp.fmt_brl(valor_geral))

    tdf = pend.groupby("tipo", as_index=False)["cobravel"].sum().rename(columns={"cobravel": "pendente"})
    fig = px.bar(
        tdf, x="tipo", y="pendente", color="tipo",
        color_discrete_map=dp.CORES_TIPO, title=f"Pendente por tipo — {competencia_label}",
        labels={"tipo": "Tipo", "pendente": "Pendente"},
    )
    fig.update_layout(showlegend=False, height=300, font_family="Montserrat")
    st.plotly_chart(fig, width="stretch")

    resumo = []
    for x in grupos:
        linha = {"Operação": x["destino"], "Total pendente": x["total"]}
        if usa_valor:
            linha["Valor"] = dp.fmt_brl(x["valor"])
        linha["E-mail(s)"] = ", ".join(x["emails"]) or "— sem e-mail —"
        resumo.append(linha)
    st.dataframe(resumo, width="stretch", hide_index=True)

    sem_email = [x["destino"] for x in grupos if not x["emails"]]
    if sem_email:
        st.caption("Sem e-mail cadastrado (não serão notificadas): " + ", ".join(sem_email))

    st.markdown("---")
    if not emailer.smtp_configurado():
        st.warning("Configure o servidor de e-mail (SMTP) em **Configurações** para enviar cobranças.")
        return

    st.markdown(f"#### Enviar cobrança — {competencia_label}")
    rot = {f"{x['destino']} · {_fmt(x['total'])} pendentes": x for x in grupos if x["emails"]}
    if rot:
        col_a, col_b = st.columns([2, 1])
        escolha = col_a.selectbox("Enviar para uma operação", ["—"] + list(rot.keys()), key="pendencias_destino_email")
        if col_b.button("Enviar e-mail", width="stretch") and escolha != "—":
            _enviar_grupo(rot[escolha])

    if st.button(f"✉️ Enviar cobrança de {competencia_label} para TODAS as operações com e-mail", type="primary"):
        enviados, falhas = 0, []
        for x in grupos:
            if not x["emails"]:
                continue
            ok_any = _enviar_grupo(x, silencioso=True)
            enviados += ok_any[0]
            falhas += ok_any[1]
        if enviados:
            st.success(f"{enviados} e-mail(s) de {competencia_label} enviado(s).")
        for f in falhas:
            st.error(f)
        if not enviados and not falhas:
            st.info("Nenhuma operação com e-mail para enviar.")


def _enviar_grupo(x, silencioso=False):
    pr = dp.precos()
    enviados, falhas = 0, []
    for email in x["emails"]:
        ok, msg = emailer.enviar_pendencia(
            email, x["destino"], x["itens"], x["total"],
            precos=pr, competencia_label=x["competencia_label"],
        )
        if ok:
            enviados += 1
        else:
            falhas.append(msg)
    if not silencioso:
        if enviados:
            st.success(f"{enviados} e-mail(s) de {x['competencia_label']} enviado(s) para {x['destino']}.")
        for f in falhas:
            st.error(f)
    return enviados, falhas
