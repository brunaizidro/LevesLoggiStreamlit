"""
page_4.py — Recebimento de devoluções.
Interface alinhada visualmente ao módulo Envios, preservando o fluxo de conferência.
"""
from __future__ import annotations

from datetime import datetime
import html

import plotly.express as px
import streamlit as st

import data_extraction as dados
import data_processing as dp


def _fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def _injetar_css():
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
html, body, [data-testid="stApp"], [data-testid="stApp"] *,
[data-testid="stDataFrame"], [data-testid="stDataFrame"] * {
    font-family: 'Montserrat', sans-serif !important;
}
[data-testid="stHeader"], [data-testid="stToolbar"] { display:none !important; }
[data-testid="stAppViewContainer"], [data-testid="stMain"] { background:#FFFFFF !important; }
[data-testid="stAppViewBlockContainer"] {
    max-width:100% !important;
    padding:18px clamp(22px,3.2vw,54px) 38px !important;
}
.rec-breadcrumb {
    color:#7B8798; font-size:11px; font-weight:700;
    letter-spacing:.55px; margin:0 0 7px;
}
.rec-title {
    color:#172B4D; font-size:clamp(28px,2.3vw,34px);
    line-height:1.18; font-weight:800; letter-spacing:-.8px; margin:0;
}
.rec-description { color:#7A8493; font-size:14px; line-height:1.55; margin:6px 0 18px; }
.rec-section-title {
    color:#172B4D; font-size:16px; font-weight:800;
    margin:18px 0 10px;
}
.rec-section-title .accent { color:#0067FC; }
.rec-card-title { color:#172B4D; font-size:16px; font-weight:800; margin:0 0 12px; }
.rec-filter-card {
    background:#FFFFFF; border:1px solid #DCE7F6; border-radius:14px;
    padding:14px 16px; box-shadow:0 4px 14px rgba(16,43,80,.045);
}
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label {
    color:#172B4D !important; font-size:13px !important; font-weight:700 !important;
}
[data-baseweb="select"] > div,
[data-testid="stNumberInput"] input {
    background:#F0F2F6 !important; border:1px solid #E7EAF0 !important;
    border-radius:10px !important; box-shadow:none !important;
}
[data-baseweb="select"] > div:focus-within {
    border-color:#0067FC !important; box-shadow:0 0 0 2px rgba(0,103,252,.10) !important;
}
.rec-kpi {
    background:#FFFFFF; border:1px solid #DCE7F6; border-radius:14px;
    padding:16px 18px; min-height:108px; box-sizing:border-box;
    box-shadow:0 4px 14px rgba(16,43,80,.045);
}
.rec-kpi-total {
    background:#0067FC; border-color:#0067FC;
    box-shadow:0 6px 18px rgba(0,103,252,.16);
}
.rec-kpi-label {
    color:#526783; font-size:11px; font-weight:800;
    letter-spacing:.35px; text-transform:uppercase;
}
.rec-kpi-value {
    color:#172B4D; font-size:30px; line-height:1.1;
    font-weight:800; margin-top:9px;
}
.rec-kpi-sub { color:#7B8798; font-size:11px; margin-top:4px; }
.rec-kpi-total .rec-kpi-label,
.rec-kpi-total .rec-kpi-value,
.rec-kpi-total .rec-kpi-sub { color:#FFFFFF; }
.rec-panel {
    background:#FFFFFF; border:1px solid #DCE7F6; border-radius:14px;
    padding:16px 18px; box-shadow:0 4px 14px rgba(16,43,80,.035);
}
.rec-meta-grid {
    display:grid; grid-template-columns:repeat(4,minmax(0,1fr));
    gap:12px; margin:0;
}
.rec-meta-item {
    padding:10px 12px; background:#F7FAFF; border-radius:9px;
    min-width:0;
}
.rec-meta-label {
    display:block; color:#71819A; font-size:10px; font-weight:800;
    letter-spacing:.4px; text-transform:uppercase; margin-bottom:5px;
}
.rec-meta-value {
    color:#172B4D; font-size:13px; font-weight:700;
    overflow-wrap:anywhere;
}
.rec-html-table-wrap {
    overflow:auto; border:1px solid #DCE7F6; border-radius:10px; background:#FFFFFF;
}
.rec-html-table {
    width:100%; border-collapse:separate; border-spacing:0;
    font-family:'Montserrat',sans-serif !important; font-size:13px; color:#172B4D;
}
.rec-html-table th {
    background:#0067FC !important; color:#FFFFFF !important;
    font-weight:700; text-align:left; padding:11px 12px; white-space:nowrap;
}
.rec-html-table td {
    background:#FFFFFF; color:#172B4D; font-weight:500;
    padding:10px 12px; border-bottom:1px solid #E8EEF7;
}
.rec-html-table tbody tr:nth-child(even) td { background:#F7FAFF; }
.rec-html-table .total-row td { background:#EAF3FF !important; font-weight:800; }
[data-testid="stAppViewContainer"] .stButton > button,
[data-testid="stFormSubmitButton"] button {
    min-height:40px !important; border-radius:9px !important;
    font-family:'Montserrat',sans-serif !important; font-weight:700 !important;
    background:#0067FC !important; border:1px solid #0067FC !important; color:#FFFFFF !important;
}
[data-testid="stAppViewContainer"] .stButton > button:hover,
[data-testid="stFormSubmitButton"] button:hover {
    background:#0058DC !important; border-color:#0058DC !important;
}
[data-testid="stAlert"] { border-radius:10px !important; }
[data-testid="stForm"] {
    border:1px solid #DCE7F6 !important; border-radius:12px !important;
    padding:14px !important; background:#FFFFFF !important;
}
.js-plotly-plot, .js-plotly-plot text { font-family:'Montserrat',sans-serif !important; }
@media(max-width:900px) {
    [data-testid="stAppViewBlockContainer"] { padding:16px 14px 28px !important; }
    .rec-meta-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
    .rec-kpi-value { font-size:26px; }
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _confirmar(dev: dict, itens: list[dict], recebidos: dict | None, quem: str):
    """Grava o recebimento.

    No "Confirmar sem contar", a quantidade recebida é exatamente a quantidade
    declarada. No "Contar e confirmar", a quantidade recebida é a informada
    pelo time de recebimento.
    """
    agora = datetime.now(dp.TZ).strftime("%Y-%m-%d %H:%M:%S")
    sem_contar = recebidos is None

    if sem_contar:
        # Aceita integralmente o que foi declarado pela operação.
        recebidos = {
            it["tipo"]: int(it["qtd_declarada"])
            for it in itens
        }
        divergente = False
    else:
        # Regra de negócio: não é permitido confirmar recebimento acima da quantidade declarada.
        # Validação no backend protege também contra valores enviados fora do formulário.
        for it in itens:
            tipo = it["tipo"]
            qtd = int(recebidos.get(tipo, 0))
            declarada = int(it["qtd_declarada"])
            if qtd < 0 or qtd > declarada:
                raise ValueError(
                    f"Quantidade recebida de {tipo} deve ficar entre 0 e {declarada}."
                )

        divergente = any(
            int(recebidos.get(it["tipo"], 0)) != int(it["qtd_declarada"])
            for it in itens
        )

    total_receb = sum(int(v) for v in recebidos.values())
    status = dp.STATUS_DIVERGENTE if divergente else dp.STATUS_CONFERIDO

    dados.atualizar_itens_recebidos(dev["id"], recebidos)
    dados.atualizar_devolucao(
        dev["id"],
        {
            "status": status,
            "total_recebido": total_receb,
            "data_recebimento": agora,
            "recebido_por": quem,
        },
    )
    return status



def _card_devolucao(dev: dict, quem: str):
    itens_df = dp.itens_da_devolucao(dev["id"])
    itens = [
        {"tipo": str(r["tipo"]), "qtd_declarada": int(r["qtd_declarada"])}
        for _, r in itens_df.iterrows()
    ]
    total = sum(i["qtd_declarada"] for i in itens)
    tipos_ordem = ["GAYLORD", "PALLET", "SACA"]
    totais = {i["tipo"].upper(): i["qtd_declarada"] for i in itens}
    totais_lista = [(t, totais.get(t, 0)) for t in tipos_ordem if totais.get(t, 0)]
    totais_lista += [(t, q) for t, q in totais.items() if t not in tipos_ordem and q]

    st.markdown(
        '<div class="rec-section-title"><span class="accent">▦</span> &nbsp; Resumo da devolução</div>',
        unsafe_allow_html=True,
    )
    kpis = [("Total declarado", total, "itens")] + [
        (t.title(), q, "itens") for t, q in totais_lista
    ]
    cols = st.columns(len(kpis))
    for idx, (col, (label, value, sub)) in enumerate(zip(cols, kpis)):
        with col:
            cls = "rec-kpi rec-kpi-total" if idx == 0 else "rec-kpi"
            st.markdown(
                f'<div class="{cls}"><div class="rec-kpi-label">{html.escape(label)}</div>'
                f'<div class="rec-kpi-value">{_fmt(value)}</div>'
                f'<div class="rec-kpi-sub">{sub}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
    left, right = st.columns([0.88, 1.12], gap="large")
    graf_df = [
        {"tipo": t, "quantidade": q}
        for t, q in totais_lista if q > 0
    ]
    paleta = {"SACA": "#0866F5", "GAYLORD": "#16B9ED", "PALLET": "#8DD8FA"}
    for t, _ in totais_lista:
        paleta.setdefault(t, "#6D9FE8")

    with left:
        with st.container(border=True):
            st.markdown('<div class="rec-card-title">Distribuição por tipo de insumo</div>', unsafe_allow_html=True)
            if graf_df:
                fig = px.pie(
                    graf_df, names="tipo", values="quantidade", hole=.66,
                    color="tipo", color_discrete_map=paleta,
                )
                fig.update_traces(
                    texttemplate="%{percent:.1%}", textposition="inside",
                    textfont=dict(family="Montserrat", size=12, color="#FFFFFF"),
                    sort=False,
                )
                fig.update_layout(
                    height=270, showlegend=True,
                    font=dict(family="Montserrat", color="#243B5B", size=11),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=8, r=8, t=8, b=8),
                    legend=dict(orientation="v", y=.5, yanchor="middle", x=.78, xanchor="left"),
                    annotations=[dict(
                        text=f"<b>{_fmt(total)}</b><br><span style='font-size:11px'>itens</span>",
                        x=.38, y=.5, xref="paper", yref="paper",
                        xanchor="center", yanchor="middle", align="center",
                        showarrow=False, font=dict(family="Montserrat", size=19, color="#102B50"),
                    )],
                )
                st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
            else:
                st.info("Não há itens declarados para exibir.")

    with right:
        with st.container(border=True):
            st.markdown('<div class="rec-card-title">Detalhes da devolução</div>', unsafe_allow_html=True)
            comp = str(dev.get("competencia", "") or "")
            comp_txt = dp.rotulo_mes(comp) if len(comp) == 7 else "—"
            meta = [
                ("Código da devolução", dev.get("id", "—")),
                ("Operação", dev.get("usuario", "—")),
                ("Destino", dev.get("destino", "—")),
                ("Placa", dev.get("placa") or "—"),
                ("Emissão", dev.get("data_criacao", "—")),
                ("Competência", comp_txt),
            ]
            if dev.get("local_devolucao"):
                meta.append(("Devolvendo para", dev.get("local_devolucao")))
            st.markdown(
                '<div class="rec-meta-grid">' + "".join(
                    '<div class="rec-meta-item">'
                    f'<span class="rec-meta-label">{html.escape(str(label))}</span>'
                    f'<span class="rec-meta-value">{html.escape(str(value))}</span>'
                    '</div>'
                    for label, value in meta
                ) + '</div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="rec-card-title">Itens declarados</div>', unsafe_allow_html=True)
        linhas = "".join(
            f'<tr><td>{html.escape(str(it["tipo"]).title())}</td>'
            f'<td style="text-align:center">{_fmt(it["qtd_declarada"])}</td></tr>'
            for it in itens
        )
        tabela = (
            '<div class="rec-html-table-wrap"><table class="rec-html-table">'
            '<thead><tr><th>Tipo de insumo</th><th style="text-align:center">Quantidade</th></tr></thead>'
            f'<tbody>{linhas}<tr class="total-row"><td>Total declarado</td>'
            f'<td style="text-align:center">{_fmt(total)}</td></tr></tbody></table></div>'
        )
        st.markdown(tabela, unsafe_allow_html=True)

    # Já processada?
    if dev.get("status") != dp.STATUS_TRANSITO:
        st.warning(
            f"Esta devolução já está **{dp.STATUS_LABEL.get(dev['status'], dev['status'])}**"
            + (f" — recebida em {dev.get('data_recebimento','')} por {dev.get('recebido_por','')}."
               if dev.get("recebido_por") else ".")
        )
        exibicao = itens_df.rename(columns={
            "tipo": "Tipo", "qtd_declarada": "Declarado", "qtd_recebida": "Recebido"
        })
        colunas = [c for c in ["Tipo", "Declarado", "Recebido"] if c in exibicao.columns]
        st.dataframe(exibicao[colunas], width="stretch", hide_index=True)
        return

    st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2, gap="large")
    with col_a:
        with st.container(border=True):
            st.markdown('<div class="rec-card-title">Aceitar o declarado</div>', unsafe_allow_html=True)
            st.caption("Confirme as quantidades informadas no romaneio sem realizar nova contagem.")
            if st.button("✅ Confirmar sem contar", type="primary", key=f"semcontar_{dev['id']}"):
                _confirmar(dev, itens, None, quem)
                st.success("Recebimento confirmado (declarado aceito).")
                st.rerun()

    with col_b:
        with st.container(border=True):
            st.markdown('<div class="rec-card-title">Contar e confirmar</div>', unsafe_allow_html=True)
            st.caption("Informe a quantidade física recebida de cada tipo de insumo.")
            with st.form(f"contar_{dev['id']}"):
                recebidos = {}
                for it in itens:
                    recebidos[it["tipo"]] = st.number_input(
                        f"{it['tipo'].title()} recebido",
                        min_value=0,
                        max_value=int(it["qtd_declarada"]),
                        step=1,
                        value=int(it["qtd_declarada"]),
                        help="A quantidade recebida não pode ultrapassar a quantidade declarada no romaneio.",
                    )
                ok = st.form_submit_button("Registrar contagem")
            if ok:
                try:
                    status = _confirmar(dev, itens, recebidos, quem)
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    if status == dp.STATUS_DIVERGENTE:
                        st.warning("Recebido com **divergência** entre declarado e contado.")
                    else:
                        st.success("Recebimento **conferido** — quantidades batem.")
                    st.rerun()


def page_4(scan_id: str | None = None, scan_token: str | None = None):
    _injetar_css()
    user = st.session_state.get("usuario") or {}
    quem = user.get("nome", user.get("usuario", ""))

    st.markdown('<div class="rec-breadcrumb">PORTAL LEVES &nbsp;/&nbsp; RECEBIMENTO</div>', unsafe_allow_html=True)
    st.markdown('<div class="rec-title">Recebimento de devoluções</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="rec-description">Aponte a câmera no QR do romaneio ou selecione uma devolução em trânsito abaixo.</div>',
        unsafe_allow_html=True,
    )

    devs = dp.devolucoes_df()

    if scan_id:
        if devs.empty:
            st.error("Devolução não encontrada.")
            return
        achou = devs[devs["id"] == scan_id]
        if achou.empty:
            st.error(f"Devolução {scan_id} não encontrada.")
        else:
            dev = achou.iloc[0].to_dict()
            if scan_token and str(dev.get("token", "")) != scan_token:
                st.error("Token inválido para esta devolução. Verifique o QR.")
            else:
                _card_devolucao(dev, quem)
        if st.button("← Voltar à lista"):
            st.query_params.clear()
            st.rerun()
        return

    if devs.empty:
        st.info("Nenhuma devolução registrada.")
        return

    pendentes = devs[devs["status"] == dp.STATUS_TRANSITO].sort_values("dt_criacao")
    if pendentes.empty:
        st.success("Nenhuma devolução em trânsito no momento.")
        return

    opcoes = {
        f"{r['id']} — {r['usuario']} ({r['destino']}) · {_fmt(r['total_declarado'])} itens": r["id"]
        for _, r in pendentes.iterrows()
    }
    with st.container(border=True):
        st.markdown('<div class="rec-card-title"><span style="color:#0067FC">⚙</span> Filtros</div>', unsafe_allow_html=True)
        escolha = st.selectbox("Devoluções em trânsito", list(opcoes.keys()), key="seletor_devolucao_transito")

    if escolha:
        dev = devs[devs["id"] == opcoes[escolha]].iloc[0].to_dict()
        _card_devolucao(dev, quem)
