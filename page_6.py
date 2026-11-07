"""
page_6.py — Conciliação enviado × devolvido (cobrança).

Confronta, por operação × tipo, o que foi enviado e o que já foi devolvido
(recebido), destacando o que está em aberto e o que é cobrável (parado há mais
que o prazo). Aging FIFO. Quantidades e valores quando houver preço configurado.
"""

from __future__ import annotations

from datetime import datetime
import io

import plotly.express as px
import pandas as pd
import streamlit as st

import data_extraction as dados
import data_processing as dp
import emailer


def _fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def _centralizar_tabela(df):
    """Configura as colunas da tabela para exibir o conteúdo centralizado."""
    config = {}
    for col in df.columns:
        serie = df[col]
        if serie.dtype.kind in "biufc":
            config[col] = st.column_config.NumberColumn(col, alignment="center")
        else:
            config[col] = st.column_config.TextColumn(col, alignment="center")
    return config


def page_6():
    st.subheader("Conciliação e cobrança")
    st.markdown("""
    <style>
    /* Identidade visual alinhada aos módulos Envios e Recebimentos */
    .concil-info-blue{
        background:#EAF3FF!important;border:1px solid #D5E6FF!important;
        border-radius:12px;padding:15px 18px;margin:8px 0 12px;
        color:#D62828!important;font-family:'Montserrat',sans-serif;
        font-size:15px;line-height:1.6;font-weight:600;
    }
    .concil-info-blue strong{color:#D62828!important;font-weight:800;}

    /* Avisos da conciliação: troca apenas o amarelo por azul-claro e mantém fonte preta */
    [data-testid="stAlert"]{
        background:#EAF3FF!important;
        border:1px solid #D5E6FF!important;
        border-radius:12px!important;
        color:#000000!important;
    }
    [data-testid="stAlert"] [data-testid="stMarkdownContainer"],
    [data-testid="stAlert"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stAlert"] [data-testid="stMarkdownContainer"] strong{
        color:#000000!important;
    }
    [data-testid="stAlert"] svg{fill:#0067FC!important;color:#0067FC!important;}

    /* Tabela no mesmo padrão visual do detalhamento de Envios */
    /* Valores monetários em padrão contábil, centralizados nas tabelas */
    .concil-html-table th:nth-child(7),
    .concil-html-table td:nth-child(7),
    .concil-html-table th:nth-child(8),
    .concil-html-table td:nth-child(8),
    .concil-resumo-table th:nth-child(6),
    .concil-resumo-table td:nth-child(6){
        text-align:center!important;
        font-variant-numeric:tabular-nums;
        white-space:nowrap;
    }
    /* Tabela de saldo pendente por e-mail no padrão visual do portal */
    .concil-email-table-wrap{height:335px;overflow:auto;}
    .concil-email-table{min-width:850px;table-layout:auto;}
    .concil-email-table th{
        text-transform:none!important;text-align:center!important;
        padding:12px 14px!important;white-space:nowrap;
    }
    .concil-email-table td{
        text-align:center!important;padding:11px 14px!important;
        font-weight:600!important;vertical-align:middle;
    }
    .concil-email-table th:nth-child(4),
    .concil-email-table td:nth-child(4){
        text-align:center!important;font-variant-numeric:tabular-nums;white-space:nowrap;
    }
    .concil-email-table td:nth-child(3){
        text-align:left!important;white-space:normal;overflow-wrap:anywhere;min-width:300px;
    }
    /* Ajustes específicos do resumo: cabeçalho simples e sem índice duplicado */
    .concil-resumo-table-wrap{height:335px;overflow:auto;}
    .concil-resumo-table{table-layout:auto;min-width:760px;}
    .concil-resumo-table th{
        text-transform:none!important;letter-spacing:0;
        text-align:center!important;padding:12px 14px!important;
    }
    .concil-resumo-table td{
        text-align:center!important;padding:11px 14px!important;
        font-weight:650!important;
    }
    .concil-resumo-table th:first-child,
    .concil-resumo-table td:first-child{
        text-align:center!important;font-weight:750!important;
        position:sticky;left:0;z-index:1;
    }
    .concil-resumo-table th:first-child{z-index:3;background:#0067FC!important;}

    .concil-html-table-wrap{
        height:335px;overflow:auto;border:1px solid #DCE7F6;
        border-radius:10px;background:#FFFFFF;
    }
    .concil-html-table{
        width:100%;border-collapse:separate;border-spacing:0;
        font-family:'Montserrat',sans-serif!important;font-size:13px;color:#172B4D;
    }
    .concil-html-table th{
        position:sticky;top:0;z-index:2;background:#0067FC!important;
        color:#FFFFFF!important;font-weight:700!important;text-align:center;
        padding:11px 12px;white-space:nowrap;
    }
    .concil-html-table td{
        background:#FFFFFF;color:#172B4D;font-weight:500;text-align:center;
        padding:10px 12px;border-bottom:1px solid #E8EEF7;white-space:nowrap;
    }
    .concil-html-table tbody tr:nth-child(even) td{background:#F7FAFF;}
    .concil-html-table tbody tr:hover td{background:#EEF5FF;}

    .concil-intro{color:#627895;font-size:14px;line-height:1.65;margin:-4px 0 20px;}
    [data-testid="stAppViewContainer"] h2,
    [data-testid="stAppViewContainer"] h3,
    [data-testid="stAppViewContainer"] h4{color:#102B50;font-weight:800;}
    [data-testid="stAppViewContainer"] [data-testid="stMetric"]{
        background:linear-gradient(145deg,#F3F8FF 0%,#EAF3FF 100%);
        border:1px solid #D9E8FF;border-radius:14px;padding:16px 17px;
        box-shadow:0 3px 12px rgba(16,43,80,.035);min-height:104px;
    }
    [data-testid="stMetricLabel"]{color:#536987!important;font-weight:650!important;}
    [data-testid="stMetricValue"]{
        color:#102B50!important;font-weight:850!important;
        font-size:clamp(19px,1.5vw,25px)!important;
        line-height:1.15!important;letter-spacing:-.35px;
        white-space:nowrap;overflow:visible;text-align:center!important;
    }
    [data-testid="stMetricValue"] div{
        font-size:inherit!important;line-height:inherit!important;
        white-space:nowrap!important;text-align:center!important;width:100%;
    }
    [data-testid="stMetric"]{
        min-width:0!important;overflow:hidden;text-align:center!important;
        display:flex;flex-direction:column;align-items:center;justify-content:center;
    }
    [data-testid="stMetricLabel"]{
        font-size:13px!important;text-align:center!important;width:100%;
    }
    [data-testid="stMetricDelta"]{justify-content:center!important;text-align:center!important;}
    [data-testid="stMetricDelta"]{font-weight:700!important;}
    [data-testid="stSelectbox"] label,
    [data-testid="stCheckbox"] label,
    [data-testid="stTextInput"] label{color:#102B50!important;font-weight:700!important;}
    [data-testid="stSelectbox"] [data-baseweb="select"]>div{
        border:1px solid #D5E4F8;border-radius:10px;background:#FFFFFF;
    }
    [data-testid="stDataFrame"],[data-testid="stTable"]{
        border:1px solid #DCE8FA;border-radius:12px;overflow:hidden;
    }
    [data-testid="stPlotlyChart"]{
        background:#FFFFFF;border:1px solid #DCE8FA;border-radius:14px;
        padding:10px 10px 2px;box-shadow:0 3px 12px rgba(16,43,80,.03);
    }
    [data-testid="stVerticalBlockBorderWrapper"]{
        border:1px solid #DCE8FA!important;border-radius:15px!important;
        background:#FFFFFF!important;box-shadow:0 3px 12px rgba(16,43,80,.035);
    }
    [data-testid="stButton"] button,[data-testid="stDownloadButton"] button{
        border-radius:10px!important;font-weight:750!important;min-height:42px;
    }
    /* Botão de exportação igual ao "Baixar CSV" da aba Envios */
    [data-testid="stDownloadButton"]{
        margin-top:4px!important;
    }
    [data-testid="stDownloadButton"] button{
        min-height:40px!important;
        border-radius:9px!important;
        font-family:'Montserrat',sans-serif!important;
        font-weight:700!important;
        color:#075BEA!important;
        border:1px solid #D5E5FF!important;
        background:#EEF5FF!important;
    }
    [data-testid="stDownloadButton"] button *{
        color:#075BEA!important;
        -webkit-text-fill-color:#075BEA!important;
    }
    [data-testid="stButton"] button[kind="primary"],
    [data-testid="stFormSubmitButton"] button[kind="primary"]{
        background:#0067FC!important;border-color:#0067FC!important;color:#FFFFFF!important;
    }
    [data-testid="stButton"] button[kind="primary"] *,
    [data-testid="stFormSubmitButton"] button[kind="primary"] *{
        color:#FFFFFF!important;-webkit-text-fill-color:#FFFFFF!important;
    }
    hr{border-color:#DCE8FA!important;}
    .concil-section-title{display:flex;align-items:center;gap:9px;color:#102B50;
        font-size:18px;font-weight:800;margin:18px 0 10px;}
    .concil-section-title .ico{display:inline-flex;color:#0067FC;font-size:20px;}
    </style>
    """, unsafe_allow_html=True)
    st.markdown(
        "<p class='concil-intro'>Cobrança por <b>competência de mês</b>. A operação tem até o "
        "<b>dia 5 do mês seguinte</b> para devolver os itens do mês. O que não voltar até lá é cobrável.</p>",
        unsafe_allow_html=True,
    )

    env = dp.envios_df()
    if env.empty:
        st.info("Nenhum envio registrado ainda.")
        return

    meses = sorted(env["mes"].unique(), reverse=True)
    rotulos = {m: dp.rotulo_mes(m) for m in meses}
    idx = next((i for i, m in enumerate(meses) if dp.competencia_fechavel(m)), 0)
    escolha = st.selectbox("Competência", [rotulos[m] for m in meses], index=idx)
    mes = next(m for m, r in rotulos.items() if r == escolha)

    prazo_ts = dp.prazo_devolucao(mes)
    fechavel = dp.competencia_fechavel(mes)
    prazo_txt = prazo_ts.strftime("%d/%m/%Y")
    if fechavel:
        st.caption(f"Prazo de devolução encerrado em **{prazo_txt}** — competência pronta para fechar.")
    else:
        st.caption(f"⏳ Devoluções desta competência são aceitas até **{prazo_txt}** — feche a cobrança após essa data.")

    df = dp.conciliacao(mes)
    if df.empty:
        st.warning("Sem envios nesta competência.")
        return

    # ---- Filtro de operação ----
    operacoes = sorted(df["destino"].dropna().astype(str).unique().tolist(), key=str.lower)
    op_escolhida = st.selectbox(
        "Operação",
        ["Todas as operações"] + operacoes,
        index=0,
        key="concil_operacao",
        help="Filtra a visão da conciliação para uma operação específica. O fechamento da competência continua considerando todas as operações.",
    )

    df_view = df
    if op_escolhida != "Todas as operações":
        df_view = df[df["destino"].astype(str) == op_escolhida].copy()

    if df_view.empty:
        st.info(f"Nenhum registro encontrado para a operação **{op_escolhida}** nesta competência.")
        return

    # ---- Preços ----
    pr = dp.precos()
    usa_valor = dp.tem_precos()

    # ---- Totais ----
    rot_cobravel = "Cobrável" if fechavel else "Em aberto"
    ncols = 5 if usa_valor else 4
    cs = st.columns(ncols)
    cs[0].metric("Enviado no mês", _fmt(df_view["enviado"].sum()))
    cs[1].metric("Devolvido", _fmt(df_view["devolvido"].sum()))
    cs[2].metric("Já cobrado", _fmt(df_view["cobrado"].sum()))
    cs[3].metric(rot_cobravel, _fmt(df_view["cobravel"].sum()))
    if usa_valor:
        valor_cobravel = sum(int(r["cobravel"]) * pr.get(r["tipo"], 0) for _, r in df_view.iterrows())
        cs[4].metric(f"Valor {rot_cobravel.lower()}", dp.fmt_brl(valor_cobravel))

    st.markdown("---")

    # ---- Fechar cobrança (baixa definitiva) ----
    with st.container(border=True):
        st.markdown("#### Fechar cobrança da competência")
        # IMPORTANTE: usa o df completo, sem o filtro de operação.
        total_cobravel = int(df["cobravel"].sum())
        if dados.competencia_ja_fechada(mes):
            st.success(f"A competência **{escolha}** já foi fechada. Os itens cobrados foram baixados (não são recobrados nem aceitam devolução).")
        elif not fechavel:
            st.info(f"Ainda dentro do prazo de devolução (até {prazo_txt}). O fechamento fica disponível a partir do dia 6.")
        elif total_cobravel == 0:
            st.caption("Nenhum item cobrável nesta competência. Nada a fechar.")
        else:
            total_valor = sum(int(r["cobravel"]) * pr.get(r["tipo"], 0) for _, r in df.iterrows()) if usa_valor else 0
            aviso_valor = f" ({dp.fmt_brl(total_valor)})" if usa_valor else ""
            st.markdown(
                f'<div class="concil-info-blue">'
                f'Ao fechar, <strong>{_fmt(total_cobravel)}</strong> itens não devolvidos até '
                f'<strong>{prazo_txt}</strong> serão registrados como cobrados e recebem '
                f'<strong>baixa definitiva</strong> — saem do saldo e não aceitam mais devolução.'
                f'<strong>{aviso_valor}</strong></div>',
                unsafe_allow_html=True,
            )
            confirma = st.checkbox("Confirmo o fechamento desta competência (ação irreversível).")
            if st.button("💰 Registrar cobrança e dar baixa", type="primary", disabled=not confirma):
                agora = datetime.now(dp.TZ).strftime("%Y-%m-%d %H:%M:%S")
                quem = (st.session_state.get("usuario") or {}).get("nome", "admin")
                cobraveis = df[df["cobravel"] > 0]
                rows = [
                    {
                        "id": f"COB-{mes}-{i:03d}", "data": agora, "competencia": mes,
                        "destino": r["destino"], "tipo": r["tipo"], "qtd": int(r["cobravel"]),
                        "prazo_dias": prazo_txt, "gerado_por": quem,
                    }
                    for i, (_, r) in enumerate(cobraveis.iterrows(), start=1)
                ]
                dados.registrar_cobrancas(rows)
                st.success(f"Cobrança da competência {escolha} registrada. Itens baixados.")
                st.rerun()

    st.markdown("---")

    # ---- Gráficos ----
    g1, g2 = st.columns([1, 1.3])
    with g1:
        # Quantidade cobrável + valor financeiro aparente por tipo.
        tdf = df_view.groupby("tipo", as_index=False)["cobravel"].sum()
        tdf["valor_cobravel"] = tdf.apply(
            lambda r: int(r["cobravel"]) * pr.get(r["tipo"], 0), axis=1
        )
        # Ordena e dimensiona as barras pelo valor financeiro, não pela quantidade.
        tdf = tdf.sort_values("valor_cobravel", ascending=False, kind="stable")
        tdf["valor_label"] = tdf["valor_cobravel"].map(
            lambda v: f"<b>{dp.fmt_brl(v)}</b>"
        )

        st.markdown(
            "<div style='text-align:center;font-weight:750;color:#102B50;"
            "font-size:16px;margin:0 0 10px 0;'>Cobrável por tipo</div>",
            unsafe_allow_html=True,
        )
        fig = px.bar(
            tdf,
            x="tipo",
            y="valor_cobravel",
            color="tipo",
            category_orders={"tipo": tdf["tipo"].tolist()},
            color_discrete_map={
                "GAYLORD": "#00AEEF",
                "PALLET": "#1685F8",
                "SACA": "#0067FC",
            },
            labels={"tipo": "Tipo", "cobravel": "Cobrável"},
            custom_data=["valor_cobravel"],
        )
        # Como o gráfico tem uma série por tipo, cada trace recebe somente
        # o valor financeiro do seu próprio tipo.
        for trace in fig.data:
            tipo_trace = str(trace.name).strip().upper()
            linha = tdf[tdf["tipo"].astype(str).str.upper() == tipo_trace]
            if not linha.empty:
                valor = float(linha.iloc[0]["valor_cobravel"])
                qtd = int(linha.iloc[0]["cobravel"])
                trace.text = [f"<b>{dp.fmt_brl(valor)}</b>"]
                trace.customdata = [[valor]]
                trace.hovertemplate = (
                    f"<b>{tipo_trace}</b><br>"
                    f"Cobrável: {qtd:,.0f}<br>"
                    "Valor da cobrança: R$ %{customdata[0]:,.2f}"
                    "<extra></extra>"
                )
                trace.textposition = "outside"
                trace.textfont = dict(size=13, family="Montserrat", color="#526783")
                trace.text = [f"<b>{dp.fmt_brl(valor)}</b>"]
        fig.update_layout(
            showlegend=False,
            height=330,
            font_family="Montserrat",
            bargap=0.34,
            margin=dict(l=12, r=28, t=12, b=42),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        # Mantém os nomes das categorias e os rótulos de valor,
        # removendo eixos numéricos, linhas e grades.
        fig.update_xaxes(
            title_text="", showgrid=False, showline=False,
            ticks="", showticklabels=True, zeroline=False,
            tickfont=dict(family="Montserrat", size=12, color="#526783"),
        )
        fig.update_yaxes(
            title_text="", showgrid=False, showline=False,
            ticks="", showticklabels=False, zeroline=False,
        )
        st.plotly_chart(fig, width="stretch")

    with g2:
        titulo_rank = (
            f"Cobrável por operação — {op_escolhida}" if op_escolhida != "Todas as operações"
            else "Cobrável por operação (top 5)"
        )
        st.markdown(
            f"<div style='text-align:center;font-weight:750;color:#102B50;"
            f"font-size:16px;margin:0 0 10px 0;'>{titulo_rank}</div>",
            unsafe_allow_html=True,
        )
        rank = (
            df_view.groupby("destino", as_index=False)["cobravel"].sum()
            .query("cobravel > 0")
            .sort_values("cobravel", ascending=False)
            .head(5)
        )
        if rank.empty:
            st.caption("Nenhum item cobrável no período. 🎉")
        else:
            # Valor total da operação: soma de cada tipo cobrável × seu preço.
            valores_por_operacao = (
                df_view.assign(
                    valor_cobravel=df_view.apply(
                        lambda r: int(r["cobravel"]) * pr.get(r["tipo"], 0),
                        axis=1
                    )
                )
                .groupby("destino", as_index=False)["valor_cobravel"]
                .sum()
            )
            rank = rank.merge(
                valores_por_operacao, on="destino", how="left"
            )
            # O Top 5 também passa a ser ordenado e dimensionado pelo valor em R$.
            rank = rank.sort_values("valor_cobravel", ascending=True, kind="stable")
            rank["valor_label"] = rank["valor_cobravel"].map(
                lambda v: f"<b>{dp.fmt_brl(v)}</b>"
            )

            figd = px.bar(
                rank,
                x="valor_cobravel",
                y="destino",
                orientation="h",
                labels={"cobravel": "Cobrável", "destino": "Operação"},
                custom_data=["cobravel"],
            )
            figd.update_traces(
                marker_color=["#003DA5" if i == 0 else "#0067FC" for i in range(len(rank))],
                text=rank["valor_label"],
                textposition="outside",
                textfont=dict(size=12, family="Montserrat", color="#526783"),
                cliponaxis=False,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Valor cobrável: R$ %{x:,.2f}<br>"
                    "Itens cobráveis: %{customdata[0]:,.0f}"
                    "<extra></extra>"
                ),
            )
            figd.update_layout(
                height=330,
                font_family="Montserrat",
                bargap=0.24,
                margin=dict(l=18, r=210, t=12, b=22),
                uniformtext_minsize=10,
                uniformtext_mode="show",
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            # Mantém as operações e os rótulos financeiros; remove eixo numérico e grades.
            figd.update_xaxes(
                title_text="", showgrid=False, showline=False,
                ticks="", showticklabels=False, zeroline=False,
                range=[0, float(rank["valor_cobravel"].max()) * 1.32],
            )
            figd.update_yaxes(
                title_text="", showgrid=False, showline=False,
                ticks="", showticklabels=True, zeroline=False,
                tickfont=dict(family="Montserrat", size=12, color="#526783"),
            )
            st.plotly_chart(figd, width="stretch")

    # ---- Tabela detalhada (destino × tipo) ----
    st.markdown("<div class=\"concil-section-title\"><span class=\"ico\">▦</span> Detalhamento por operação × tipo</div>", unsafe_allow_html=True)
    so_cobravel = st.checkbox("Mostrar apenas com cobrável > 0", value=False)
    tab = df_view.copy()
    if so_cobravel:
        tab = tab[tab["cobravel"] > 0]

    if usa_valor:
        tab["Valor unitário"] = tab["tipo"].map(pr).fillna(0.0)
        tab["Valor cobrável"] = tab["cobravel"].astype(int) * tab["Valor unitário"]

    tab_disp = tab.drop(columns=["em_aberto"]).rename(columns={
        "destino": "Operação", "tipo": "Tipo", "enviado": "Enviado",
        "devolvido": "Devolvido", "cobrado": "Já cobrado", "cobravel": "Cobrável",
    })
    if usa_valor:
        tab_disp["Valor unitário"] = tab_disp["Valor unitário"].map(dp.fmt_brl)
        tab_disp["Valor cobrável"] = tab_disp["Valor cobrável"].map(dp.fmt_brl)

    tabela_html = tab_disp.to_html(index=False, escape=True, border=0, classes="concil-html-table")
    st.markdown(
        f'<div class="concil-html-table-wrap">{tabela_html}</div>',
        unsafe_allow_html=True,
    )

    # ---- Resumo por operação ----
    st.markdown("<div class=\"concil-section-title\"><span class=\"ico\">▤</span> Resumo por operação (cobrável por tipo)</div>", unsafe_allow_html=True)
    piv = tab.pivot_table(index="destino", columns="tipo", values="cobravel", aggfunc="sum", fill_value=0)
    piv["TOTAL"] = piv.sum(axis=1)
    if usa_valor:
        valores_op = tab.groupby("destino")["Valor cobrável"].sum()
        piv["VALOR TOTAL"] = valores_op
    piv = piv[piv["TOTAL"] > 0].sort_values("TOTAL", ascending=False)

    # Inicializa a tabela mesmo quando não houver operações cobráveis.
    # A exportação Excel usa piv_disp independentemente de a tabela estar vazia.
    piv_disp = piv.copy()
    if piv.empty:
        st.caption("Nenhuma operação com itens cobráveis no período.")
    else:
        if usa_valor:
            piv_disp["VALOR TOTAL"] = piv_disp["VALOR TOTAL"].map(dp.fmt_brl)

        # Prepara a visualização sem índice hierárquico, evitando cabeçalhos duplicados.
        piv_visual = piv_disp.reset_index()
        piv_visual.columns = [
            "Destino" if str(col).strip().lower() == "destino"
            else str(col).strip().title()
            for col in piv_visual.columns
        ]
        piv_html = piv_visual.to_html(
            index=False, escape=True, border=0, classes="concil-html-table concil-resumo-table"
        )
        st.markdown(
            f'<div class="concil-html-table-wrap concil-resumo-table-wrap">{piv_html}</div>',
            unsafe_allow_html=True,
        )

    # ---- Exportação Excel ----
    sufixo = mes or "ate_hoje"
    excel_buffer = io.BytesIO()
    with __import__("pandas").ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        tab_disp.to_excel(writer, index=False, sheet_name="Conciliação")
        piv_disp.to_excel(writer, sheet_name="Resumo por operação")
    excel_buffer.seek(0)

    st.download_button(
        "Baixar conciliação (Excel)",
        excel_buffer.getvalue(),
        file_name=f"conciliacao_{sufixo}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="dl_concil",
    )

    # ---- Enviar e-mail de saldo pendente da competência ----
    st.markdown("---")
    st.markdown("<div class=\"concil-section-title\"><span class=\"ico\">✉</span> Enviar saldo pendente por e-mail</div>", unsafe_allow_html=True)
    st.caption(f"O e-mail considera somente os itens ainda pendentes da competência {escolha}; não envia notas de débito da aba Cobrancas.")

    pend_email = df.copy()
    pend_email = pend_email[pend_email["cobravel"] > 0].copy()
    if pend_email.empty:
        st.info(f"Não há saldo pendente para enviar por e-mail na competência {escolha}.")
        return

    grupos_email = []
    for destino_email, grupo_email in pend_email.groupby("destino"):
        itens_email = [
            {
                "tipo": linha["tipo"],
                "enviado": int(linha["enviado"]),
                "devolvido": int(linha["devolvido"]),
                "pendente": int(linha["cobravel"]),
            }
            for _, linha in grupo_email.iterrows()
        ]
        emails = dp.emails_por_destino(destino_email)
        grupos_email.append({
            "destino": str(destino_email),
            "itens": itens_email,
            "total": int(grupo_email["cobravel"].sum()),
            "emails": emails,
        })

    pr_email = dp.precos()
    resumo_email = []
    for grupo in grupos_email:
        linha = {
            "Operação": grupo["destino"],
            "Saldo pendente": _fmt(grupo["total"]),
            "E-mail(s)": ", ".join(grupo["emails"]) if grupo["emails"] else "Sem e-mail cadastrado",
        }
        if usa_valor:
            linha["Valor pendente"] = dp.fmt_brl(
                sum(item["pendente"] * pr_email.get(item["tipo"], 0) for item in grupo["itens"])
            )
        resumo_email.append(linha)
    resumo_email_df = pd.DataFrame(resumo_email)
    resumo_email_html = resumo_email_df.to_html(
        index=False, escape=True, border=0, classes="concil-html-table concil-email-table"
    )
    st.markdown(
        f'<div class="concil-html-table-wrap concil-email-table-wrap">{resumo_email_html}</div>',
        unsafe_allow_html=True,
    )

    sem_email = [grupo["destino"] for grupo in grupos_email if not grupo["emails"]]
    if sem_email:
        st.markdown(
            '<div class="concil-info-blue">'
            '<strong>Não há e-mail cadastrado para:</strong> '
            + ", ".join(sem_email)
            + '</div>',
            unsafe_allow_html=True,
        )

    if not emailer.smtp_configurado():
        st.warning("Configure o servidor SMTP em Configurações para enviar os saldos pendentes.")
        return

    opcoes_email = {
        f"{grupo['destino']} · {_fmt(grupo['total'])} pendentes": grupo
        for grupo in grupos_email if grupo["emails"]
    }
    if opcoes_email:
        col_a, col_b = st.columns([2, 1])
        escolha_email = col_a.selectbox(
            "Enviar para uma operação",
            ["—"] + list(opcoes_email.keys()),
            key="saldo_pendente_destino_email",
        )
        if col_b.button("Enviar e-mail", width="stretch", key="btn_enviar_saldo_pendente_unico") and escolha_email != "—":
            grupo = opcoes_email[escolha_email]
            ok, msg = emailer.enviar_pendencia(
                grupo["emails"][0], grupo["destino"], grupo["itens"], grupo["total"],
                precos=pr_email, competencia_label=escolha,
                destinatarios_adicionais=grupo["emails"][1:],
            )
            if ok:
                st.success(f"E-mail de saldo pendente enviado para {grupo['destino']}.")
            else:
                st.error(msg)

    if st.button(
        f"✉️ Enviar saldo pendente de {escolha} para todas as operações com e-mail",
        type="primary",
        key="btn_enviar_saldo_pendente_todas",
    ):
        enviados, falhas = 0, []
        for grupo in grupos_email:
            if not grupo["emails"]:
                continue
            ok, msg = emailer.enviar_pendencia(
                grupo["emails"][0], grupo["destino"], grupo["itens"], grupo["total"],
                precos=pr_email, competencia_label=escolha,
                destinatarios_adicionais=grupo["emails"][1:],
            )
            if ok:
                enviados += 1
            else:
                falhas.append(f"{grupo['destino']}: {msg}")
        if enviados:
            st.success(f"{enviados} e-mail(s) de saldo pendente enviados para {escolha}.")
        for falha in falhas:
            st.error(falha)
        if enviados == 0 and not falhas:
            st.info("Nenhuma operação com e-mail cadastrado para envio.")


def _emails_do_destino(destino: str) -> list[str]:
    alvo = dp._normalizar(destino)
    return [u["email"] for u in dados.ler_usuarios()
            if u.get("email") and u.get("ativo") and dp._normalizar(u["destino"]) == alvo]


def _enviar_cobrancas_email(cobs_mes, competencia_label: str, prazo_txt: str):
    grupos = []
    for destino, g in cobs_mes.groupby("destino"):
        itens = [{"tipo": r["tipo"], "qtd": int(r["qtd"])} for _, r in g.iterrows()]
        total = int(g["qtd"].sum())
        emails = _emails_do_destino(destino)
        grupos.append({"destino": destino, "itens": itens, "total": total, "emails": emails})

    pr = dp.precos()
    usa_valor = dp.tem_precos()
    resumo = []
    for x in grupos:
        linha = {"Operação": x["destino"], "Total cobrado": x["total"]}
        if usa_valor:
            linha["Valor"] = dp.fmt_brl(sum(it["qtd"] * pr.get(it["tipo"], 0) for it in x["itens"]))
        linha["E-mail(s)"] = ", ".join(x["emails"]) or "— sem e-mail —"
        resumo.append(linha)
    resumo_df = __import__("pandas").DataFrame(resumo)
    st.dataframe(
        resumo_df,
        width="stretch",
        hide_index=True,
        column_config=_centralizar_tabela(resumo_df),
    )

    sem_email = [x["destino"] for x in grupos if not x["emails"]]
    if sem_email:
        st.caption("Sem e-mail cadastrado (não serão notificadas): " + ", ".join(sem_email))

    if st.button("✉️ Enviar e-mails de cobrança", type="primary", key="btn_enviar_cobrancas"):
        with st.spinner("Enviando e-mails..."):
            resultados = []
            for x in grupos:
                if not x["emails"]:
                    resultados.append((x["destino"], False, "sem e-mail"))
                    continue
                ok = emailer.enviar_cobranca(
                    x["emails"], competencia_label, prazo_txt, x["itens"],
                    total=x["total"], valor=(
                        sum(it["qtd"] * pr.get(it["tipo"], 0) for it in x["itens"])
                        if usa_valor else None
                    ),
                )
                resultados.append((x["destino"], ok, "enviado" if ok else "falha"))
            for destino, ok, msg in resultados:
                if ok:
                    st.success(f"{destino}: e-mail enviado.")
                else:
                    st.error(f"{destino}: {msg}.")
