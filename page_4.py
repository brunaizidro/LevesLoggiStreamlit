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

/* Texto branco nos botões de confirmação */
[data-testid="stAppViewContainer"] .stButton > button,
[data-testid="stFormSubmitButton"] button,
[data-testid="stAppViewContainer"] .stButton > button *,
[data-testid="stFormSubmitButton"] button * {
    color:#FFFFFF !important;
    -webkit-text-fill-color:#FFFFFF !important;
}

[data-testid="stForm"] {
    border:1px solid #DCE7F6 !important; border-radius:12px !important;
    padding:14px !important; background:#FFFFFF !important;
}
[data-testid="stDataFrame"] { border:1px solid #DCE7F6 !important; border-radius:10px !important; }
[data-testid="stAlert"] { border-radius:10px !important; }
hr { border-color:#DCE7F6 !important; margin:22px 0 !important; }
/* Layout aprimorado de conferência */
/* Ícones lineares no mesmo padrão da navegação lateral */
.rec-inline-icon{width:23px;height:23px;stroke:#0067FC;fill:none;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round;vertical-align:middle;}
.rec-meta-label{display:flex!important;align-items:center;gap:7px;}
.rec-meta-icon{display:inline-flex;align-items:center;justify-content:center;width:16px;height:16px;color:#0067FC;flex:0 0 16px;}
.rec-meta-icon svg{width:16px;height:16px;stroke:#0067FC;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;}

.rec-hero {background:linear-gradient(110deg,#EAF3FF 0%,#F5F9FF 100%);border:1px solid #DCEAFF;border-radius:16px;padding:16px 20px;margin:12px 0 18px;}
.rec-hero-title {display:flex;align-items:center;gap:12px;color:#102B50;font-size:23px;font-weight:800;}
.rec-status {display:inline-flex;align-items:center;background:#CFE7FF;color:#0058D6;border-radius:20px;padding:6px 13px;font-size:12px;font-weight:800;}
.rec-meta-panel {display:grid;grid-template-columns:1.5fr .8fr 1fr 1.2fr 1fr;gap:0;background:#FFFFFF;border:1px solid #DCE7F6;border-radius:12px;padding:15px 10px;margin-top:12px;}
.rec-meta-cell {padding:0 13px;border-right:1px solid #DCE7F6;min-width:0;color:#102B50;font-size:13px;}
.rec-meta-cell:last-child {border-right:0;}
.rec-meta-label {display:block;color:#536987;font-size:12px;font-weight:600;margin-bottom:5px;}
.rec-meta-value {font-weight:800;overflow-wrap:anywhere;}
.rec-panel {background:#FFFFFF;border:1px solid #DCE7F6;border-radius:15px;padding:17px 16px;box-shadow:0 3px 12px rgba(16,43,80,.035);min-width:0;}
.rec-panel-title {font-size:18px;font-weight:800;color:#102B50;margin:0 0 14px;display:flex;align-items:center;gap:10px;}
.rec-panel-title span {color:#0067FC;font-size:22px;}
.rec-declared-panel{padding:18px 17px 17px;background:#FFFFFF;border-color:#DCE8FA;}
.rec-declared-heading{display:flex;align-items:center;gap:11px;background:linear-gradient(100deg,#EAF3FF,#F3F8FF);border-radius:11px;padding:12px 14px;margin-bottom:15px;color:#102B50;font-size:18px;font-weight:800;}
.rec-heading-icon{display:inline-flex;align-items:center;justify-content:center;width:29px;height:29px;color:#0067FC;}
.rec-heading-icon svg{width:25px;height:25px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;}
.rec-item-row {display:flex;align-items:center;justify-content:space-between;background:#F2F7FF;border:1px solid #E5EFFF;border-radius:11px;padding:12px 14px;margin:9px 0;color:#102B50;font-weight:700;min-height:58px;transition:background .15s ease;}
.rec-item-name {display:flex;align-items:center;gap:13px;}
.rec-item-icon {display:inline-flex;align-items:center;justify-content:center;width:38px;height:38px;background:#E1EEFF;border-radius:10px;color:#0067FC;flex:0 0 38px;}
.rec-item-icon svg {width:23px;height:23px;stroke:currentColor;fill:none;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round;}
.rec-item-label {font-size:15px;font-weight:750;}
.rec-item-qty {display:inline-flex;align-items:center;justify-content:center;min-width:48px;height:38px;padding:0 12px;background:#DFECFF;border-radius:10px;color:#102B50;font-size:18px;font-weight:850;}
.rec-total-bar {display:flex;justify-content:space-between;align-items:center;background:#0067FC;color:#FFFFFF;border-radius:11px;padding:13px 15px;margin-top:14px;font-weight:800;min-height:56px;}
.rec-total-value{display:inline-flex;align-items:center;justify-content:center;min-width:52px;height:36px;padding:0 12px;border-radius:9px;background:#FFFFFF;color:#0067FC;font-size:18px;font-weight:850;}
.rec-actions {background:#FFFFFF;border:1px solid #DCE7F6;border-radius:15px;padding:15px 18px;margin-top:18px;}
.rec-actions-title {font-size:17px;font-weight:800;color:#102B50;margin-bottom:10px;}
@media(max-width:900px) {.rec-meta-panel{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.rec-meta-cell{border-right:0;padding:0 6px}.}

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

    comp = str(dev.get("competencia", "") or "")
    comp_txt = dp.rotulo_mes(comp) if len(comp) == 7 else "—"
    meta = [
        ('<svg viewBox="0 0 24 24"><path d="M12 21s7-4.4 7-11a7 7 0 1 0-14 0c0 6.6 7 11 7 11Z"/><circle cx="12" cy="10" r="2.5"/></svg>', "Operação", dev.get("usuario", "")),
        ('<svg viewBox="0 0 24 24"><path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5M9 21v-7h6v7"/></svg>', "Destino", dev.get("destino", "")),
        ('<svg viewBox="0 0 24 24"><path d="M3 7h11v11H3zM14 11h4l3 3v4h-7z"/><circle cx="7.5" cy="18.5" r="1.8"/><circle cx="17.5" cy="18.5" r="1.8"/></svg>', "Placa", dev.get("placa") or "—"),
        ('<svg viewBox="0 0 24 24"><rect x="4" y="5" width="16" height="16" rx="2"/><path d="M8 3v4M16 3v4M4 10h16"/></svg>', "Emissão", dev.get("data_criacao", "")),
        ('<svg viewBox="0 0 24 24"><rect x="4" y="5" width="16" height="16" rx="2"/><path d="M8 3v4M16 3v4M4 10h16M8 14h3M8 17h6"/></svg>', "Competência", comp_txt),
    ]
    st.markdown(
        f'<div class="rec-hero"><div class="rec-hero-title"><svg class="rec-inline-icon" viewBox="0 0 24 24"><path d="M3 7h11v11H3zM14 11h4l3 3v4h-7z"/><circle cx="7.5" cy="18.5" r="1.8"/><circle cx="17.5" cy="18.5" r="1.8"/></svg> &nbsp; {dev["id"]} '
        f'<span class="rec-status">Em conferência</span></div>'
        '<div class="rec-meta-panel">' + "".join(
            f'<div class="rec-meta-cell"><span class="rec-meta-label"><span class="rec-meta-icon">{ico}</span>{label}</span>'
            f'<span class="rec-meta-value">{value}</span></div>'
            for ico, label, value in meta
        ) + '</div></div>',
        unsafe_allow_html=True,
    )
    if dev.get("local_devolucao"):
        st.caption(f"Local de devolução: {dev.get('local_devolucao')}")

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

    total_declarado = sum(i["qtd_declarada"] for i in itens)
    col_itens, col_contagem = st.columns([1, 1], gap="large")
    with col_itens:
        icones_svg = {
            "GAYLORD": '<svg viewBox="0 0 24 24"><path d="m12 2 9 5v10l-9 5-9-5V7l9-5Z"/><path d="m3 7 9 5 9-5M12 12v10"/></svg>',
            "PALLET": '<svg viewBox="0 0 24 24"><path d="M3 4h18v12H3zM3 9h18M9 4v12m6-12v12M2 19h20M5 16v3m14-3v3"/></svg>',
            "SACA": '<svg viewBox="0 0 24 24"><path d="M8 3c1.5 1 6.5 1 8 0l-1 4c3 2 4 5 4 12 0 1-2 2-7 2s-7-1-7-2c0-7 1-10 4-12L8 3Z"/><path d="M9 7h6"/></svg>',
        }
        itens_html = "".join(
            f'<div class="rec-item-row"><div class="rec-item-name">'
            f'<span class="rec-item-icon">{icones_svg.get(str(it["tipo"]).upper(), "<svg viewBox=\'0 0 24 24\'><circle cx=\'12\' cy=\'12\' r=\'8\'/></svg>")}</span>'
            f'<span class="rec-item-label">{it["tipo"].title()}</span></div>'
            f'<span class="rec-item-qty">{_fmt(it["qtd_declarada"])}</span></div>'
            for it in itens
        )
        st.markdown(
            '<div class="rec-panel rec-declared-panel">'
            '<div class="rec-declared-heading"><span class="rec-heading-icon"><svg viewBox="0 0 24 24"><path d="m12 2 9 5v10l-9 5-9-5V7l9-5Z"/><path d="m3 7 9 5 9-5M12 12v10"/></svg></span>'
            '<span>Itens declarados</span></div>'
            + itens_html
            + f'<div class="rec-total-bar"><span>Total declarado</span><span class="rec-total-value">{_fmt(total_declarado)}</span></div></div>',
            unsafe_allow_html=True,
        )

    with col_contagem:
        st.markdown('<div class="rec-panel"><div class="rec-panel-title"><span>☑</span> Contar e confirmar</div>', unsafe_allow_html=True)
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
            ok = st.form_submit_button("✓ Confirmar recebimento", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
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

    st.markdown('<div class="rec-actions"><div class="rec-actions-title">Aceitar o declarado</div></div>', unsafe_allow_html=True)
    if st.button("✅ Confirmar sem contar", type="secondary", key=f"semcontar_{dev['id']}"):
        _confirmar(dev, itens, None, quem)
        st.success("Recebimento confirmado (declarado aceito).")
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
