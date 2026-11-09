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
        marker=dict(colors=["#0756B8", "#8BC8F5", "#D7E0EA"]),
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
    div[data-testid="stMetric"] {background:#F3F7FE;border:1px solid #D2E3FC;padding:8px 11px;border-radius:11px;min-height:64px;}
    div[data-testid="stMetricLabel"] p {font-size:11px;font-weight:700;color:#183B6B;margin-bottom:2px;}
    div[data-testid="stMetricValue"] {font-size:20px;font-weight:800;color:#064AA6;}
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

    st.markdown(f"""
    <style>
      .kpi-grid {{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:10px 0 16px;}}
      .kpi-card {{display:flex;align-items:center;gap:14px;min-height:104px;padding:17px 20px;border:1px solid #D2E3FC;border-radius:18px;background:linear-gradient(135deg,#FFFFFF 0%,#F3F8FF 100%);box-shadow:0 3px 10px rgba(6,74,166,.06);}}
      .kpi-icon {{width:60px;height:60px;flex:0 0 60px;display:flex;align-items:center;justify-content:center;border-radius:16px;background:#E1EEFF;color:#0756B8;}}\n      .kpi-icon svg {{width:42px;height:42px;display:block;}}
      .kpi-label {{font-size:14px;font-weight:700;color:#34445F;margin-bottom:5px;}}
      .kpi-value {{font-size:27px;line-height:1.15;font-weight:800;color:#0756B8;white-space:nowrap;}}
      .kpi-sub {{display:inline-block;margin-left:8px;padding:5px 10px;border-radius:20px;background:#DDF5E9;color:#078354;font-size:15px;font-weight:800;vertical-align:middle;}}
      .kpi-sub-red {{background:#FDE3E3;color:#D92323;}}
      .kpi-green .kpi-icon {{background:#DDF5E9;color:#078354;}}
      .kpi-green .kpi-value {{color:#078F61;}}
      .kpi-red .kpi-icon {{background:#FDE3E3;color:#D92323;}}
      .kpi-red .kpi-value {{color:#D92323;}}
      @media(max-width:850px) {{.kpi-grid {{grid-template-columns:repeat(2,minmax(0,1fr));}} .kpi-value {{font-size:22px;}}}}
      @media(max-width:560px) {{.kpi-grid {{grid-template-columns:1fr;}}}}
    </style>
    <div class="kpi-grid">
      <div class="kpi-card"><div class="kpi-icon"><svg viewBox="0 0 48 48" aria-hidden="true"><path d="M9 14 24 6l15 8v20l-15 8-15-8z" fill="none" stroke="currentColor" stroke-width="2.8" stroke-linejoin="round"/><path d="m9 14 15 8 15-8M24 22v20M17 10l15 8v8l-8 4-8-4v-8" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linejoin="round"/></svg></div><div><div class="kpi-label">Total de Leves</div><div class="kpi-value">{_fmt(total_leves)}</div></div></div>
      <div class="kpi-card kpi-green"><div class="kpi-icon"><svg viewBox="0 0 48 48" aria-hidden="true"><path d="m7 25 10 10L41 11" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/><path d="m12 12 8-5 17 7" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" opacity=".65"/></svg></div><div><div class="kpi-label">Leves que devolveram</div><div class="kpi-value">{_fmt(devolvidos)} <span class="kpi-sub">{devolvidos/total_leves:.1%}</span></div></div></div>
      <div class="kpi-card kpi-red"><div class="kpi-icon"><svg viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="17" fill="none" stroke="currentColor" stroke-width="3.5"/><path d="M24 13v14M24 33v2" stroke="currentColor" stroke-width="4" stroke-linecap="round"/></svg></div><div><div class="kpi-label">Leves que não devolveram</div><div class="kpi-value" style="color:#0756B8">{_fmt(nao_devolveram)} <span class="kpi-sub kpi-sub-red">{nao_devolveram/total_leves:.1%}</span></div></div></div>
      <div class="kpi-card"><div class="kpi-icon"><svg viewBox="0 0 48 48" aria-hidden="true"><path d="M5 14h25v21H5zM30 21h8l6 8v6H30z" fill="none" stroke="currentColor" stroke-width="3" stroke-linejoin="round"/><circle cx="14" cy="36" r="4" fill="#fff" stroke="currentColor" stroke-width="3"/><circle cx="36" cy="36" r="4" fill="#fff" stroke="currentColor" stroke-width="3"/><path d="M35 22v7h8" fill="none" stroke="currentColor" stroke-width="2.5"/></svg></div><div><div class="kpi-label">Valor total enviado</div><div class="kpi-value">{dp.fmt_brl(valor_total)}</div></div></div>
      <div class="kpi-card kpi-green"><div class="kpi-icon"><svg viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="16" fill="none" stroke="currentColor" stroke-width="3.2"/><path d="m15 24 6 6 13-14" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div><div><div class="kpi-label">Valor devolvido</div><div class="kpi-value">{dp.fmt_brl(valor_devolvido)}</div></div></div>
      <div class="kpi-card kpi-red"><div class="kpi-icon"><svg viewBox="0 0 48 48" aria-hidden="true"><ellipse cx="17" cy="13" rx="10" ry="5" fill="none" stroke="currentColor" stroke-width="2.8"/><path d="M7 13v17c0 3 4 5 10 5s10-2 10-5V13M7 21c0 3 4 5 10 5s10-2 10-5M7 29c0 3 4 5 10 5s10-2 10-5" fill="none" stroke="currentColor" stroke-width="2.8"/><ellipse cx="34" cy="10" rx="8" ry="4" fill="none" stroke="currentColor" stroke-width="2.6"/><path d="M26 10v14c0 2 3 4 8 4s8-2 8-4V10M26 17c0 2 3 4 8 4s8-2 8-4" fill="none" stroke="currentColor" stroke-width="2.6"/></svg></div><div><div class="kpi-label">Valor pendente</div><div class="kpi-value">{dp.fmt_brl(valor_pendente)}</div></div></div>
    </div>
    """, unsafe_allow_html=True)

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
            xaxis=dict(visible=False, showgrid=False, zeroline=False, showticklabels=False, title=None),
            yaxis=dict(visible=False, showgrid=False, zeroline=False, showticklabels=False, title=None),
        )
        fig_val.update_traces(textposition="outside", cliponaxis=False,
                              textfont=dict(size=10, color="#17365F"))
        st.plotly_chart(fig_val, use_container_width=True, config={"displayModeBar": False})
    with c3:
        # Evolução mensal apenas da taxa de devolução sobre o valor enviado.
        meses_evolucao = sorted(envios["mes"].dropna().astype(str).unique().tolist())[-6:]
        evolucao = []
        for competencia in meses_evolucao:
            hist = dp.conciliacao(competencia)
            if hist.empty:
                continue
            enviado_hist = sum(_valor(r["enviado"], r["tipo"], precos) for _, r in hist.iterrows())
            devolvido_hist = sum(_valor(r["devolvido"], r["tipo"], precos) for _, r in hist.iterrows())
            pendente_hist = sum(_valor(r["cobravel"], r["tipo"], precos) for _, r in hist.iterrows())
            taxa_devolucao = (devolvido_hist / enviado_hist * 100) if enviado_hist > 0 else 0
            evolucao.append({
                "Mês": dp.rotulo_mes(competencia)[:3],
                "Taxa de devolução": taxa_devolucao,
            })
        if evolucao:
            ev = pd.DataFrame(evolucao)
            variacoes = ev["Taxa de devolução"].diff()
            rotulos_taxa = []
            for idx, taxa in enumerate(ev["Taxa de devolução"]):
                if idx == 0 or pd.isna(variacoes.iloc[idx]):
                    rotulos_taxa.append(f"{taxa:.1f}%")
                else:
                    delta = variacoes.iloc[idx]
                    seta = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
                    rotulos_taxa.append(f"{taxa:.1f}% {seta} {abs(delta):.1f} p.p.")
            fig_ev = go.Figure()
            fig_ev.add_scatter(
                x=ev["Mês"], y=ev["Taxa de devolução"], name="% devolvido",
                mode="lines+markers+text", text=rotulos_taxa, textposition="top center",
                textfont=dict(size=9, color="#0756B8"),
                line=dict(color="#0756B8", width=3),
                marker=dict(size=8, color="#fff", line=dict(color="#0756B8", width=2)),
            )
            fig_ev.update_layout(
                title=dict(text="Evolução da taxa de devolução", x=0.03, xanchor="left",
                           font=dict(size=15, color="#123B78")),
                height=310, margin=dict(l=18,r=18,t=52,b=48),
                font=dict(family="Montserrat", size=10, color="#17365F"),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", y=-0.2, font=dict(size=9)),
                xaxis=dict(showgrid=False, showline=False, showticklabels=True, ticks="", title=None,
                           tickfont=dict(color="#64748B", size=10), zeroline=False),
                yaxis=dict(range=[0, 110], showgrid=False, showline=False, showticklabels=False,
                           ticks="", title=None, zeroline=False),
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
    # Exibe aproximadamente 15 Leves por vez; os demais ficam na rolagem vertical.
    altura_tabela = 15 * 29 + 48
    html_tabela = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800&display=swap" rel="stylesheet">
      <style>
        * { box-sizing: border-box; }
        body { margin: 0; padding: 0; background: transparent; font-family: 'Montserrat', Arial, sans-serif; }
        .pendencias-table-wrap {
          width: 100%; max-height: 483px; overflow: auto;
          border: 1px solid #C9DCF5; border-radius: 10px; background: #fff;
        }
        table.pendencias-table {
          width: 100%; min-width: 1120px; border-collapse: separate;
          border-spacing: 0; font-family: 'Montserrat', Arial, sans-serif;
          color: #17365F; font-size: 12px; font-weight: 600;
        }
        .pendencias-table thead th {
          position: sticky; top: 0; z-index: 2;
          background: #0866F5 !important; color: #fff !important;
          font-weight: 700 !important; text-align: center !important;
          vertical-align: middle !important; padding: 8px 6px !important;
          font-family: 'Montserrat', Arial, sans-serif !important; font-size: 12px !important;
          border-right: 1px solid rgba(255,255,255,.35);
          border-bottom: 1px solid #0757D8; white-space: normal;
        }
        .pendencias-table tbody td {
          text-align: center !important; vertical-align: middle !important;
          padding: 6px 5px !important; border-right: 1px solid #E1EAF5;
          border-bottom: 1px solid #E1EAF5; white-space: nowrap;
          background: #fff; font-family: 'Montserrat', Arial, sans-serif !important;
          font-size: 11px !important; font-weight: 600 !important;
        }
        .pendencias-table tbody tr:nth-child(even) td { background: #F1F6FD; }
        /* Coluna da sigla mais larga para facilitar a leitura */
        .pendencias-table thead th:first-child,
        .pendencias-table tbody td:first-child {
          min-width: 88px !important;
          width: 88px !important;
          padding-left: 10px !important;
          padding-right: 10px !important;
        }
        /* Status com mais espaço para não cortar "Não devolveu" */
        .pendencias-table thead th:nth-child(2),
        .pendencias-table tbody td:nth-child(2) {
          min-width: 112px !important;
          width: 112px !important;
          padding-left: 10px !important;
          padding-right: 10px !important;
        }
        /* Destaque visual para o saldo e o valor pendente */
        .pendencias-table thead th:nth-child(12),
        .pendencias-table thead th:nth-child(13) {
          background: #064AA6 !important;
          color: #E7ECF2 !important;
          border-left: 2px solid rgba(255,255,255,.55) !important;
          border-bottom: 1px solid #0757D8 !important;
        }
        .pendencias-table tbody td:nth-child(12),
        .pendencias-table tbody td:nth-child(13) {
          background: #F7F8FA !important;
          color: #064AA6 !important;
          font-weight: 800 !important;
          border-left: 1px solid #E3E7EC !important;
        }
        .pendencias-table tbody tr:nth-child(even) td:nth-child(12),
        .pendencias-table tbody tr:nth-child(even) td:nth-child(13) {
          background: #F1F3F5 !important;
        }
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
