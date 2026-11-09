"""
page_8.py — Dashboard gerencial de pendências de devolução por competência.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

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
    .pendencias .block-container {padding-top:1rem;}
    .pendencias-header {background:linear-gradient(105deg,#064AA6 0%,#0877E8 100%);padding:17px 24px;border-radius:14px;color:#fff;margin:0 0 16px;}
    .pendencias-title {font-size:27px;font-weight:800;color:#fff;margin:0;line-height:1.2;}
    .pendencias-sub {font-size:13px;color:#EAF4FF;margin:4px 0 0;font-weight:600;}
    div[data-testid="stMetric"] {background:#F3F7FE;border:1px solid #D2E3FC;padding:13px 14px;border-radius:13px;min-height:78px;}
    div[data-testid="stMetricLabel"] p {font-size:12px;font-weight:700;color:#183B6B;}
    div[data-testid="stMetricValue"] {font-size:23px;font-weight:800;color:#064AA6;}
    .section-title {font-size:17px;font-weight:800;color:#064AA6;margin:12px 0 10px;}
    div[data-testid="stDataFrame"] {border:1px solid #C8DDF8;border-radius:12px;overflow:hidden;}
    div[data-testid="stSelectbox"] label {font-weight:700;color:#183B6B;}
    div[data-testid="stButton"] button {border:1px solid #BBD4F5;border-radius:9px;font-weight:700;color:#064AA6;}
    .stPlotlyChart {border:1px solid #D6E5FA;border-radius:13px;padding:7px;background:#fff;}
    </style>
    <div class="pendencias">
      <div class="pendencias-header">
        <div class="pendencias-title">📦 Pendências de Devolução</div>
        <div class="pendencias-sub">Análise gerencial das devoluções de insumos (Leves)</div>
      </div>
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

    c1, c2, c3 = st.columns([1, 1.08, 1.25])
    with c1:
        fig_status = _grafico_donut(resumo)
        fig_status.update_layout(
            title=dict(text="Situação das devoluções (Leves)", x=0.03, xanchor="left",
                       font=dict(size=15, color="#123B78")),
            height=285, margin=dict(l=8, r=8, t=42, b=8),
            legend=dict(orientation="h", y=-0.12, x=0.02, font=dict(size=10)),
        )
        st.plotly_chart(fig_status, use_container_width=True, config={"displayModeBar": False})
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
        fig_val.update_layout(
            showlegend=False, height=285,
            margin=dict(l=8, r=16, t=42, b=8),
            font=dict(family="Montserrat", size=10, color="#17365F"),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            title=dict(x=0.03, xanchor="left", font=dict(size=15, color="#123B78")),
            xaxis=dict(title="Valor", gridcolor="#E6EEF8", zeroline=False,
                       tickfont=dict(color="#73839A")),
            yaxis=dict(title="Situação", autorange="reversed",
                       tickfont=dict(color="#73839A")),
        )
        fig_val.update_traces(textposition="outside", cliponaxis=False,
                              textfont=dict(size=10, color="#17365F"))
        st.plotly_chart(fig_val, use_container_width=True, config={"displayModeBar": False})
    with c3:
        # Evolução das competências mais recentes disponíveis.
        meses_evolucao = sorted(envios["mes"].dropna().astype(str).unique().tolist())[-6:]
        evolucao = []
        for competencia in meses_evolucao:
            hist = dp.conciliacao(competencia)
            if hist.empty:
                continue
            devolvido_hist = sum(_valor(r["devolvido"], r["tipo"], precos) for _, r in hist.iterrows())
            pendente_hist = sum(_valor(r["cobravel"], r["tipo"], precos) for _, r in hist.iterrows())
            evolucao.append({
                "Mês": dp.rotulo_mes(competencia)[:3],
                "Valor devolvido": devolvido_hist,
                "Valor pendente": pendente_hist,
                "Valor total": devolvido_hist + pendente_hist,
            })
        if evolucao:
            ev = pd.DataFrame(evolucao)
            fig_ev = go.Figure()
            fig_ev.add_bar(x=ev["Mês"], y=ev["Valor devolvido"], name="Valor devolvido",
                           marker_color="#0756B8")
            fig_ev.add_bar(x=ev["Mês"], y=ev["Valor pendente"], name="Valor pendente",
                           marker_color="#8BC8F5")
            fig_ev.add_scatter(x=ev["Mês"], y=ev["Valor total"], name="Valor total",
                               mode="lines+markers", line=dict(color="#0756B8", width=2),
                               marker=dict(size=6, color="#fff", line=dict(color="#0756B8", width=2)))
            fig_ev.update_layout(
                title=dict(text="Evolução das devoluções", x=0.03, xanchor="left",
                           font=dict(size=15, color="#123B78")),
                barmode="stack", height=285, margin=dict(l=8,r=8,t=42,b=8),
                font=dict(family="Montserrat", size=10, color="#17365F"),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", y=-0.22, font=dict(size=9)),
                xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#E6EEF8", tickformat="~s"),
            )
            st.plotly_chart(fig_ev, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Sem histórico suficiente para exibir a evolução.")

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
    # Renderização em iframe HTML: garante CSS próprio sem o Markdown escapar as tags.
    tabela_html = tabela.to_html(index=False, border=0, escape=True)
    tabela_html = tabela_html.replace(
        '<table',
        '<table class="pendencias-table"',
        1,
    )
    altura_tabela = min(720, max(190, 43 + len(tabela) * 34))
    html_tabela = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        * { box-sizing: border-box; }
        body { margin: 0; padding: 0; background: transparent; font-family: Montserrat, Arial, sans-serif; }
        .pendencias-table-wrap {
          width: 100%; max-height: 700px; overflow: auto;
          border: 1px solid #C9DCF5; border-radius: 10px; background: #fff;
        }
        table.pendencias-table {
          width: 100%; min-width: 1250px; border-collapse: separate;
          border-spacing: 0; font-family: Montserrat, Arial, sans-serif;
          color: #17365F; font-size: 12px;
        }
        .pendencias-table thead th {
          position: sticky; top: 0; z-index: 2;
          background: #0866F5 !important; color: #fff !important;
          font-weight: 700 !important; text-align: center !important;
          vertical-align: middle !important; padding: 11px 8px !important;
          border-right: 1px solid rgba(255,255,255,.35);
          border-bottom: 1px solid #0757D8; white-space: normal;
        }
        .pendencias-table tbody td {
          text-align: center !important; vertical-align: middle !important;
          padding: 9px 8px !important; border-right: 1px solid #E1EAF5;
          border-bottom: 1px solid #E1EAF5; white-space: nowrap;
          background: #fff;
        }
        .pendencias-table tbody tr:nth-child(even) td { background: #F1F6FD; }
        .pendencias-table tbody tr:last-child td { border-bottom: 0; }
        .pendencias-table th:last-child, .pendencias-table td:last-child { border-right: 0; }
      </style>
    </head>
    <body>
      <div class="pendencias-table-wrap">""" + tabela_html + """</div>
    </body>
    </html>
    """
    components.html(html_tabela, height=altura_tabela, scrolling=True)

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
