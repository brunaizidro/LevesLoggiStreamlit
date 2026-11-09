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
        .dev-page-title { color:#172B4D !important; display:block !important; width:100% !important; font-size:clamp(28px,2.3vw,34px) !important; line-height:1.18 !important; font-weight:800 !important; letter-spacing:-.8px !important; margin:0 !important; padding:0 !important; text-align:left !important; }
        .dev-page-subtitle { color:#627895 !important; display:block !important; font-family:'Montserrat',sans-serif !important; font-size:14px !important; line-height:1.55 !important; font-weight:600 !important; margin:2px 0 18px !important; padding:0 !important; position:static !important; top:auto !important; text-align:left !important; }
        .dev-section-title { display:flex; align-items:center; gap:14px; color:#173F78; background:#EAF2FF; border:1px solid #CFE0FF; border-radius:13px; padding:13px 18px; font-family:'Montserrat',sans-serif; font-size:18px; font-weight:800; margin:16px 0 12px; }
        .dev-new-title { position:relative; display:flex; align-items:center; gap:16px; color:#123f7c; background:linear-gradient(105deg,#eaf3ff 0%,#f5f9ff 58%,#e2efff 100%); border:2px solid #6da8ff; border-radius:17px; padding:13px 22px; min-height:86px; font-family:'Montserrat',sans-serif; font-size:23px; font-weight:800; margin:18px 0 10px; box-shadow:0 5px 15px rgba(7,93,229,.09); overflow:hidden; }
        .dev-new-title-copy { display:flex; flex-direction:column; gap:4px; position:relative; z-index:1; }
        .dev-new-title-copy strong { color:#123f7c; font-size:23px; line-height:1.15; font-weight:850; }
        .dev-new-title-copy small { color:#54749b; font-size:13px; line-height:1.3; font-weight:650; }
        .dev-new-truck { display:flex; align-items:center; justify-content:center; position:absolute; right:22px; bottom:0; width:205px; height:72px; color:#1680f5; opacity:.9; }
        .dev-new-truck:before { content:''; position:absolute; right:-20px; bottom:-28px; width:235px; height:90px; border-radius:60% 0 0 0; background:linear-gradient(110deg,rgba(191,220,255,.35),rgba(141,190,255,.55)); }
        .dev-new-truck svg { position:relative; z-index:1; width:100%; height:100%; }
        div[data-testid='stForm'] { border:2px solid #c7dcff !important; border-radius:17px !important; padding:16px 18px 16px !important; background:linear-gradient(180deg,#f8fbff 0%,#ffffff 100%) !important; box-shadow:0 5px 16px rgba(30,91,165,.07) !important; }
        div[data-testid='stFormSubmitButton'] button { min-height:48px !important; padding:11px 25px !important; border-radius:12px !important; font-size:14px !important; box-shadow:0 4px 10px rgba(7,93,229,.2) !important; }
        @media (max-width:700px) { .dev-new-title { min-height:74px; padding:12px 14px; } .dev-new-title-copy strong { font-size:20px; } .dev-new-title-copy small { font-size:11px; max-width:240px; } .dev-new-truck { opacity:.2; right:4px; width:120px; } }
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
        .dev-field-label { color:#0E2C5A; font-family:'Montserrat',sans-serif; font-size:13px; font-weight:700; margin:12px 0 6px; }
        .dev-observation-label { margin-top:14px; }
        [class*="st-key-dev-plate-field"], [class*="st-key-dev-observation-field"] { width:100%; box-sizing:border-box; border:1px solid #C9D8F3; border-radius:13px; background:linear-gradient(180deg,#FBFDFF 0%,#F8FAFF 100%); padding:0 8px; overflow:hidden; }
        [class*="st-key-dev-plate-field"] [data-testid="stHorizontalBlock"], [class*="st-key-dev-observation-field"] [data-testid="stHorizontalBlock"] { display:flex !important; flex-wrap:nowrap !important; width:100% !important; align-items:stretch !important; gap:0 !important; }
        [class*="st-key-dev-plate-field"] [data-testid="column"]:first-child, [class*="st-key-dev-observation-field"] [data-testid="column"]:first-child { flex:0 0 64px !important; width:64px !important; max-width:64px !important; min-width:64px !important; min-height:44px !important; padding:0 !important; display:flex !important; align-items:center !important; justify-content:center !important; }
        [class*="st-key-dev-plate-field"] [data-testid="column"]:last-child, [class*="st-key-dev-observation-field"] [data-testid="column"]:last-child { flex:1 1 0% !important; width:calc(100% - 64px) !important; max-width:calc(100% - 64px) !important; min-width:0 !important; padding:0 !important; }
        [class*="st-key-dev-plate-field"] [data-testid="column"]:first-child [data-testid="stMarkdownContainer"], [class*="st-key-dev-observation-field"] [data-testid="column"]:first-child [data-testid="stMarkdownContainer"] { width:100% !important; display:flex !important; align-items:center !important; justify-content:center !important; margin:0 !important; padding:0 !important; }
        .dev-input-icon { display:flex !important; align-items:center !important; justify-content:center !important; width:64px; height:44px; margin:0 auto !important; border-right:1px solid #DCE7FA; color:#075DE5; padding:8px; box-sizing:border-box; line-height:0 !important; }
        .dev-input-icon svg { display:block; width:25px; height:25px; flex:0 0 25px; margin:auto !important; position:relative; left:-8px; top:-9px; }
        .dev-textarea-icon { height:64px; }
        [class*="st-key-dev-plate-field"] div[data-testid="stTextInput"], [class*="st-key-dev-observation-field"] div[data-testid="stTextArea"] { display:block !important; width:100% !important; max-width:100% !important; min-width:0 !important; margin:0 !important; padding:0 !important; }
        [class*="st-key-dev-plate-field"] div[data-testid="stTextInput"] > div, [class*="st-key-dev-observation-field"] div[data-testid="stTextArea"] > div { display:block !important; width:100% !important; max-width:100% !important; min-width:0 !important; border:0 !important; box-shadow:none !important; background:transparent !important; padding:0 !important; }
        [class*="st-key-dev-plate-field"] input, [class*="st-key-dev-observation-field"] textarea { display:block; width:100% !important; max-width:100% !important; min-width:0 !important; box-sizing:border-box !important; border:0 !important; outline:0 !important; box-shadow:none !important; border-radius:0 !important; background:transparent !important; color:#17345f !important; font-family:'Montserrat',sans-serif !important; }
        [class*="st-key-dev-plate-field"] input { height:44px !important; padding:0 12px !important; font-size:14px !important; }
        [class*="st-key-dev-observation-field"] textarea { min-height:64px !important; height:64px !important; padding:10px 12px !important; font-size:14px !important; resize:none !important; }
        [class*="st-key-dev-plate-field"] input:focus, [class*="st-key-dev-observation-field"] textarea:focus { border:0 !important; box-shadow:none !important; }
                div[data-testid='stFormSubmitButton'] button { background:#075DE5 !important; color:#fff !important; border:0 !important; border-radius:10px !important; font-family:'Montserrat',sans-serif !important; font-weight:800 !important; padding:10px 22px !important; }
        div[data-testid='stFormSubmitButton'] button:hover { background:#064fc4 !important; box-shadow:0 4px 12px rgba(7,93,229,.18) !important; }
        .dev-balance-section-title { display:flex; align-items:center; gap:15px; width:100%; box-sizing:border-box; color:#104783; background:linear-gradient(105deg,#eaf3ff 0%,#dceaff 100%); border:1px solid #c9ddff; border-radius:15px; padding:10px 18px; min-height:62px; margin:12px 0 10px; font-family:'Montserrat',sans-serif; font-size:18px; line-height:1.25; font-weight:800; letter-spacing:-.35px; }
        .dev-balance-section-title svg { width:32px; height:32px; flex:0 0 32px; color:#075DE5; }
        .dev-balance-card { position:relative; overflow:hidden; box-sizing:border-box; background:#fff; border:1px solid #d6e4f7; border-radius:16px; padding:15px 18px 13px; min-height:178px; box-shadow:0 6px 16px rgba(28,89,160,.08); transition:transform .18s ease, box-shadow .18s ease, border-color .18s ease; }
        .dev-balance-card:before { content:""; position:absolute; left:0; top:0; bottom:0; width:5px; background:#1680f5; }
        .dev-balance-card:hover { transform:translateY(-2px); border-color:#b8d2f5; box-shadow:0 12px 25px rgba(23,75,136,.13); }
        .dev-balance-top { display:flex; align-items:center; gap:15px; min-height:72px; }
        .dev-balance-icon { display:flex; align-items:center; justify-content:center; flex:0 0 72px; width:72px; height:68px; box-sizing:border-box; border-radius:20px; background:#e9f3ff; color:#1680f5; padding:17px; }
        .dev-balance-icon svg { width:100%; height:100%; display:block; }
        .dev-balance-divider { align-self:stretch; width:1px; min-height:68px; background:#d8e5f6; }
        .dev-balance-info { display:flex; flex-direction:column; align-items:flex-start; justify-content:center; min-width:0; }
        .dev-balance-label { color:#123b6c; font-family:'Montserrat',sans-serif; font-size:15px; line-height:1.2; font-weight:800; letter-spacing:.15px; text-transform:uppercase; margin:0 0 7px; text-align:left; }
        .dev-balance-qty { color:#123b6c; font-family:'Montserrat',sans-serif; font-size:40px; line-height:1; font-weight:800; letter-spacing:-2px; margin:0; text-align:left; }
        .dev-balance-caption { color:#7188a5; font-family:'Montserrat',sans-serif; font-size:12px; font-weight:750; margin:11px 0 5px; padding-top:10px; border-top:1px solid #e5edf7; }
        .dev-balance-value { color:#0755ad; font-family:'Montserrat',sans-serif; font-size:18px; line-height:1.2; font-weight:800; }
        .dev-total-banner { display:flex; align-items:center; gap:15px; box-sizing:border-box; width:100%; background:linear-gradient(105deg,#0646a8 0%,#075de5 100%); border:1px solid #075de5; border-radius:15px; padding:10px 20px; min-height:72px; margin:12px 0 16px; color:#fff; font-family:'Montserrat',sans-serif; font-size:20px; font-weight:800; box-shadow:0 9px 20px rgba(7,93,229,.2); }
        .dev-total-icon { display:flex; align-items:center; justify-content:center; flex:0 0 48px; width:48px; height:46px; color:#fff; border-right:2px solid rgba(255,255,255,.25); padding-right:18px; box-sizing:content-box; }
        .dev-total-icon svg { width:42px; height:42px; display:block; }
        .dev-total-label { color:#fff; white-space:nowrap; }
        .dev-total-banner strong { display:inline-flex; align-items:center; justify-content:center; min-height:48px; padding:0 20px; box-sizing:border-box; border-radius:13px; background:rgba(65,151,255,.28); color:#fff; font-size:27px; line-height:1; font-weight:800; letter-spacing:-1px; white-space:nowrap; margin-left:0; }
        @media (max-width: 900px) {
          .dev-balance-card { padding:14px 16px 12px; min-height:170px; }
          .dev-balance-top { gap:12px; min-height:68px; }
          .dev-balance-icon { flex-basis:68px; width:68px; height:66px; padding:13px; border-radius:16px; }
          .dev-balance-divider { min-height:66px; }
          .dev-balance-label { font-size:14px; margin-bottom:7px; }
          .dev-balance-qty { font-size:38px; }
          .dev-balance-value { font-size:18px; }
          .dev-total-banner { gap:13px; padding:10px 16px; min-height:72px; }
          .dev-total-banner strong { font-size:25px; min-height:48px; padding:0 16px; }
        }
        @media (max-width: 600px) {
          .dev-balance-section-title { font-size:17px; padding:14px 16px; min-height:64px; }
          .dev-balance-section-title svg { width:32px; height:32px; flex-basis:32px; }
          .dev-total-banner { flex-wrap:wrap; gap:12px; }
          .dev-total-icon { flex-basis:42px; width:42px; padding-right:12px; }
          .dev-total-icon svg { width:42px; height:42px; }
          .dev-total-label { white-space:normal; font-size:16px; }
          .dev-total-banner strong { width:100%; font-size:28px; }
        }
        div[data-testid="stSelectbox"] label, div[data-testid="stNumberInput"] label, div[data-testid="stTextInput"] label { color:#17385f !important; font-weight:650 !important; }
        div[data-testid="stSelectbox"] > div > div, div[data-testid="stNumberInput"] input, div[data-testid="stTextInput"] input { border-radius:10px !important; }
        div[data-testid="stExpander"] { border:1px solid #d5e6ff !important; border-radius:12px !important; background:#f7faff !important; }
        div[data-testid="stForm"] { border:1px solid #d5e6ff; border-radius:15px; padding:20px 18px 12px; background:#fbfdff; }
        div[data-testid="stFormSubmitButton"] button { background:#075BEA !important; color:white !important; border:0 !important; border-radius:10px !important; font-weight:700 !important; padding:10px 22px !important; }
        div[data-testid="stAlert"][kind="success"] { background:#e8f8f2 !important; border:1px solid #c9efdf !important; color:#126b62 !important; border-radius:11px !important; }
        div[data-testid="stAlert"][kind="info"] { background:#eaf3ff !important; border:1px solid #d8e8ff !important; color:#1155cc !important; border-radius:12px !important; }
        .dev-list-title { color:#172b4d !important; font-family:'Montserrat',sans-serif !important; font-size:22px !important; font-weight:800 !important; letter-spacing:-.4px !important; margin:22px 0 12px !important; }
        .dev-table-header { display:grid; grid-template-columns:31% 18% 18% 15% 18%; align-items:center; background:#eaf3ff; color:#17345f; border-radius:10px 10px 0 0; margin:-1px -1px 12px; padding:12px 16px; font-family:'Montserrat',sans-serif; font-size:11px; font-weight:800; letter-spacing:.45px; }
        .dev-table-header > div:nth-child(2), .dev-table-header > div:nth-child(3), .dev-table-header > div:nth-child(4) { text-align:center !important; }
        .dev-record-cell { display:flex; align-items:center; gap:12px; min-height:46px; }
        .dev-record-icon { display:flex; align-items:center; justify-content:center; flex:0 0 36px; width:36px; height:36px; border-radius:11px; background:#e5f0ff; color:#075bea; font-size:20px; font-weight:800; }
        .dev-record-id { display:block; color:#172b4d !important; font-family:'Montserrat',sans-serif !important; font-size:14px !important; font-weight:800 !important; line-height:1.35; }
        .dev-record-meta { display:block; color:#526985 !important; font-family:'Montserrat',sans-serif !important; font-size:12px !important; font-weight:500 !important; line-height:1.45; margin-top:2px !important; }
        .dev-status { display:inline-flex; align-items:center; gap:6px; border-radius:8px; padding:6px 10px; font-family:'Montserrat',sans-serif; font-size:12px; font-weight:700; white-space:nowrap; background:#eaf3ff; color:#1155cc; }
        .dev-status-wrap { display:flex !important; align-items:center !important; justify-content:center !important; width:100% !important; }
        .dev-operation { justify-content:center !important; width:100% !important; text-align:center !important; }
        .dev-status-check { font-size:14px; font-weight:900; }
        .dev-status-ok { background:#d9f9d4; color:#087b55; }
        .dev-status-cancel { background:#fff0f0; color:#bd3e45; }
        .dev-operation { display:flex; align-items:center; gap:8px; color:#243b60; font-family:'Montserrat',sans-serif; font-size:13px; font-weight:600; white-space:nowrap; }
        .dev-operation span { color:#075bea; font-size:18px; font-weight:800; }
        .dev-quantity-wrap { display:flex !important; align-items:center !important; justify-content:center !important; width:100% !important; min-width:0 !important; text-align:center !important; }\n        .dev-quantity { display:block !important; width:100% !important; color:#172b4d !important; font-family:'Montserrat',sans-serif !important; font-size:16px !important; font-weight:800 !important; text-align:center !important; }
        .dev-row-divider { height:1px; background:#dce5f0; margin:0 2px 10px; }
        div[data-testid="stVerticalBlockBorderWrapper"] { border:1px solid #cfdced !important; border-radius:12px !important; background:#fff !important; }
        div[data-testid="stVerticalBlockBorderWrapper"] > div { padding:12px 14px !important; }
        div[data-testid="stDownloadButton"] button { border:1px solid #075bea !important; border-radius:10px !important; font-family:'Montserrat',sans-serif !important; font-weight:700 !important; color:#17345f !important; background:#fff !important; white-space:nowrap !important; padding:7px 12px !important; }
        div[data-testid="stDownloadButton"] button:hover { border-color:#1155cc !important; color:#1155cc !important; background:#f5f9ff !important; }
        hr.sb-sep { border-color:#d8e7f8 !important; margin:22px 0 !important; }
        
        /* Painel Nova devolução — mais respiro, alinhamento e leitura */
        .st-key-dev-new-panel {
            box-sizing:border-box !important;
            width:100% !important;
            border:2px solid #4b8cff !important;
            border-radius:16px !important;
            padding:16px 18px 18px !important;
            margin:16px 0 20px !important;
            background:#ffffff !important;
            box-shadow:0 4px 13px rgba(7,93,229,.08) !important;
        }
        .st-key-dev-new-panel, .st-key-dev-new-panel * {
            font-weight:800 !important;
        }
        .st-key-dev-new-panel .dev-new-title {
            min-height:66px !important;
            box-sizing:border-box !important;
            padding:10px 16px !important;
            margin:0 0 14px !important;
            border:1px solid #c6dcff !important;
            border-radius:12px !important;
            background:linear-gradient(100deg,#eaf3ff 0%,#f5f9ff 65%,#e1edff 100%) !important;
            box-shadow:none !important;
            gap:12px !important;
        }
        .st-key-dev-new-panel .dev-section-icon {
            width:40px !important;
            height:40px !important;
            flex-basis:40px !important;
            border-radius:10px !important;
            font-size:25px !important;
        }
        .st-key-dev-new-panel .dev-new-title-copy { gap:3px !important; }
        .st-key-dev-new-panel .dev-new-title-copy strong {
            font-size:23px !important;
            line-height:1.2 !important;
            font-weight:800 !important;
            color:#103e79 !important;
        }
        .st-key-dev-new-panel .dev-new-title-copy small {
            font-size:13px !important;
            line-height:1.3 !important;
            font-weight:800 !important;
            color:#52739b !important;
        }
        /* O caminhão foi removido para manter o cabeçalho limpo. */
        .st-key-dev-new-panel div[data-testid="stForm"] {
            border:0 !important;
            border-radius:0 !important;
            padding:2px 3px 1px !important;
            margin:0 !important;
            background:transparent !important;
            box-shadow:none !important;
        }
        .st-key-dev-new-panel div[data-testid="stForm"] [data-testid="stVerticalBlock"] {
            gap:14px !important;
        }
        .st-key-dev-new-panel [class*="st-key-dev-qtd-"] {
            box-sizing:border-box !important;
            min-height:58px !important;
            padding:8px 11px !important;
            border:1px solid #cfe0ff !important;
            border-radius:11px !important;
            background:linear-gradient(100deg,#f3f7ff,#fbfdff) !important;
            box-shadow:0 2px 6px rgba(23,75,136,.06) !important;
            display:flex !important;
            align-items:center !important;
            justify-content:center !important;
        }
        .st-key-dev-new-panel [class*="st-key-dev-qtd-"] [data-testid="stHorizontalBlock"] {
            gap:10px !important;
            align-items:center !important;
        }
        .st-key-dev-new-panel .dev-qty-head {
            min-height:42px !important;
            gap:10px !important;
            align-items:center !important;
            justify-content:center !important;
            transform:translateY(-7px) !important;
            width:100% !important;
        }
        .st-key-dev-new-panel [class*="st-key-dev-qtd-"] [data-testid="stHorizontalBlock"] > div:first-child {
            display:flex !important;
            align-items:center !important;
            justify-content:center !important;
        }
        .st-key-dev-new-panel .dev-qty-title {
            align-items:flex-start !important;
            text-align:left !important;
        }
        .st-key-dev-new-panel .dev-qty-icon {
            width:34px !important;
            height:34px !important;
            flex-basis:34px !important;
            padding:6px !important;
            border-radius:9px !important;
        }
        .st-key-dev-new-panel .dev-qty-title {
            display:flex !important;
            flex-direction:column !important;
            justify-content:center !important;
            gap:3px !important;
        }
        .st-key-dev-new-panel .dev-qty-title strong {
            font-size:16px !important;
            line-height:1.2 !important;
            font-weight:800 !important;
            text-align:left !important;
        }
        .st-key-dev-new-panel .dev-qty-title small {
            font-size:13px !important;
            line-height:1.2 !important;
            font-weight:800 !important;
            text-align:left !important;
        }
        .st-key-dev-new-panel [class*="st-key-dev-qtd-"] div[data-testid="stNumberInput"] input {
            height:38px !important;
            min-height:38px !important;
            font-size:28px !important;
            font-weight:800 !important;
            text-align:center !important;
        }
        .st-key-dev-new-panel .dev-field-label {
            display:block !important;
            width:100% !important;
            font-size:18px !important;
            line-height:1.3 !important;
            font-weight:800 !important;
            text-align:left !important;
            margin:5px 0 8px !important;
            padding-left:2px !important;
            color:#123b6c !important;
        }
        .st-key-dev-new-panel [class*="st-key-dev-plate-field"],
        .st-key-dev-new-panel [class*="st-key-dev-observation-field"] {
            border:1px solid #c9dcff !important;
            border-radius:11px !important;
            background:#fff !important;
            overflow:hidden !important;
            min-height:46px !important;
            display:flex !important;
            align-items:center !important;
        }
        .st-key-dev-new-panel .dev-input-icon {
            min-height:42px !important;
            height:42px !important;
            display:flex !important;
            align-items:center !important;
            justify-content:center !important;
        }
        .st-key-dev-new-panel .dev-input-icon svg {
            width:21px !important;
            height:21px !important;
        }
        .st-key-dev-new-panel div[data-testid="stTextInput"] input,
        .st-key-dev-new-panel div[data-testid="stTextArea"] textarea {
            font-size:17px !important;
            font-weight:800 !important;
            border-radius:8px !important;
            text-align:left !important;
        }
        .st-key-dev-new-panel div[data-testid="stTextInput"] input {
            min-height:40px !important;
            height:40px !important;
        }
        .st-key-dev-new-panel div[data-testid="stTextArea"] textarea {
            min-height:58px !important;
            height:58px !important;
            padding-top:10px !important;
        }
        .st-key-dev-new-panel div[data-testid="stFormSubmitButton"] {
            display:flex !important;
            justify-content:center !important;
            margin-top:4px !important;
        }
        .st-key-dev-new-panel div[data-testid="stFormSubmitButton"] button {
            min-height:44px !important;
            height:44px !important;
            padding:8px 24px !important;
            border-radius:10px !important;
            font-size:17px !important;
            font-weight:800 !important;
            box-shadow:0 3px 8px rgba(7,93,229,.18) !important;
        }
        @media (max-width:700px) {
            .st-key-dev-new-panel { padding:12px !important; }
            .st-key-dev-new-panel .dev-new-title-copy strong { font-size:21px !important; }
            .st-key-dev-new-panel .dev-new-title-copy small { font-size:12px !important; }
            .st-key-dev-new-panel .dev-field-label { font-size:13px !important; }
        }
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

    titulo_saldo = "Saldo a devolver" + ("" if eh_gdl else f" — {escolha_mes}")
    icone_caixa_titulo = "<svg viewBox='0 0 48 48' aria-hidden='true'><path d='m6 15 18-9 18 9v20L24 44 6 35Z' fill='none' stroke='currentColor' stroke-width='3' stroke-linejoin='round'/><path d='m6 15 18 10 18-10M24 25v19M16 10l18 10' fill='none' stroke='currentColor' stroke-width='3' stroke-linejoin='round'/></svg>"
    st.markdown(f"<div class='dev-balance-section-title'>{icone_caixa_titulo}<span>{titulo_saldo}</span></div>", unsafe_allow_html=True)
    pr = dp.precos()
    icones_saldo = {
        "gaylord": "<svg viewBox='0 0 48 48' aria-hidden='true'><path d='M7 15 24 6l17 9v19L24 43 7 34Z' fill='none' stroke='currentColor' stroke-width='2.8' stroke-linejoin='round'/><path d='m7 15 17 10 17-10M24 25v18M16 10l17 10M32 10 15 20' fill='none' stroke='currentColor' stroke-width='2.6' stroke-linejoin='round'/></svg>",
        "pallet": "<svg viewBox='0 0 48 48' aria-hidden='true'><path d='m5 17 19-10 19 10-19 10Z M5 25l19 10 19-10M5 33l19 10 19-10' fill='none' stroke='currentColor' stroke-width='2.8' stroke-linejoin='round'/><path d='M10 18v7m28-7v7' fill='none' stroke='currentColor' stroke-width='2.4' stroke-linecap='round'/></svg>",
        "saca": "<svg viewBox='0 0 48 48' aria-hidden='true'><path d='M18 7c2 4 10 4 12 0M18 7l-2 7c-5 4-8 11-8 20 0 5 7 7 16 7s16-2 16-7c0-9-3-16-8-20l-2-7M16 14h16' fill='none' stroke='currentColor' stroke-width='2.8' stroke-linecap='round' stroke-linejoin='round'/></svg>",
    }
    cols = st.columns(max(len(saldo), 1), gap="large")
    for i, (_, r) in enumerate(saldo.iterrows()):
        tipo = r["tipo"]
        tipo_chave = str(tipo).strip().lower()
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
            icone = icones_saldo.get(tipo_chave, icones_saldo["gaylord"])
            st.markdown(
                f"""
                <div class="dev-balance-card" title="{ajuda}">
                    <div class="dev-balance-top">
                        <div class="dev-balance-icon">{icone}</div>
                        <div class="dev-balance-divider"></div>
                        <div class="dev-balance-info">
                            <div class="dev-balance-label">{str(tipo).upper()}</div>
                            <div class="dev-balance-qty">{_fmt(qtd_saldo)}</div>
                        </div>
                    </div>
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
        icone_moedas = "<svg viewBox='0 0 64 64' aria-hidden='true'><ellipse cx='22' cy='18' rx='15' ry='7' fill='none' stroke='currentColor' stroke-width='4'/><path d='M7 18v9c0 4 7 7 15 7 3 0 6-.5 8-1.5M7 27c0 4 7 7 15 7 3 0 6-.5 8-1.5M7 36c0 4 7 7 15 7 5 0 9-1.5 12-4' fill='none' stroke='currentColor' stroke-width='4' stroke-linecap='round'/><ellipse cx='43' cy='9' rx='13' ry='6' fill='none' stroke='currentColor' stroke-width='4'/><path d='M30 9v8c0 3 6 6 13 6 7 0 13-3 13-6V9M30 17v8c0 3 6 6 13 6 7 0 13-3 13-6v-8M30 25v8c0 3 6 6 13 6 7 0 13-3 13-6v-8' fill='none' stroke='currentColor' stroke-width='4' stroke-linecap='round'/></svg>"
        st.markdown(
            f"<div class='dev-total-banner'><span class='dev-total-icon'>{icone_moedas}</span><span class='dev-total-label'>Valor total a devolver</span><strong>{dp.fmt_brl(total_val)}</strong></div>",
            unsafe_allow_html=True,
        )

    st.markdown("<hr class='sb-sep' style='border-top-color:#e6e6e6;'>", unsafe_allow_html=True)

    # ---- Nova devolução ----
    if eh_gdl:
        _minhas_devolucoes(destino, eh_admin=False, eh_gdl=True)
        return

    with st.container(key="dev-new-panel"):
        st.markdown("""<div class="dev-new-title"><span class="dev-section-icon">＋</span><span class="dev-new-title-copy"><strong>Nova devolução</strong><small>Registre uma nova devolução de insumos</small></span></div>""", unsafe_allow_html=True)
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
                        obs = st.text_area("Observação", placeholder="Informe alguma particularidade desta devolução...", height=38, label_visibility="collapsed")
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
                f"<div class='dev-status-wrap'><span class='dev-status {status_class}'>"
                f"<span class='dev-status-check'>✓</span>{status_txt}</span></div>",
                unsafe_allow_html=True,
            )
            operacao = str(d.get("placa") or "").strip()
            c3.markdown(
                f"<div class='dev-operation'><span>🚚</span>{operacao or '—'}</div>",
                unsafe_allow_html=True,
            )
            c4.markdown(
                f"<div class='dev-quantity-wrap' style='display:flex;justify-content:center;align-items:center;width:100%;text-align:center;'>"
                f"<span class='dev-quantity' style='display:block;width:100%;text-align:center;margin:0 auto;'>{_fmt(d['total_declarado'])}</span></div>",
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
