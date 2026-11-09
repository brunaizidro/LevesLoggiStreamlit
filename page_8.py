"""
page_8.py — Dashboard gerencial de pendências de devolução por competência.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data_processing as dp
import emailer


def _fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def _valor(qtd, tipo, precos):
    return float(qtd or 0) * float(precos.get(str(tipo).upper(), 0) or 0)


def _grupos_email(pend, competencia_label):
    grupos = []
    if pend.empty:
        return grupos
    for destino, g in pend.groupby("destino"):
        itens = [
            {"tipo": r["tipo"], "enviado": int(r["enviado"]),
             "devolvido": int(r["devolvido"]), "pendente": int(r["cobravel"])}
            for _, r in g.iterrows() if int(r["cobravel"]) > 0
        ]
        total = sum(i["pendente"] for i in itens)
        if total:
            grupos.append({
                "destino": destino, "itens": itens, "total": total,
                "emails": dp.emails_por_destino(destino),
                "competencia_label": competencia_label,
                "valor": sum(_valor(i["pendente"], i["tipo"], dp.precos()) for i in itens),
            })
    return grupos


def _montar_resumo(pend, precos):
    tipos = ["SACA", "GAYLORD", "PALLET"]
    linhas = []
    for destino, g in pend.groupby("destino"):
        linha = {"Leve": destino}
        total_pendente = 0
        total_valor = 0.0
        total_enviado = 0
        total_devolvido = 0
        for tipo, nome in [("SACA", "Sacas"), ("GAYLORD", "Gaylords"), ("PALLET", "Pallets")]:
            t = g[g["tipo"].astype(str).str.upper() == tipo]
            enviado = int(t["enviado"].sum()) if not t.empty else 0
            devolvido = int(t["devolvido"].sum()) if not t.empty else 0
            pendente = int(t["cobravel"].sum()) if not t.empty else 0
            linha[f"{nome} enviados"] = enviado
            linha[f"{nome} devolvidos"] = devolvido
            linha[f"{nome} pendentes"] = pendente
            total_pendente += pendente
            total_valor += _valor(pendente, tipo, precos)
            total_enviado += enviado
            total_devolvido += devolvido
        if total_pendente == 0:
            status = "Devolvido"
        elif total_devolvido > 0:
            status = "Parcial"
        else:
            status = "Não devolveu"
        linha["Status"] = status
        linha["Saldo pendente"] = total_pendente
        linha["Valor pendente"] = dp.fmt_brl(total_valor)
        linha["_valor_num"] = total_valor
        linha["_total_enviado"] = total_enviado
        linha["_total_devolvido"] = total_devolvido
        linhas.append(linha)
    return pd.DataFrame(linhas)


def _grafico_donut(resumo):
    contagem = resumo["Status"].value_counts().reindex(
        ["Devolvido", "Parcial", "Não devolveu"], fill_value=0
    )
    fig = go.Figure(go.Pie(
        labels=contagem.index, values=contagem.values, hole=.64,
        marker=dict(colors=["#22C55E", "#F4B740", "#F87171"]),
        textinfo="value+percent", textposition="inside",
    ))
    fig.update_layout(
        title="Situação das devoluções (Leves)", height=310,
        margin=dict(l=10, r=10, t=48, b=10), font=dict(family="Montserrat"),
        legend=dict(orientation="h", y=-.08), paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def page_8():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
    .pendencias, .pendencias * {font-family:'Montserrat',sans-serif;}
    .pendencias-title {font-size:30px;font-weight:800;color:#123B78;margin:0;line-height:1.2;}
    .pendencias-sub {font-size:13px;color:#58708F;margin:4px 0 18px;font-weight:500;}
    .pendencias .block-container {padding-top:1.2rem;}
    div[data-testid="stMetric"] {background:#F4F8FF;border:1px solid #D6E5FA;padding:12px 14px;border-radius:13px;}
    div[data-testid="stMetricLabel"] p {font-size:12px;font-weight:700;color:#29476F;}
    div[data-testid="stMetricValue"] {font-size:23px;font-weight:800;color:#123B78;}
    .section-title {font-size:17px;font-weight:800;color:#123B78;margin:8px 0 10px;}
    div[data-testid="stDataFrame"] {border:1px solid #D6E5FA;border-radius:12px;overflow:hidden;}
    </style>
    <div class="pendencias">
      <div class="pendencias-title">📦 Pendências de Devolução</div>
      <div class="pendencias-sub">Análise gerencial das devoluções de insumos (Leves)</div>
    </div>
    """, unsafe_allow_html=True)

    envios = dp.envios_df()
    if envios.empty or "mes" not in envios.columns:
        st.info("Ainda não há envios registrados para consultar.")
        return

    meses = sorted(envios["mes"].dropna().astype(str).unique().tolist(), reverse=True)
    if not meses:
        st.info("Não foram encontradas competências nos envios.")
        return

    f1, f2, f3 = st.columns([1.15, 1.15, .55])
    with f1:
        mes = st.selectbox("Mês de referência", meses, index=0,
                           format_func=dp.rotulo_mes, key="pendencias_competencia")
    competencia_label = dp.rotulo_mes(mes)
    pend = dp.conciliacao(mes)
    if pend.empty:
        st.info(f"Não há envios registrados para {competencia_label}.")
        return

    destinos = sorted(pend["destino"].dropna().astype(str).unique().tolist())
    with f2:
        destino_filtro = st.selectbox("Operação (Leve)", ["Todas"] + destinos,
                                      key="pendencias_destino_filtro")
    with f3:
        st.markdown("<div style='height:27px'></div>", unsafe_allow_html=True)
        if st.button("↻ Limpar filtros", use_container_width=True):
            st.session_state["pendencias_destino_filtro"] = "Todas"
            st.rerun()

    if destino_filtro != "Todas":
        pend = pend[pend["destino"] == destino_filtro].copy()

    precos = dp.precos()
    resumo = _montar_resumo(pend, precos)
    if resumo.empty:
        st.info("Não há dados para os filtros selecionados.")
        return

    total_leves = len(resumo)
    devolvidos = int((resumo["Status"] == "Devolvido").sum())
    parciais = int((resumo["Status"] == "Parcial").sum())
    nao_devolveram = int((resumo["Status"] == "Não devolveu").sum())
    qtd_devolvida = sum(int(pend.loc[pend["tipo"].astype(str).str.upper() == tipo, "devolvido"].sum())
                        for tipo in ["SACA", "GAYLORD", "PALLET"])
    qtd_pendente = int(resumo["Saldo pendente"].sum())
    valor_devolvido = sum(_valor(r["devolvido"], r["tipo"], precos) for _, r in pend.iterrows())
    valor_pendente = float(resumo["_valor_num"].sum())
    valor_total = valor_devolvido + valor_pendente

    st.caption(f"Indicadores e detalhamento da competência {competencia_label}.")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total de Leves", _fmt(total_leves))
    k2.metric("Leves que devolveram", f"{_fmt(devolvidos)} ({devolvidos/total_leves:.1%})")
    k3.metric("Devolução parcial", f"{_fmt(parciais)} ({parciais/total_leves:.1%})")
    k4.metric("Leves que não devolveram", f"{_fmt(nao_devolveram)} ({nao_devolveram/total_leves:.1%})")
    v1, v2, v3 = st.columns(3)
    v1.metric("Valor devolvido", dp.fmt_brl(valor_devolvido))
    v2.metric("Valor pendente", dp.fmt_brl(valor_pendente))
    v3.metric("Valor total enviado", dp.fmt_brl(valor_total))

    c1, c2 = st.columns([1, 1.1])
    with c1:
        st.plotly_chart(_grafico_donut(resumo), use_container_width=True)
    with c2:
        valores = pd.DataFrame([
            {"Situação": "Devolvido", "Valor": valor_devolvido},
            {"Situação": "Pendente", "Valor": valor_pendente},
        ])
        fig_val = px.bar(valores, x="Valor", y="Situação", orientation="h",
                         color="Situação",
                         color_discrete_map={"Devolvido": "#0756B8", "Pendente": "#8BC8F5"},
                         text=valores["Valor"].map(dp.fmt_brl),
                         title="Valores (R$)")
        fig_val.update_layout(showlegend=False, height=310, margin=dict(l=10,r=20,t=48,b=10),
                              font_family="Montserrat", paper_bgcolor="rgba(0,0,0,0)")
        fig_val.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(fig_val, use_container_width=True)

    st.markdown('<div class="section-title">Detalhamento por Leve</div>', unsafe_allow_html=True)
    colunas = [
        "Leve", "Status",
        "Sacas enviados", "Sacas devolvidos", "Sacas pendentes",
        "Gaylords enviados", "Gaylords devolvidos", "Gaylords pendentes",
        "Pallets enviados", "Pallets devolvidos", "Pallets pendentes",
        "Saldo pendente", "Valor pendente",
    ]
    tabela = resumo.rename(columns={
        "Sacas enviados": "Sacas enviados", "Sacas devolvidos": "Sacas devolvidos",
        "Sacas pendentes": "Sacas pendentes",
    })
    tabela = tabela[colunas].copy()
    st.dataframe(
        tabela, use_container_width=True, hide_index=True,
        column_config={
            "Leve": st.column_config.TextColumn("Leve (Sigla)", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Saldo pendente": st.column_config.NumberColumn("Saldo pendente (qtd)", format="%d"),
        },
    )

    st.markdown("---")
    st.markdown('<div class="section-title">✉️ Enviar e-mail de cobrança</div>', unsafe_allow_html=True)
    st.caption("Selecione as operações com saldo pendente e envie um lembrete de devolução.")
    pend_email = pend[pd.to_numeric(pend["cobravel"], errors="coerce").fillna(0) > 0].copy()
    grupos = _grupos_email(pend_email, competencia_label)
    sem_email = [x["destino"] for x in grupos if not x["emails"]]
    grupos_com_email = [x for x in grupos if x["emails"]]

    if not emailer.smtp_configurado():
        st.warning("Configure o servidor de e-mail (SMTP) em Configurações para enviar cobranças.")
        return
    if not grupos_com_email:
        st.info("Não há operações com pendências e e-mail cadastrado para esta competência.")
        return

    rot = {f"{x['destino']} · {_fmt(x['total'])} pendentes": x for x in grupos_com_email}
    col_a, col_b = st.columns([2, 1])
    escolha = col_a.selectbox("Destinatários", ["Todas as operações com e-mail"] + list(rot.keys()),
                              key="pendencias_destino_email")
    modelo = col_b.selectbox("Modelo de e-mail", ["Cobrança de devolução"], key="pendencias_modelo_email")
    if st.button("➤ Enviar e-mail", type="primary", use_container_width=True):
        alvos = grupos_com_email if escolha == "Todas as operações com e-mail" else [rot[escolha]]
        enviados, falhas = 0, []
        for x in alvos:
            ok, erros = _enviar_grupo(x, silencioso=True)
            enviados += ok
            falhas.extend(erros)
        if enviados:
            st.success(f"{enviados} e-mail(s) enviado(s) para {competencia_label}.")
        for erro in falhas:
            st.error(erro)
    if sem_email:
        st.caption("Sem e-mail cadastrado (não serão notificadas): " + ", ".join(sem_email))


def _enviar_grupo(x, silencioso=False):
    pr = dp.precos()
    enviados, falhas = 0, []
    emails = list(dict.fromkeys(
        str(email).strip() for email in x.get("emails", []) if str(email).strip()
    ))
    if emails:
        ok, msg = emailer.enviar_pendencia(
            emails[0], x["destino"], x["itens"], x["total"],
            precos=pr, competencia_label=x["competencia_label"],
            destinatarios_adicionais=emails[1:],
        )
        if ok:
            enviados = 1
        else:
            falhas.append(msg)
    if not silencioso:
        if enviados:
            st.success(f"1 e-mail de {x['competencia_label']} enviado para {x['destino']} ({len(emails)} destinatário(s)).")
        for erro in falhas:
            st.error(erro)
    return enviados, falhas
