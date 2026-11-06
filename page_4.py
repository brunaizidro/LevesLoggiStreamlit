"""
page_4.py — Recebimento (valida devoluções).

Abre automaticamente uma devolução quando acessada pelo QR (id + token na URL),
verificando o token. Caso contrário, lista as devoluções em trânsito para
seleção manual. A conferência/contagem é decisão do time de recebimento:
"Confirmar sem contar" (aceita o declarado) ou "Contar e confirmar" (registra o
que chegou e marca divergência se diferir).
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st

import data_extraction as dados
import data_processing as dp


def _fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def _injetar_css():
    st.markdown(
        """
<style>
/* Identidade visual replicada do módulo Envios — sem alterar conteúdo ou fluxo */
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
html, body, [data-testid="stApp"], [data-testid="stApp"] *,
[data-testid="stDataFrame"], [data-testid="stDataFrame"] * {
    font-family:'Montserrat',sans-serif !important;
}
[data-testid="stHeader"], [data-testid="stToolbar"] { display:none !important; }
[data-testid="stAppViewContainer"], [data-testid="stMain"] { background:#FFFFFF !important; }
[data-testid="stAppViewBlockContainer"] {
    max-width:100% !important;
    padding:18px clamp(22px,3.2vw,54px) 38px !important;
}
.rec-breadcrumb {
    color:#7B8798 !important; font-size:11px !important;
    font-weight:600 !important; letter-spacing:.55px !important; margin:0 0 7px !important;
}
.rec-page-title {
    color:#172B4D !important; font-size:clamp(28px,2.3vw,34px) !important;
    line-height:1.18 !important; font-weight:800 !important;
    letter-spacing:-.8px !important; margin:0 !important;
}
.rec-page-description {
    color:#7A8493 !important; font-size:14px !important;
    line-height:1.55 !important; margin:6px 0 18px !important;
}
h1,h2,h3,h4,[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,[data-testid="stMarkdownContainer"] h3 {
    color:#172B4D !important; font-family:'Montserrat',sans-serif !important;
    font-weight:800 !important;
}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stCaptionContainer"] {
    color:#253B59; font-family:'Montserrat',sans-serif !important;
}
[data-testid="stWidgetLabel"] p,[data-testid="stWidgetLabel"] label {
    color:#172B4D !important; font-size:13px !important; font-weight:700 !important;
}
[data-baseweb="select"] > div,[data-testid="stNumberInput"] input {
    background:#F0F2F6 !important; border:1px solid #E7EAF0 !important;
    border-radius:10px !important; min-height:42px !important; box-shadow:none !important;
}
[data-baseweb="select"] > div:focus-within,
[data-testid="stNumberInput"] input:focus {
    border-color:#0067FC !important; box-shadow:0 0 0 2px rgba(0,103,252,.10) !important;
}
[data-baseweb="tag"] { background:#0067FC !important; border-radius:6px !important; }
[data-baseweb="tag"] *,[data-baseweb="tag"] span { color:#FFFFFF !important; }
.st-key-rec_filters {
    background:#FFFFFF !important; border:1px solid #DCE7F6 !important;
    border-radius:14px !important; padding:14px 16px !important;
    box-shadow:0 4px 14px rgba(16,43,80,.045) !important;
}
.st-key-rec_filters [data-testid="stVerticalBlockBorderWrapper"] {
    border:0 !important; box-shadow:none !important;
}
.rec-filter-heading,.rec-section-heading {
    color:#172B4D !important; font-size:17px !important;
    font-weight:800 !important; margin:0 0 10px !important;
}
.rec-filter-heading span,.rec-section-heading span { color:#0067FC !important; }
.rec-meta-row {
    display:grid; grid-template-columns:1.4fr 1fr 1fr 1.2fr;
    gap:18px; align-items:start; margin:14px 0 8px;
}
.rec-meta-item { color:#172B4D; font-size:14px; font-weight:700; line-height:1.55; }
.rec-meta-item strong { color:#172B4D; font-weight:800; }
.rec-competencia {
    color:#172B4D; font-size:14px; font-weight:700; margin:10px 0 18px;
}
.rec-items-heading {
    color:#172B4D !important; font-size:22px !important;
    line-height:1.25 !important; font-weight:800 !important; margin:0 0 12px !important;
}
.rec-items-list { margin:0 0 10px 0; padding-left:22px; color:#253B59; }
.rec-items-list li { padding:7px 0; font-size:15px; font-weight:600; }
.rec-total {
    color:#172B4D; font-size:15px; font-weight:800; margin-top:8px;
}
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
[data-testid="stForm"] {
    border:1px solid #DCE7F6 !important; border-radius:12px !important;
    padding:14px !important; background:#FFFFFF !important;
}
[data-testid="stDataFrame"] { border:1px solid #DCE7F6 !important; border-radius:10px !important; }
[data-testid="stAlert"] { border-radius:10px !important; }
hr { border-color:#DCE7F6 !important; margin:22px 0 !important; }
@media(max-width:900px) {
    [data-testid="stAppViewBlockContainer"] { padding:16px 14px 28px !important; }
    .rec-meta-row { grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }
    .rec-page-title { font-size:27px !important; }
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
    itens = [{"tipo": r["tipo"], "qtd_declarada": int(r["qtd_declarada"])}
             for _, r in itens_df.iterrows()]

    st.markdown(
        f'<div class="rec-section-heading"><span>▦</span> &nbsp; {dev["id"]}</div>',
        unsafe_allow_html=True,
    )
    meta = [
        ("Operação", dev.get("usuario", "")),
        ("Destino", dev.get("destino", "")),
        ("Placa", dev.get("placa") or "—"),
        ("Emissão", dev.get("data_criacao", "")),
    ]
    st.markdown(
        '<div class="rec-meta-row">' + "".join(
            f'<div class="rec-meta-item"><strong>{label}:</strong> {value}</div>'
            for label, value in meta
        ) + '</div>',
        unsafe_allow_html=True,
    )
    comp = str(dev.get("competencia", "") or "")
    comp_txt = dp.rotulo_mes(comp) if len(comp) == 7 else "—"
    competencia_txt = f"Competência: {comp_txt}"
    if dev.get("local_devolucao"):
        competencia_txt += f" &nbsp; · &nbsp; Devolvendo para: {dev.get('local_devolucao')}"
    st.markdown(f'<div class="rec-competencia">{competencia_txt}</div>', unsafe_allow_html=True)

    # Já processada?
    if dev.get("status") != dp.STATUS_TRANSITO:
        st.warning(
            f"Esta devolução já está **{dp.STATUS_LABEL.get(dev['status'], dev['status'])}**"
            + (f" — recebida em {dev.get('data_recebimento','')} por {dev.get('recebido_por','')}."
               if dev.get("recebido_por") else ".")
        )
        st.dataframe(
            itens_df.rename(columns={"tipo": "Tipo", "qtd_declarada": "Declarado",
                                     "qtd_recebida": "Recebido"})[["Tipo", "Declarado", "Recebido"]],
            width="stretch", hide_index=True,
        )
        return

    st.markdown('<div class="rec-items-heading">Itens declarados</div>', unsafe_allow_html=True)
    itens_html = "".join(
        f"<li><strong>{it['tipo'].title()}:</strong> {_fmt(it['qtd_declarada'])}</li>"
        for it in itens
    )
    st.markdown(f'<ul class="rec-items-list">{itens_html}</ul>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="rec-total">Total declarado: {_fmt(sum(i["qtd_declarada"] for i in itens))}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Aceitar o declarado**")
        if st.button("✅ Confirmar sem contar", type="primary", key=f"semcontar_{dev['id']}"):
            _confirmar(dev, itens, None, quem)
            st.success("Recebimento confirmado (declarado aceito).")
            st.rerun()

    with col_b:
        st.markdown("**Contar e confirmar**")
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
    st.markdown('<div class="rec-page-title">Recebimento de devoluções</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="rec-page-description">Aponte a câmera no QR do romaneio ou selecione uma devolução em trânsito abaixo.</div>',
        unsafe_allow_html=True,
    )

    devs = dp.devolucoes_df()

    # Aberto via QR (id + token na URL).
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

    # Lista de pendentes (em trânsito).
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
    with st.container(border=True, key="rec_filters"):
        st.markdown('<div class="rec-filter-heading"><span>⚙</span> Filtros</div>', unsafe_allow_html=True)
        escolha = st.selectbox("Devoluções em trânsito", list(opcoes.keys()))
    if escolha:
        dev = devs[devs["id"] == opcoes[escolha]].iloc[0].to_dict()
        st.markdown("---")
        _card_devolucao(dev, quem)
