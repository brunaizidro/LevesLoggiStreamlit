"""
page_3.py — Devoluções (operação).

Mostra o saldo a devolver (enviado − devolvido), permite declarar uma nova
devolução (limitada ao saldo) e gerar o Romaneio em PDF com QR. Lista as
devoluções da operação com status, reimpressão e cancelamento (em trânsito).
Para o perfil admin, permite selecionar a operação e registrar a devolução
manualmente em nome dela.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import pandas as pd
import streamlit as st

import data_extraction as dados
import data_processing as dp
import manual
import romaneio


# O app já possui a rota "Devoluções", mas atualmente o menu do perfil admin
# não a inclui. Como page_3 é importada pelo app antes da montagem da sidebar,
# adicionamos a opção somente ao radio de navegação quando o usuário é admin.
_radio_original = st.radio


def _radio_com_devolucao_admin(label, options, *args, **kwargs):
    opcoes = list(options)
    user = st.session_state.get("usuario") or {}
    if label == "Navegação" and user.get("perfil") == "admin":
        if "↩️ Devoluções" not in opcoes:
            try:
                pos = opcoes.index("🔔 Pendências")
            except ValueError:
                pos = len(opcoes)
            opcoes.insert(pos, "↩️ Devoluções")
    return _radio_original(label, opcoes, *args, **kwargs)


st.radio = _radio_com_devolucao_admin


def _fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def _operacoes_destinos_envios() -> dict[str, dict]:
    """Lê Operação (coluna C) e Destino (coluna E) da aba Envios.

    Mantém `destino` como a operação no restante da regra de devoluções,
    preservando a compatibilidade com o portal, e usa a coluna E somente
    para definir o local/CD físico da devolução.
    """
    try:
        ws = dados._aba(
            dados.ABA_ENVIOS,
            ["DATA", "tipo", "operacao", "total", "destino"],
        )
        valores = ws.get_all_values()
    except Exception:  # noqa: BLE001
        return {}

    mapa = {}
    for i, row in enumerate(valores):
        if i == 0 or not any(row):
            continue
        row = (row + [""] * 5)[:5]
        operacao = str(row[2]).strip()
        destino_fisico = str(row[4]).strip()
        if not operacao:
            continue

        chave = dp._normalizar(operacao)
        item = mapa.setdefault(
            chave,
            {"operacao": operacao, "destinos": []},
        )
        if destino_fisico and dp._normalizar(destino_fisico) not in {
            dp._normalizar(x) for x in item["destinos"]
        }:
            item["destinos"].append(destino_fisico)

    return mapa


def page_3():
    user = st.session_state.get("usuario") or {}
    eh_admin = user.get("perfil") == "admin"
    eh_gdl = user.get("perfil") == "gdl"
    destino = user.get("destino", "")

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
        [data-testid="stApp"] * { font-family: 'Montserrat', sans-serif !important; }
        .dev-page-kicker { color:#6383aa; font-size:12px; font-weight:700; letter-spacing:1.1px; text-transform:uppercase; margin:0 0 5px; }
        .dev-header { width:100% !important; display:flex !important; flex-direction:column !important; align-items:flex-start !important; gap:0 !important; margin:0 0 18px !important; padding:0 !important; }
        .dev-title-wrap { width:100% !important; display:block !important; text-align:left !important; margin:0 !important; padding:0 !important; line-height:1 !important; }
        .dev-page-title { color:#172B4D !important; display:block !important; width:100% !important; font-size:38px !important; line-height:1.18 !important; font-weight:800 !important; letter-spacing:-.8px !important; margin:0 !important; padding:0 !important; text-align:left !important; }
        .dev-page-subtitle { color:#627895 !important; display:block !important; font-family:'Montserrat',sans-serif !important; font-size:16px !important; line-height:1.55 !important; font-weight:600 !important; margin:2px 0 18px !important; padding:0 !important; position:static !important; top:auto !important; text-align:left !important; }
        .dev-section-title { display:flex; align-items:center; gap:14px; color:#173F78; background:#EAF2FF; border:1px solid #CFE0FF; border-radius:13px; padding:13px 18px; font-family:'Montserrat',sans-serif; font-size:20px; font-weight:800; margin:16px 0 12px; }
        .dev-new-title { display:flex; align-items:center; gap:16px; color:#173F78; background:#EAF2FF; border:1px solid #CFE0FF; border-radius:15px; padding:10px 18px; min-height:74px; font-family:'Montserrat',sans-serif; font-size:22px; font-weight:800; margin:16px 0 8px; }
        .dev-section-icon { display:inline-flex; align-items:center; justify-content:center; width:40px; height:40px; flex:0 0 40px; border-radius:11px; background:#075DE5; color:#fff; font-size:27px; line-height:1; font-weight:500; }
        div[data-testid='stForm'] { border:1px solid #d5e6ff !important; border-radius:17px !important; padding:14px 18px 16px !important; background:linear-gradient(180deg,#fbfdff 0%,#ffffff 100%) !important; }
        [class*="st-key-dev-qtd-"] { background:linear-gradient(180deg,#f5f8ff 0%,#f9fbff 100%); border:1px solid #D5E2FA; border-radius:15px; padding:12px 11px !important; min-height:80px; box-shadow:0 2px 6px rgba(23,75,136,.055); }
        [class*="st-key-dev-qtd-"] [data-testid="stHorizontalBlock"] { align-items:center; gap:8px; }
        .dev-qty-head { display:flex; align-items:center; gap:10px; min-height:52px; margin:0; white-space:nowrap; }
        .dev-qty-icon { display:inline-flex; align-items:center; justify-content:center; width:50px; height:50px; flex:0 0 50px; border-radius:12px; background:#E3EDFF; color:#075DE5; padding:9px; }
        .dev-qty-icon svg { width:100%; height:100%; }
        .dev-qty-title { display:flex; flex-direction:column; gap:4px; color:#0E2C5A; font-family:'Montserrat',sans-serif; line-height:1.15; }
        .dev-qty-title strong { font-size:14px; font-weight:800; }
        .dev-qty-title small { color:#7890B2; font-size:11px; font-weight:650; }
        [class*="st-key-dev-qtd-"] div[data-testid="stNumberInput"] { margin:0 !important; }
        [class*="st-key-dev-qtd-"] div[data-testid="stNumberInput"] input { font-size:27px !important; font-weight:800 !important; color:#0E2C5A !important; text-align:center !important; padding:0 2px !important; }
        [class*="st-key-dev-qtd-"] div[data-testid="stNumberInput"] button { color:#075DE5 !important; border-radius:9px !important; min-width:34px !important; }
        div[data-testid='stNumberInput'] label, div[data-testid='stTextInput'] label, div[data-testid='stTextArea'] label { color:#17385f !important; font-family:'Montserrat',sans-serif !important; font-weight:750 !important; }
        div[data-testid='stNumberInput'] > div, div[data-testid='stTextInput'] > div, div[data-testid='stTextArea'] > div { border-radius:10px !important; }
        div[data-testid='stNumberInput'] input, div[data-testid='stTextInput'] input, div[data-testid='stTextArea'] textarea { border-radius:10px !important; border-color:#cbd8e8 !important; background:#fff !important; font-family:'Montserrat',sans-serif !important; }
        div[data-testid='stTextArea'] textarea { min-height:68px !important; }
        .dev-field-label { color:#0E2C5A; font-family:'Montserrat',sans-serif; font-size:16px; font-weight:800; margin:12px 0 6px; }
        .dev-observation-label { margin-top:14px; }
        [class*="st-key-dev-plate-field"], [class*="st-key-dev-observation-field"] { width:100%; box-sizing:border-box; border:1px solid #C9D8F3; border-radius:13px; background:linear-gradient(180deg,#FBFDFF 0%,#F8FAFF 100%); padding:0 8px; overflow:hidden; }
        [class*="st-key-dev-plate-field"] [data-testid="stHorizontalBlock"], [class*="st-key-dev-observation-field"] [data-testid="stHorizontalBlock"] { display:flex !important; flex-wrap:nowrap !important; width:100% !important; align-items:stretch !important; gap:0 !important; }
        [class*="st-key-dev-plate-field"] [data-testid="column"]:first-child, [class*="st-key-dev-observation-field"] [data-testid="column"]:first-child { flex:0 0 64px !important; width:64px !important; max-width:64px !important; min-width:64px !important; min-height:44px !important; padding:0 !important; display:flex !important; align-items:center !important; justify-content:center !important; }
        [class*="st-key-dev-plate-field"] [data-testid="column"]:last-child, [class*="st-key-dev-observation-field"] [data-testid="column"]:last-child { flex:1 1 0% !important; width:calc(100% - 64px) !important; max-width:calc(100% - 64px) !important; min-width:0 !important; padding:0 !important; }
        [class*="st-key-dev-plate-field"] [data-testid="column"]:first-child [data-testid="stMarkdownContainer"], [class*="st-key-dev-observation-field"] [data-testid="column"]:first-child [data-testid="stMarkdownContainer"] { width:100% !important; display:flex !important; align-items:center !important; justify-content:center !important; margin:0 !important; padding:0 !important; }
        .dev-input-icon { display:flex !important; align-items:center !important; justify-content:center !important; width:64px; height:44px; margin:0 auto !important; border-right:1px solid #DCE7FA; color:#075DE5; padding:8px; box-sizing:border-box; line-height:0 !important; }
        .dev-input-icon svg { display:block; width:25px; height:25px; flex:0 0 25px; margin:auto !important; position:relative; left:-8px; top:-5px; }
        .dev-textarea-icon { height:64px; }
        [class*="st-key-dev-plate-field"] div[data-testid="stTextInput"], [class*="st-key-dev-observation-field"] div[data-testid="stTextArea"] { display:block !important; width:100% !important; max-width:100% !important; min-width:0 !important; margin:0 !important; padding:0 !important; }
        [class*="st-key-dev-plate-field"] div[data-testid="stTextInput"] > div, [class*="st-key-dev-observation-field"] div[data-testid="stTextArea"] > div { display:block !important; width:100% !important; max-width:100% !important; min-width:0 !important; border:0 !important; box-shadow:none !important; background:transparent !important; padding:0 !important; }
        [class*="st-key-dev-plate-field"] input, [class*="st-key-dev-observation-field"] textarea { display:block; width:100% !important; max-width:100% !important; min-width:0 !important; box-sizing:border-box !important; border:0 !important; outline:0 !important; box-shadow:none !important; border-radius:0 !important; background:transparent !important; color:#17345f !important; font-family:'Montserrat',sans-serif !important; }
        [class*="st-key-dev-plate-field"] input { height:44px !important; padding:0 12px !important; font-size:16px !important; }
        [class*="st-key-dev-observation-field"] textarea { min-height:64px !important; height:64px !important; padding:10px 12px !important; font-size:15px !important; resize:none !important; }
        [class*="st-key-dev-plate-field"] input:focus, [class*="st-key-dev-observation-field"] textarea:focus { border:0 !important; box-shadow:none !important; }
                div[data-testid='stFormSubmitButton'] button { background:#075DE5 !important; color:#fff !important; border:0 !important; border-radius:10px !important; font-family:'Montserrat',sans-serif !important; font-weight:800 !important; padding:10px 22px !important; }
        div[data-testid='stFormSubmitButton'] button:hover { background:#064fc4 !important; box-shadow:0 4px 12px rgba(7,93,229,.18) !important; }
        .dev-balance-card { position:relative; overflow:hidden; background:#ffffff; border:1px solid #d9e4f2; border-radius:14px; padding:18px 20px 17px; min-height:146px; box-shadow:0 3px 10px rgba(23,52,95,.045); transition:transform .18s ease, box-shadow .18s ease, border-color .18s ease; }
        .dev-balance-card:before { content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background:#2874df; }
        .dev-balance-card:hover { transform:translateY(-2px); border-color:#b8d2f5; box-shadow:0 7px 18px rgba(23,75,136,.09); }
        .dev-balance-label { color:#607895; font-family:'Montserrat',sans-serif; font-size:12px; font-weight:800; letter-spacing:.45px; text-transform:uppercase; margin-bottom:9px; text-align:center; }
        .dev-balance-qty { color:#142f55; font-family:'Montserrat',sans-serif; font-size:34px; line-height:1.05; font-weight:800; letter-spacing:-1px; margin-bottom:15px; text-align:center; }
        .dev-balance-caption { color:#8192a8; font-family:'Montserrat',sans-serif; font-size:11px; font-weight:700; margin-bottom:3px; padding-top:10px; border-top:1px solid #edf1f6; }
        .dev-balance-value { color:#174b88; font-family:'Montserrat',sans-serif; font-size:17px; font-weight:800; }
        .dev-total-banner { display:flex; align-items:center; gap:13px; background:#075DE5; border:1px solid #075DE5; border-radius:13px; padding:16px 20px; margin:14px 0 20px; color:#ffffff; font-family:'Montserrat',sans-serif; font-size:14px; font-weight:700; box-shadow:0 3px 10px rgba(7,93,229,.18); }
        .dev-total-banner strong { color:#ffffff; font-size:19px; font-weight:800; margin-left:4px; }
        div[data-testid="stSelectbox"] label, div[data-testid="stNumberInput"] label, div[data-testid="stTextInput"] label { color:#17385f !important; font-weight:650 !important; }
        div[data-testid="stSelectbox"] > div > div, div[data-testid="stNumberInput"] input, div[data-testid="stTextInput"] input { border-radius:10px !important; }
        div[data-testid="stExpander"] { border:1px solid #d5e6ff !important; border-radius:12px !important; background:#f7faff !important; }
        div[data-testid="stForm"] { border:1px solid #d5e6ff; border-radius:15px; padding:20px 18px 12px; background:#fbfdff; }
        div[data-testid="stFormSubmitButton"] button { background:#075BEA !important; color:white !important; border:0 !important; border-radius:10px !important; font-weight:700 !important; padding:10px 22px !important; }
        div[data-testid="stAlert"][kind="success"] { background:#e8f8f2 !important; border:1px solid #c9efdf !important; color:#126b62 !important; border-radius:11px !important; }
        div[data-testid="stAlert"][kind="info"] { background:#eaf3ff !important; border:1px solid #d8e8ff !important; color:#1155cc !important; border-radius:12px !important; }
        .dev-list-title { color:#172b4d !important; font-family:'Montserrat',sans-serif !important; font-size:24px !important; font-weight:800 !important; letter-spacing:-.4px !important; margin:22px 0 12px !important; }
        .dev-table-header { display:grid; grid-template-columns:31% 18% 18% 15% 18%; align-items:center; background:#eaf3ff; color:#17345f; border-radius:10px 10px 0 0; margin:-1px -1px 12px; padding:12px 16px; font-family:'Montserrat',sans-serif; font-size:11px; font-weight:800; letter-spacing:.45px; }
        .dev-record-cell { display:flex; align-items:center; gap:12px; min-height:46px; }
        .dev-record-icon { display:flex; align-items:center; justify-content:center; flex:0 0 36px; width:36px; height:36px; border-radius:11px; background:#e5f0ff; color:#075bea; font-size:20px; font-weight:800; }
        .dev-record-id { display:block; color:#172b4d !important; font-family:'Montserrat',sans-serif !important; font-size:14px !important; font-weight:800 !important; line-height:1.35; }
        .dev-record-meta { display:block; color:#526985 !important; font-family:'Montserrat',sans-serif !important; font-size:12px !important; font-weight:500 !important; line-height:1.45; margin-top:2px !important; }
        .dev-status { display:inline-flex; align-items:center; gap:6px; border-radius:8px; padding:6px 10px; font-family:'Montserrat',sans-serif; font-size:12px; font-weight:700; white-space:nowrap; background:#eaf3ff; color:#1155cc; }
        .dev-status-check { font-size:14px; font-weight:900; }
        .dev-status-ok { background:#d9f9d4; color:#087b55; }
        .dev-status-cancel { background:#fff0f0; color:#bd3e45; }
        .dev-operation { display:flex; align-items:center; gap:8px; color:#243b60; font-family:'Montserrat',sans-serif; font-size:13px; font-weight:600; white-space:nowrap; }
        .dev-operation span { color:#075bea; font-size:18px; font-weight:800; }
        .dev-quantity { color:#172b4d !important; font-family:'Montserrat',sans-serif !important; font-size:16px !important; font-weight:800 !important; text-align:center; }
        .dev-row-divider { height:1px; background:#dce5f0; margin:0 2px 10px; }
        div[data-testid="stVerticalBlockBorderWrapper"] { border:1px solid #cfdced !important; border-radius:12px !important; background:#fff !important; }
        div[data-testid="stVerticalBlockBorderWrapper"] > div { padding:12px 14px !important; }
        div[data-testid="stDownloadButton"] button { border:1px solid #075bea !important; border-radius:10px !important; font-family:'Montserrat',sans-serif !important; font-weight:700 !important; color:#17345f !important; background:#fff !important; white-space:nowrap !important; padding:7px 12px !important; }
        div[data-testid="stDownloadButton"] button:hover { border-color:#1155cc !important; color:#1155cc !important; background:#f5f9ff !important; }
        hr.sb-sep { border-color:#d8e7f8 !important; margin:22px 0 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    subtitulo = (
        "Selecione a operação e registre uma devolução manual em nome dela. O saldo e a competência serão calculados para a operação selecionada."
        if eh_admin or eh_gdl else
        "Declare o que está devolvendo, gere o romaneio com QR e envie impresso junto com os itens."
    )
    st.markdown(
        "<div class='dev-header'>"
        "<div class='dev-page-kicker'>PORTAL LEVES &nbsp;/&nbsp; DEVOLUÇÕES</div>"
        "<div class='dev-title-wrap'><div class='dev-page-title'>Devoluções</div></div>"
        "<div class='dev-page-subtitle'>" + subtitulo + "</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    if eh_admin or eh_gdl:
        mapa_operacoes = _operacoes_destinos_envios()
        if not mapa_operacoes:
            st.info("Nenhuma operação encontrada na aba Envios.")
            return

        chaves = sorted(mapa_operacoes, key=lambda k: mapa_operacoes[k]["operacao"].lower())
        operacoes = [mapa_operacoes[k]["operacao"] for k in chaves]

        destino = st.selectbox(
            "Operação",
            operacoes,
            key="devolucao_operacao_admin",
            help=("Selecione a operação para visualizar as devoluções." if eh_gdl else "Selecione a operação em nome da qual a devolução será registrada."),
        )

        if eh_gdl:
            st.info("Perfil GDL: visualização das devoluções. O registro de novas devoluções é exclusivo do administrador.")

    # ---- Competência selecionada (antes do saldo) ----
    if not eh_gdl:
        elegiveis = dp.competencias_elegiveis(destino)
        if not elegiveis:
            st.info("Nenhuma competência aberta para devolução (prazos encerrados).")
            _minhas_devolucoes(destino, eh_admin=eh_admin)
            return

        rot_mes = {m: dp.rotulo_mes(m) for m in elegiveis}
        st.markdown("<div class='dev-section-title'>📅 &nbsp; Devolução referente ao saldo de qual mês?</div>", unsafe_allow_html=True)
        if len(elegiveis) > 1:
            st.info("Marque o mês de competência ao qual os itens devolvidos pertencem.")

        st.markdown(
            """
            <style>
            div[role="radiogroup"] label p {
                font-size: 18px !important;
                font-weight: 600 !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Quando só existe uma competência aberta, seleciona automaticamente.
        # Isso evita exigir um clique desnecessário após o prazo do mês anterior.
        if len(elegiveis) == 1:
            st.session_state["competencia_devolucao"] = rot_mes[elegiveis[0]]

        escolha_mes = st.radio(
            "Selecione a competência da devolução",
            options=[rot_mes[m] for m in elegiveis],
            index=0 if len(elegiveis) == 1 else None,
            horizontal=True,
            key="competencia_devolucao",
            label_visibility="collapsed",
        )
        if not escolha_mes:
            st.warning("⚠️ Marque o **mês de competência** desta devolução para continuar.")
            _minhas_devolucoes(destino, eh_admin=eh_admin)
            return

        mes_ref = next(m for m, r in rot_mes.items() if r == escolha_mes)
        prazo_txt = dp.prazo_devolucao(mes_ref).strftime("%d/%m/%Y")
        st.success(f"Competência selecionada: **{escolha_mes}** · prazo: **{prazo_txt}**")

    # ---- Saldo a devolver ----
    if eh_gdl:
        saldo = dp.saldo_por_tipo(destino)
    else:
        conc = dp.conciliacao(mes_ref)
        if not conc.empty:
            conc = conc[conc["destino"].map(dp._normalizar) == dp._normalizar(destino)].copy()
            conc["saldo"] = conc["em_aberto"].astype(int)
            saldo = conc[conc["saldo"] > 0][["tipo", "enviado", "devolvido", "saldo"]].copy()
        else:
            saldo = pd.DataFrame(columns=["tipo", "enviado", "devolvido", "saldo"])
    if saldo.empty or saldo["enviado"].sum() == 0:
        if eh_admin:
            st.info(f"Nenhum ativo enviado para a operação **{destino}** até o momento.")
        else:
            st.info("Nenhum ativo enviado para a sua operação até o momento.")
        return

    st.markdown("<div class='dev-section-title'>Saldo a devolver" + ("" if eh_gdl else f" — {escolha_mes}") + "</div>", unsafe_allow_html=True)
    pr = dp.precos()
    cols = st.columns(max(len(saldo), 1))
    for i, (_, r) in enumerate(saldo.iterrows()):
        tipo = r["tipo"]
        qtd_saldo = int(r["saldo"])
        valor_unitario = pr.get(tipo, 0)
        valor_total_insumo = qtd_saldo * valor_unitario

        ajuda = f"Enviado: {_fmt(r['enviado'])} · Já devolvido: {_fmt(r['devolvido'])}"
        if valor_unitario > 0:
            ajuda += f" · {dp.fmt_brl(valor_total_insumo)}"

        with cols[i]:
            valor_html = (
                f"<div class='dev-balance-caption'>Valor do saldo</div>"
                f"<div class='dev-balance-value'>{dp.fmt_brl(valor_total_insumo)}</div>"
                if valor_unitario > 0 else ""
            )
            st.markdown(
                f"""
                <div class="dev-balance-card" title="{ajuda}">
                    <div class="dev-balance-label">{tipo.title()}</div>
                    <div class="dev-balance-qty">{_fmt(qtd_saldo)}</div>
                    {valor_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

    if dp.tem_precos():
        total_val = sum(
            int(r["saldo"]) * pr.get(r["tipo"], 0)
            for _, r in saldo.iterrows()
        )
        st.markdown(
            f"<div class='dev-total-banner'><span style='font-size:20px;'>R$</span><span>Valor total a devolver</span><strong>{dp.fmt_brl(total_val)}</strong></div>",
            unsafe_allow_html=True,
        )

    st.markdown("<hr class='sb-sep' style='border-top-color:#e6e6e6;'>", unsafe_allow_html=True)

    # ---- Nova devolução ----
    if eh_gdl:
        _minhas_devolucoes(destino, eh_admin=False, eh_gdl=True)
        return

    st.markdown("<div class='dev-new-title'><span class='dev-section-icon'>＋</span><span>Nova devolução</span></div>", unsafe_allow_html=True)
    pend = {t: q for t, q in dp.pending_mes_tipo(destino, mes_ref).items() if q > 0}
    if not pend:
        st.success(f"Sem pendência de devolução para {escolha_mes}. 🎉")
    else:
        with st.form("nova_devolucao", clear_on_submit=True):
            qtds = {}
            itens_pend = sorted(pend.items())
            fcols = st.columns(len(itens_pend), gap="medium")
            icones_insumo = {
                "gaylord": "<svg viewBox='0 0 48 48' aria-hidden='true'><path d='M7 15 24 6l17 9v19L24 43 7 34Z' fill='none' stroke='currentColor' stroke-width='2.6' stroke-linejoin='round'/><path d='m7 15 17 10 17-10M24 25v18M16 10l17 10M32 10 15 20' fill='none' stroke='currentColor' stroke-width='2.4' stroke-linejoin='round'/></svg>",
                "pallet": "<svg viewBox='0 0 48 48' aria-hidden='true'><path d='m5 17 19-10 19 10-19 10Z M5 25l19 10 19-10M5 33l19 10 19-10' fill='none' stroke='currentColor' stroke-width='2.6' stroke-linejoin='round'/></svg>",
                "saca": "<svg viewBox='0 0 48 48' aria-hidden='true'><path d='M18 7c2 4 10 4 12 0M18 7l-2 7c-5 4-8 11-8 20 0 5 7 7 16 7s16-2 16-7c0-9-3-16-8-20l-2-7M16 14h16M17 22c4 2 10 2 14 0' fill='none' stroke='currentColor' stroke-width='2.6' stroke-linecap='round' stroke-linejoin='round'/></svg>",
            }
            for i, (t, q) in enumerate(itens_pend):
                with fcols[i].container(key=f"dev-qtd-{i}"):
                    qty_cols = st.columns([1.45, 1.0], gap="small", vertical_alignment="center")
                    with qty_cols[0]:
                        st.markdown(
                            f"<div class='dev-qty-head'>"
                            f"<span class='dev-qty-icon'>{icones_insumo.get(str(t).lower(), '＋')}</span>"
                            f"<span class='dev-qty-title'><strong>{t.upper()}</strong>"
                            f"<small>Máx. {_fmt(q)}</small></span></div>",
                            unsafe_allow_html=True,
                        )
                    with qty_cols[1]:
                        qtds[t] = st.number_input(
                            f"Quantidade de {t.title()}",
                            min_value=0, max_value=int(q), step=1, value=0,
                            label_visibility="collapsed", key=f"dev-quantidade-{i}",
                        )
            st.markdown("<div class='dev-field-label'>Placa do veículo</div>", unsafe_allow_html=True)
            with st.container(key="dev-plate-field"):
                plate_icon, plate_input = st.columns([0.065, 0.935], gap=0, vertical_alignment="center")
                with plate_icon:
                    st.markdown("<div class='dev-input-icon'><svg viewBox='0 0 24 24' aria-hidden='true'><path d='M3 7h12v11H3zM15 11h4l3 3v4h-7zM7 18a2 2 0 1 0 4 0m7 0a2 2 0 1 0 4 0' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'/></svg></div>", unsafe_allow_html=True)
                with plate_input:
                    placa = st.text_input("Placa do veículo", placeholder="Ex.: ABC1D23", label_visibility="collapsed")
            st.markdown("<div class='dev-field-label dev-observation-label'>Observação (opcional)</div>", unsafe_allow_html=True)
            with st.container(key="dev-observation-field"):
                obs_icon, obs_input = st.columns([0.065, 0.935], gap=0, vertical_alignment="center")
                with obs_icon:
                    st.markdown("<div class='dev-input-icon dev-textarea-icon'><svg viewBox='0 0 24 24' aria-hidden='true'><rect x='5' y='3' width='14' height='18' rx='1.5' fill='none' stroke='currentColor' stroke-width='1.8'/><path d='M8 8h8M8 12h8M8 16h5' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round'/></svg></div>", unsafe_allow_html=True)
                with obs_input:
                    obs = st.text_area("Observação", placeholder="Informe alguma particularidade desta devolução...", height=64, label_visibility="collapsed")
            enviar = st.form_submit_button("▤  Gerar devolução", type="primary")

        if enviar:
            itens = [{"tipo": t, "qtd_declarada": int(q)} for t, q in qtds.items() if q > 0]
            placa_norm = "".join(str(placa or "").upper().split()).replace("-", "")
            if not itens:
                st.error("Informe ao menos uma quantidade.")
            elif not placa_norm:
                st.error("Informe a placa do veículo.")
            else:
                total = sum(it["qtd_declarada"] for it in itens)
                id_dev = dados.proximo_codigo_devolucao()
                token = uuid.uuid4().hex
                agora = datetime.now(dp.TZ).strftime("%Y-%m-%d %H:%M:%S")
                dev = {
                    "id": id_dev, "token": token, "data_criacao": agora,
                    "usuario": user.get("nome", user.get("usuario", "")),
                    "destino": destino, "status": dp.STATUS_TRANSITO,
                    "total_declarado": total, "total_recebido": "",
                    "data_recebimento": "", "recebido_por": "", "obs": obs,
                    "placa": placa_norm,
                    "competencia": mes_ref,
                }
                dados.criar_devolucao(dev, itens)
                st.success(f"Devolução **{id_dev}** criada. Baixe o romaneio abaixo e envie com os itens.")
                pdf = romaneio.gerar_romaneio_pdf(dev, itens, dp.base_url())
                st.download_button(
                    "📄 Baixar romaneio (PDF)", pdf, file_name=f"{id_dev}.pdf",
                    mime="application/pdf", key=f"dl_{id_dev}", type="primary",
                )

    _minhas_devolucoes(destino, eh_admin=eh_admin)


def _minhas_devolucoes(destino: str, eh_admin: bool = False, eh_gdl: bool = False):
    st.markdown(
        "<div class='dev-list-title'>"
        + ("Devoluções da operação" if (eh_admin or eh_gdl) else "Minhas devoluções")
        + "</div>",
        unsafe_allow_html=True,
    )
    devs = dp.devolucoes_df()
    if devs.empty:
        st.caption("Nenhuma devolução registrada ainda.")
        return
    minhas = devs[devs["destino"].map(dp._normalizar) == dp._normalizar(destino)]
    minhas = minhas.sort_values("dt_criacao", ascending=False)
    if minhas.empty:
        st.caption("Nenhuma devolução registrada ainda.")
        return

    with st.container(border=True):
        st.markdown(
            "<div class='dev-table-header'>"
            "<div>REGISTRO</div><div>STATUS</div><div>OPERAÇÃO</div>"
            "<div>QUANTIDADE</div><div></div></div>",
            unsafe_allow_html=True,
        )
        for idx, (_, d) in enumerate(minhas.iterrows()):
            c1, c2, c3, c4, c5 = st.columns(
                [2.0, 1.15, 1.2, 0.95, 1.0], vertical_alignment="center"
            )
            comp = d.get("competencia")
            comp_txt = dp.rotulo_mes(comp) if comp and len(str(comp)) == 7 else ""
            c1.markdown(
                "<div class='dev-record-cell'>"
                "<span class='dev-record-icon'>▤</span>"
                "<span><span class='dev-record-id'>" + str(d["id"]) + "</span>"
                "<span class='dev-record-meta'>" + str(d["data_criacao"]) + "</span>"
                + (f"<span class='dev-record-meta'>{comp_txt}</span>" if comp_txt else "")
                + "</span></div>",
                unsafe_allow_html=True,
            )
            status_txt = dp.STATUS_LABEL.get(d["status"], d["status"])
            status_class = (
                "dev-status-cancel" if "cancel" in str(d["status"]).lower()
                else "dev-status-ok" if any(x in str(status_txt).lower() for x in ("conferido", "recebido"))
                else ""
            )
            c2.markdown(
                f"<span class='dev-status {status_class}'>"
                f"<span class='dev-status-check'>✓</span>{status_txt}</span>",
                unsafe_allow_html=True,
            )
            operacao = str(d.get("placa") or "").strip()
            c3.markdown(
                f"<div class='dev-operation'><span>🚚</span>{operacao or '—'}</div>",
                unsafe_allow_html=True,
            )
            c4.markdown(
                f"<div class='dev-quantity'>{_fmt(d['total_declarado'])}</div>",
                unsafe_allow_html=True,
            )
            with c5:
                itens = dp.itens_da_devolucao(d["id"])
                itens_l = [{"tipo": r["tipo"], "qtd_declarada": r["qtd_declarada"]}
                           for _, r in itens.iterrows()]
                dev_h = d.to_dict()
                st.download_button(
                    "▤  Romaneio",
                    romaneio.gerar_romaneio_pdf(dev_h, itens_l, dp.base_url()),
                    file_name=f"{d['id']}.pdf", mime="application/pdf",
                    key=f"rom_{d['id']}",
                )
                if d["status"] == dp.STATUS_TRANSITO:
                    if st.button("Cancelar", key=f"can_{d['id']}"):
                        dados.atualizar_devolucao(d["id"], {"status": dp.STATUS_CANCELADO})
                        st.rerun()
            if idx < len(minhas) - 1:
                st.markdown("<div class='dev-row-divider'></div>", unsafe_allow_html=True)
