"""
portal_admin.py — Portal do administrador (Gestão de Materiais), visual novo.

Layout no padrão do protótipo aprovado: menu lateral branco com seções
(OPERAÇÃO / GESTÃO / SUPORTE), barra superior com trilha, busca, aviso e
usuário; conteúdo em cartões claros com azul Loggi.

Telas novas (só leitura, leves): Início, Retornos e romaneios, Indicadores e
Bases. As telas que GRAVAM dados (receber devolução, devolução manual,
conciliação/fechamento, cobranças, usuários, configurações) reaproveitam as
páginas existentes, para não mexer em regra de negócio.
"""

from __future__ import annotations

import base64
import functools
import html
import os
import re

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import contato
import data_extraction as dados
import data_processing as dp
import manual
import romaneio

CHAVE = "adm_pagina"
CHAVE_SUB = "adm_sub"
CHAVE_BUSCA = "adm_busca"

MENU = [
    ("Operação", [
        ("Envios", ":material/local_shipping:"),
        ("Devoluções", ":material/assignment_return:"),
        ("Recebimentos", ":material/inbox:"),
    ]),
    ("Gestão", [
        ("Pendências", ":material/pending_actions:"),
        ("Cobranças", ":material/receipt_long:"),
        ("Bases e usuários", ":material/store:"),
        ("Configurações", ":material/settings:"),
    ]),
    ("Suporte", [
        ("Manual e ajuda", ":material/help:"),
    ]),
]
PAGINAS = [p for _, itens in MENU for p, _ in itens]

# O mesmo portal atende Admin, GDL e Leve (operação); muda o que cada um vê.
#  - GDL: todas as bases, sem Recebimentos/Configurações; não registra devolução
#    nem fecha cobrança; cadastra apenas usuários de operação.
#  - Leve: só a própria base (filtro de operação fixo) e registra as devoluções dela.
PAGINAS_PERFIL = {
    "gdl": {"Envios", "Devoluções", "Pendências", "Cobranças", "Bases e usuários", "Manual e ajuda"},
    "operacao": {"Envios", "Devoluções", "Pendências", "Cobranças", "Manual e ajuda"},
}
PAPEL_PERFIL = {"admin": "Gestão de Materiais", "gdl": "GDL"}


def _usuario() -> dict:
    return st.session_state.get("usuario") or {}


def _perfil() -> str:
    p = str(_usuario().get("perfil", "")).strip().lower()
    return p if p in ("admin", "gdl") else "operacao"


def _eh_admin() -> bool:
    return _perfil() == "admin"


def _minha_base() -> str | None:
    """Sigla da base do usuário Leve; None para Admin e GDL (veem todas)."""
    if _perfil() != "operacao":
        return None
    return str(_usuario().get("destino", "")).strip()


def _da_minha_base(df: pd.DataFrame, col: str = "destino") -> pd.DataFrame:
    """Para a Leve, mantém só as linhas da própria base; Admin/GDL: tudo."""
    base = _minha_base()
    if base is None or df.empty:
        return df
    alvo = dp._normalizar(base)
    return df[df[col].map(dp._normalizar) == alvo]


def _menu() -> list:
    permitidas = PAGINAS_PERFIL.get(_perfil())
    if permitidas is None:
        return MENU
    menu = [(sec, [(n, i) for n, i in itens if n in permitidas]) for sec, itens in MENU]
    return [(sec, itens) for sec, itens in menu if itens]

TIPOS = ["SACA", "GAYLORD", "PALLET"]
NOME = {"SACA": "Sacas", "GAYLORD": "Gaylords", "PALLET": "Pallets"}
COR = {"SACA": "#006aff", "GAYLORD": "#00baff", "PALLET": "#9cc3ff"}
STATUS = {
    "EM_TRANSITO": ("Em trânsito", "azul"),
    "RECEBIDO": ("Recebido", "verde"),
    "CONFERIDO": ("Conferido", "verde"),
    "DIVERGENTE": ("Divergente", "amarelo"),
    "CANCELADO": ("Cancelado", "cinza"),
}

_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--azul:#006aff;--azul-claro:#00baff;--azul-bg:#eaf3ff;--texto:#14213d;--texto-2:#66728a;--linha:#e6ebf3;
  --fundo:#f5f8fc;--verde:#0f7b5f;--verde-bg:#e3f6ee;--amarelo:#8a5a00;--amarelo-bg:#fdf0d5;--vermelho:#b42318;--vermelho-bg:#fdecea}
[data-testid="stApp"] *:not([data-testid="stIconMaterial"]):not(.material-symbols-rounded){font-family:Montserrat,sans-serif!important}
[data-testid="stApp"] [data-testid="stIconMaterial"]{font-family:"Material Symbols Rounded"!important;font-weight:400!important}
[data-testid="stApp"],[data-testid="stMain"],[data-testid="stAppViewContainer"]{background:#ffffff!important;color:var(--texto)}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"],[data-testid="stSidebarHeader"]{display:none!important}
[data-testid="stMainBlockContainer"]{max-width:100%!important;padding:22px 24px 60px 28px!important}
[data-testid="stApp"] input,[data-testid="stApp"] textarea,[data-testid="stApp"] button,[data-testid="stApp"] [data-baseweb="select"] *{font-family:Montserrat,sans-serif!important}
.ad-big{background:#fff;border:1px solid var(--linha);border-top:6px solid var(--azul);border-radius:20px;padding:22px 26px 20px;min-height:168px;box-sizing:border-box;display:flex;flex-direction:column}
.ad-big .v{font-size:46px;font-weight:800;color:#14213d;line-height:1;letter-spacing:-1px}
.ad-big .l{font-size:16px;font-weight:700;color:#14213d;margin-top:14px}
.ad-big .s{font-size:12.5px;font-weight:600;color:#6b7a90;margin-top:6px}
.ad-grade{max-height:640px;overflow:auto;border-radius:12px}
.ad-t2{width:100%;border-collapse:separate;border-spacing:0;font-size:14px}
.ad-t2 thead th{position:sticky;top:0;z-index:1;background:#f4f6fa;color:#5f6b7d;font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:16px 14px;text-align:center}
.ad-t2 thead th:first-child{text-align:left;border-radius:10px 0 0 0}.ad-t2 thead th:last-child{border-radius:0 10px 0 0}
.ad-t2 td{padding:14px;border-bottom:1px solid #edf0f5;text-align:center;color:#1f2a3d;font-variant-numeric:tabular-nums}
.ad-t2 td:first-child{text-align:left;font-weight:700;color:#14213d}
.ad-t2 td.b{font-weight:700}
.ad-t2,.ad-t2 th,.ad-t2 td,.ad-t2 tr{border-left:0!important;border-right:0!important;border-top:0!important;box-shadow:none!important}
.ad-t2 td{border-bottom:1px solid #edf0f5!important}.ad-t2 th{border-bottom:0!important}
.ad-t2 tr.tot td{border-top:2px solid #d9e2f0!important;border-bottom:0!important}
.ad-grade table{margin:0!important}
.ad-t2 tr.tot td{border-top:2px solid #d9e2f0;border-bottom:0;font-weight:800;background:#fafcff}
.st-key-ad-box-env-filtros label, .st-key-ad-box-env-filtros label *,.st-key-ad-box-env-filtros [data-baseweb='select'] *,.st-key-ad-box-env-filtros input{font-weight:700!important}
.st-key-ad-box-env-filtros [data-baseweb='select'] [aria-hidden] {font-weight:700!important}
.st-key-ad-env-limpar button{background:#e6f0ff!important;color:#0050c8!important;border:0!important;border-radius:999px!important;min-height:40px!important;font-weight:700!important;box-shadow:none!important}
.st-key-ad-env-limpar button p{white-space:nowrap!important;overflow:visible!important;text-overflow:clip!important}
.st-key-ad-env-limpar button *{color:#0050c8!important;-webkit-text-fill-color:#0050c8!important;font-weight:700!important;font-size:13px!important}
.st-key-ad-env-limpar button [data-testid='stIconMaterial']{font-size:17px!important}
.st-key-ad-env-limpar button:hover{background:#d6e7ff!important}
.ad-big.ad-big-destaque{background:#eef5ff;border-color:#d7e6ff;border-top-color:var(--azul)}
.ad-big.ad-big-destaque .v{color:#0050c8}
.rc-id{display:flex;align-items:center;gap:12px;font-size:22px;font-weight:800;color:#14213d;margin:0 0 14px}
.rc-meta{display:grid;grid-template-columns:2.2fr 1fr 1fr 1.4fr 1.2fr;background:#f4f6fa;border-radius:12px;padding:14px 18px;gap:12px}
.rc-l{font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#5f6b7d}
.rc-v{font-size:14.5px;font-weight:700;color:#14213d;margin-top:4px}
[class*='st-key-ad-rec-aceitar-'] button{background:#e6f0ff!important;color:#0050c8!important;border:0!important;border-radius:999px!important;min-height:42px!important;font-weight:700!important;box-shadow:none!important}
[class*='st-key-ad-rec-aceitar-'] button *{color:#0050c8!important;-webkit-text-fill-color:#0050c8!important;font-weight:700!important}
[class*='st-key-ad-rec-aceitar-'] button:hover{background:#d6e7ff!important}
.st-key-ad-box-rec-filtros label,.st-key-ad-box-rec-filtros label *,.st-key-ad-box-rec-filtros [data-baseweb='select'] *,.st-key-ad-box-rec-contar label,.st-key-ad-box-rec-contar label *{font-weight:700!important}
.st-key-ad-box-rec-contar input{font-size:15px!important;font-weight:700!important}
.st-key-ad-box-rec-contar [data-testid='stNumberInput']{max-width:220px}
.st-key-ad-box-rec-contar [data-testid='stNumberInput'] [data-baseweb='input']{min-height:34px!important;height:34px!important}
.st-key-ad-box-rec-contar [data-testid='stFormSubmitButton'] button{min-height:36px!important;height:36px!important;border-radius:999px!important;padding:0 18px!important;font-size:13px!important}
.st-key-ad-box-rec-contar [data-testid='stFormSubmitButton'] button *{font-size:13px!important}
.st-key-ad-box-rec-contar label p{font-size:13px!important}
[data-testid='stMain'] [data-testid='stSegmentedControl'] button{font-weight:700!important}
.ad-big .v.pd-v{font-size:clamp(24px,2.3vw,36px);white-space:nowrap}
.st-key-ad-box-pd-filtros + div .ad-big .l{white-space:nowrap}
.ad-big.pd-card{border-top-color:#f2a7a7}
.ad-big.pd-card.pd-card-destaque{background:#fff1f1;border-color:#f8d6d6;border-top-color:#f2a7a7}
.ad-big.pd-card.pd-card-destaque .v{color:#b42318}
.ad-pill.vermelho{background:#fdecea;color:#b42318}
.rk-lista{display:flex;flex-direction:column;gap:4px}
.rk{display:flex;align-items:center;gap:12px;padding:8px 4px;border-bottom:1px solid #edf0f5}.rk:last-child{border-bottom:0}
.rk-n{width:28px;height:28px;flex:0 0 28px;border-radius:50%;background:#eef2f7;color:#5f6b7d;font-size:12.5px;font-weight:800;display:flex;align-items:center;justify-content:center}
.rk:nth-child(-n+3) .rk-n{background:#fdecea;color:#b42318}
.rk-c{flex:1;min-width:0}
.rk-l{display:flex;align-items:baseline;gap:10px}
.rk-l b{font-size:14px;font-weight:800;color:#14213d;min-width:44px}
.rk-l span{font-size:12px;font-weight:600;color:#6b7a90;flex:1}
.rk-l em{font-style:normal;font-size:14px;font-weight:800;color:#14213d;white-space:nowrap}
.rk-b{height:6px;background:#f1f4f8;border-radius:999px;margin-top:6px;overflow:hidden}
.rk-b span{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,#00baff 25%,#006aff 75%)}
[class*='st-key-ad-dev-card-']{background:#fff;border:1px solid var(--linha);border-top:6px solid #f2a7a7;border-radius:20px;padding:18px 20px 14px!important;min-height:210px}
.st-key-ad-dev-card-total{min-height:0!important}
[data-testid='stHorizontalBlock']:has(.st-key-ad-dev-card-total){align-items:stretch!important}
[data-testid='stHorizontalBlock']:has(.st-key-ad-dev-card-total)>[data-testid='stColumn']>[data-testid='stVerticalBlock']{height:100%}
[data-testid='stHorizontalBlock']:has(.st-key-ad-dev-card-total)>[data-testid='stColumn']>[data-testid='stVerticalBlock']>[data-testid='stLayoutWrapper']{flex:1 1 auto;display:flex;flex-direction:column}
[data-testid='stHorizontalBlock']:has(.st-key-ad-dev-card-total) [class*='st-key-ad-dev-card-']{flex:1 1 auto;height:100%}
[class*='st-key-ad-dev-form-'] [data-testid='stHorizontalBlock']:first-of-type{align-items:stretch!important}
[class*='st-key-ad-dev-form-'] [data-testid='stColumn'] > [data-testid='stVerticalBlock']{height:100%}
.st-key-ad-dev-card-total{height:100%}
.dv-nome{font-size:13px;font-weight:800;letter-spacing:.06em;color:#14213d}
.dv-saldo{font-size:44px;font-weight:800;color:#b42318;line-height:1.05;margin-top:6px;letter-spacing:-1px}
.dv-saldo.zero{color:#0f7b5f}.dv-saldo.valor{font-size:clamp(24px,2.2vw,34px);white-space:nowrap}
.dv-sub{font-size:12px;font-weight:600;color:#6b7a90;margin:4px 0 10px}
.dv-ok{display:inline-block;background:#e3f6ee;color:#0f7b5f;border-radius:999px;padding:5px 12px;font-size:12px;font-weight:700}
[class*='st-key-ad-dev-card-'] input{font-size:20px!important;font-weight:800!important;text-align:center}
[class*='st-key-ad-dev-card-'] label p{font-weight:700!important;font-size:13px!important}
[class*='st-key-ad-dev-form-'] [data-testid='stFormSubmitButton'] button{min-height:52px!important;font-size:15px!important;padding:0 28px!important;border-radius:14px!important}
.st-key-ad-box-dev-filtros label,.st-key-ad-box-dev-filtros label *,.st-key-ad-box-dev-filtros [data-baseweb='select'] *{font-weight:700!important}
.st-key-ad-dev-cab{background:#f4f6fa;border-radius:10px;padding:0!important;min-height:44px;display:flex;align-items:center}
.st-key-ad-dev-cab > div{width:100%}
[class*='st-key-ad-dev-linha-'] [data-testid='stMarkdownContainer'],.st-key-ad-dev-cab [data-testid='stMarkdownContainer']{margin-bottom:0!important}
[class*='st-key-ad-dev-linha-'] [data-testid='stHorizontalBlock'],.st-key-ad-dev-cab [data-testid='stHorizontalBlock']{align-items:center!important}
[class*='st-key-ad-dev-linha-'] [data-testid='stColumn'],.st-key-ad-dev-cab [data-testid='stColumn']{display:flex;flex-direction:column;justify-content:center;align-items:center}
[class*='st-key-ad-dev-linha-']{min-height:64px;display:flex;align-items:center}
[class*='st-key-ad-dev-linha-'] > div{width:100%}
[class*='st-key-ad-dev-rom-'] [data-testid='stDownloadButton']{display:flex;justify-content:center;width:100%}
html body [data-testid='stMain'] [data-testid='stForm'] [data-testid='stTextInput'] label,html body [data-testid='stMain'] [data-testid='stForm'] [data-testid='stTextInput'] label *{font-weight:700!important;font-size:13.5px!important;color:#14213d!important}
[class*='st-key-ad-dev-form-'] [data-testid='stFormSubmitButton'] button *,html body [data-testid='stMain'] [data-testid='stForm'] [data-testid='stFormSubmitButton'] button p{font-weight:800!important}
.dv-sucesso{background:#e3f6ee;border:1px solid #bfe8d6;border-radius:14px;padding:14px 18px;color:#0b5e48}
.dv-sucesso b{display:block;font-size:16px;font-weight:800;color:#0f7b5f}
.dv-sucesso span{font-size:13.5px;font-weight:600}.dv-sucesso strong{font-weight:800;color:#0b5e48}
.st-key-ad-dev-ok{margin:6px 0 10px}
[class*='st-key-ad-dev-okrom-'] button{background:#0f7b5f!important;color:#fff!important;border:0!important;border-radius:999px!important;font-weight:700!important}
[class*='st-key-ad-dev-okrom-'] button *{color:#fff!important;-webkit-text-fill-color:#fff!important;font-weight:700!important}
.dv-vazio{background:#fdf0d5;border-radius:12px;padding:16px 18px;color:#7a4f00}
.dv-vazio b{display:block;font-size:15px;font-weight:800}.dv-vazio span{font-size:13px;font-weight:600}
.ad-tit .ad-mes{font-size:13px;padding:4px 12px;margin-left:4px}
.pd-faixa .ad-mes{padding:2px 10px;font-size:12.5px;background:#dde3ec;color:#33415c}
.dv-th{color:#5f6b7d;font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:0 6px;line-height:44px;text-align:center;width:100%}
.dv-td .ad-pill{display:inline-block;width:auto;max-width:fit-content}
[class*='st-key-ad-dev-linha-']{border-bottom:1px solid #edf0f5;padding:6px 0!important}
.dv-td{width:100%;text-align:center;font-size:14px;color:#1f2a3d}.dv-td b{font-weight:700}.dv-td span{display:block;font-size:12px;color:#6b7a90;font-weight:600}
[class*='st-key-ad-dev-rom-']{display:flex;justify-content:center}
[class*='st-key-ad-dev-rom-'] button{background:#e6f0ff!important;color:#0050c8!important;border:0!important;border-radius:999px!important;min-height:32px!important;height:32px!important;padding:0 14px!important;font-weight:700!important;box-shadow:none!important}
[class*='st-key-ad-dev-rom-'] button *{color:#0050c8!important;-webkit-text-fill-color:#0050c8!important;font-weight:700!important;font-size:12.5px!important}
[class*='st-key-ad-dev-rom-'] button:hover{background:#d6e7ff!important}
.st-key-ad-box-cb-filtros label,.st-key-ad-box-cb-filtros label *,.st-key-ad-box-cb-filtros [data-baseweb='select'] *{font-weight:700!important}
.st-key-ad-cb-limpar button,.st-key-ad-cb-xlsx button{background:#e6f0ff!important;color:#0050c8!important;border:0!important;border-radius:999px!important;min-height:36px!important;font-weight:700!important;box-shadow:none!important}
.st-key-ad-cb-limpar button *,.st-key-ad-cb-xlsx button *{color:#0050c8!important;-webkit-text-fill-color:#0050c8!important;font-weight:700!important;font-size:13px!important}
.st-key-ad-cb-limpar button p{white-space:nowrap!important}
.st-key-ad-cb-xlsx{margin-top:12px}.st-key-ad-cb-xlsx button{width:auto!important;min-height:32px!important;height:32px!important;padding:0 16px!important}
.cb-t td:first-child{text-align:center}.cb-t thead th:first-child{text-align:center}
.st-key-ad-us-busca label p,.st-key-ad-bases-busca label p{font-size:14px!important;font-weight:700!important}
.us-t{table-layout:fixed}.us-t td{font-size:13.5px;word-break:break-word}
.us-t th:nth-child(1),.us-t td:nth-child(1){width:30%;text-align:left}
.us-t th:nth-child(2),.us-t td:nth-child(2){width:10%}.us-t th:nth-child(3),.us-t td:nth-child(3){width:9%}
.us-t th:nth-child(4),.us-t td:nth-child(4){width:27%;font-size:12.5px;color:#5f6b7d}
.us-t th:nth-child(5),.us-t td:nth-child(5){width:12%}.us-t th:nth-child(6),.us-t td:nth-child(6){width:12%}
.st-key-ad-box-us-novo label p{font-weight:700!important;font-size:13px!important}
.st-key-ad-us-novo{padding-bottom:8px}.st-key-ad-us-novo p{font-weight:700!important}
.bs-t td:first-child,.bs-t thead th:first-child{text-align:center}
.bs-t td.bs-nome{font-weight:600}
[class*='st-key-ad-box-cfg-'] label p{font-weight:700!important;font-size:13px!important;color:#14213d!important}
[class*='st-key-ad-box-cfg-'] textarea{font-size:13.5px!important;line-height:1.6!important}
.ad-tit > div .ad-pill{margin-left:8px;vertical-align:middle}
.st-key-ad-box-aj{border-top:6px solid var(--azul)!important;border-radius:20px!important;padding:22px 24px!important}
.aj-cab{display:flex;align-items:center;gap:14px;margin-bottom:8px}
.aj-ic{width:48px;height:48px;border-radius:14px;background:var(--azul-bg);color:var(--azul);display:flex;align-items:center;justify-content:center;flex:0 0 48px}
.aj-ic span,.aj-ic .material-symbols-rounded{font-size:28px!important}
[class*='st-key-ct_anexo_'] [data-testid='stFileUploaderDropzoneInstructions'] span{display:none!important}
[class*='st-key-ct_anexo_'] [data-testid='stFileUploaderDropzoneInstructions']::after{content:'PNG ou JPG · até 3 imagens de 5 MB';font-size:12.5px;color:#6b7a90;font-weight:600}
.aj-cab b{display:block;font-size:20px;font-weight:800;color:#14213d}.aj-cab > div > span{font-size:13px;font-weight:600;color:#5f6b7d}
.aj-sla{margin-left:auto;background:#e3f6ee;color:#0f7b5f;font-weight:800;font-size:13px;border-radius:999px;padding:8px 14px;white-space:nowrap}
.aj-passo{display:flex;gap:12px;padding:12px 0;border-bottom:1px solid #edf0f5;font-size:13px;color:#5f6b7d;font-weight:600}.aj-passo:last-child{border-bottom:0}
.aj-passo > span{width:26px;height:26px;flex:0 0 26px;border-radius:50%;background:var(--azul-bg);color:var(--azul);font-weight:800;display:flex;align-items:center;justify-content:center}
.aj-passo b{display:block;color:#14213d;font-size:14px;font-weight:800;margin-bottom:2px}.aj-passo b.az{display:inline;color:var(--azul)}
.st-key-ad-box-aj label p{font-weight:700!important;font-size:13px!important}
.st-key-ad-manual button{background:#e6f0ff!important;color:#0050c8!important;border:0!important;border-radius:999px!important;font-weight:700!important}
.st-key-ad-manual button p{white-space:nowrap!important}
.st-key-ad-manual button *{color:#0050c8!important;-webkit-text-fill-color:#0050c8!important;font-weight:700!important}
.pd-faixa{border-radius:12px;padding:12px 16px;font-size:13.5px;font-weight:600;margin:6px 0 4px}
.pd-faixa.azul{background:#eaf3ff;color:#0050c8}.pd-faixa.amarelo{background:#fdf0d5;color:#7a4f00}.pd-faixa.verde{background:#e3f6ee;color:#0f7b5f}
.pd-ins{padding:12px 0;border-bottom:1px solid #edf0f5}.pd-ins:last-child{border-bottom:0}
.pd-ins-top{display:flex;justify-content:space-between;font-size:14px;color:#14213d}.pd-ins-top span{font-weight:700}
.pd-barra{height:8px;background:#eef2f7;border-radius:999px;margin:8px 0 6px;overflow:hidden}.pd-barra span{display:block;height:100%;background:#0a6cff;border-radius:999px}
.pd-ins-sub{font-size:12.5px;color:#5f6b7d;font-weight:600}
.st-key-ad-box-pd-filtros label,.st-key-ad-box-pd-filtros label *,.st-key-ad-box-pd-filtros [data-baseweb='select'] *{font-weight:700!important}
.st-key-ad-pd-limpar button,.st-key-ad-pd-xlsx button{background:#e6f0ff!important;color:#0050c8!important;border:0!important;border-radius:999px!important;min-height:36px!important;font-weight:700!important;box-shadow:none!important}
.st-key-ad-pd-limpar button *,.st-key-ad-pd-xlsx button *{color:#0050c8!important;-webkit-text-fill-color:#0050c8!important;font-weight:700!important;font-size:13px!important}
.st-key-ad-pd-limpar button p{white-space:nowrap!important}
.st-key-ad-pd-xlsx{margin-top:12px}.st-key-ad-pd-xlsx button{width:auto!important;min-height:32px!important;height:32px!important;padding:0 16px!important}
.st-key-ad-env-xlsx{margin-top:12px}
.st-key-ad-env-xlsx button{background:#e6f0ff!important;color:#0050c8!important;border:0!important;border-radius:999px!important;min-height:32px!important;height:32px!important;padding:0 16px!important;font-size:13px!important;font-weight:700!important;box-shadow:none!important;width:auto!important}
.st-key-ad-env-xlsx button *{color:#0050c8!important;-webkit-text-fill-color:#0050c8!important;font-size:13px!important;font-weight:700!important}
.st-key-ad-env-xlsx button [data-testid='stIconMaterial']{font-size:16px!important}
.st-key-ad-env-xlsx button:hover{background:#d6e7ff!important}
[data-baseweb='popover'] *:not([data-testid='stIconMaterial']),[data-baseweb='tag'] *,[data-baseweb='menu'] *{font-family:Montserrat,sans-serif!important}
.js-plotly-plot .plotly text{font-family:Montserrat,sans-serif!important}
.ad-mes{display:inline-block;background:#e6f0ff;color:#0050c8;font-weight:700;font-size:13px;border-radius:999px;padding:7px 16px}
section[data-testid="stSidebar"]{width:248px!important;min-width:248px!important;max-width:248px!important;transform:none!important;visibility:visible!important}
section[data-testid="stSidebar"]>div:first-child{background:#fff!important;border-right:1px solid var(--linha);padding:18px 12px!important}
.material-symbols-rounded{font-family:"Material Symbols Rounded"!important;font-weight:400;font-style:normal;line-height:1;letter-spacing:normal;text-transform:none;white-space:nowrap;-webkit-font-feature-settings:'liga';font-feature-settings:'liga'}
.ad-logo{text-align:center;margin:30px 0 14px}
.ad-logo img{height:30px}
.ad-logo div{font-size:13px;font-weight:600;color:var(--texto);margin-top:2px}
.ad-sec{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#8d98ab;padding:16px 10px 4px;line-height:1.2}
.ad-rodape{height:1px;background:var(--linha);margin:18px 6px 8px}
[data-testid="stSidebar"] [data-testid="stButton"] button{justify-content:flex-start!important;border:0!important;background:transparent!important;
  color:#33415c!important;font-weight:500!important;font-size:13.5px!important;min-height:36px!important;height:36px;border-radius:9px!important;box-shadow:none!important;padding:0 10px!important}
[data-testid="stSidebar"] [data-testid="stButton"] button>div{justify-content:flex-start!important;width:100%;gap:10px}
[data-testid="stSidebar"] [data-testid="stButton"] button p{text-align:left!important}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover{background:var(--fundo)!important;color:var(--texto)!important}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"]{background:var(--azul-bg)!important;color:var(--azul)!important;font-weight:600!important}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] *{color:var(--azul)!important}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:2px!important}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"]{margin-bottom:0!important}
.ad-trilha{font-size:13px;color:var(--texto-2);padding-top:9px}
.ad-trilha b{color:var(--azul);font-weight:600}
.ad-user{display:flex;align-items:center;justify-content:flex-end;gap:12px;padding-top:2px}
.ad-user-menu{justify-content:flex-start;padding:4px 10px 10px}
.ad-sino{position:relative;color:var(--texto-2);font-size:13px;display:flex;align-items:center;gap:4px}
.ad-sino .n{background:var(--vermelho);color:#fff;border-radius:999px;font-size:10px;font-weight:700;padding:1px 6px}
.ad-av{width:34px;height:34px;border-radius:50%;background:var(--azul);color:#fff;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700}
.ad-nome{font-size:12.5px;font-weight:600;color:var(--texto);line-height:1.2}
.ad-nome span{display:block;font-weight:400;color:var(--texto-2);font-size:11.5px}
.ad-topo-linha{height:1px;background:var(--linha);margin:8px 0 18px}
.ad-h1{font-size:24px;font-weight:700;color:var(--texto);margin:0 0 2px}
.ad-sub{font-size:13.5px;color:var(--texto-2);margin:0 0 18px}
.ad-card{background:#fff;border:1px solid var(--linha);border-radius:14px;padding:16px 18px}
.ad-kpi{display:flex;gap:12px;align-items:flex-start}
.ad-kpi .ic{width:38px;height:38px;border-radius:10px;background:var(--azul-bg);color:var(--azul);display:flex;align-items:center;justify-content:center;font-size:20px;flex:0 0 38px}
.ad-kpi .l{font-size:12.5px;color:var(--texto-2)}
.ad-kpi .v{font-size:24px;font-weight:700;color:var(--texto);line-height:1.15;margin:2px 0}
.ad-tag{display:inline-block;border-radius:6px;padding:2px 7px;font-size:11.5px;font-weight:600}
.ad-tag.up{background:var(--verde-bg);color:var(--verde)}.ad-tag.down{background:var(--vermelho-bg);color:var(--vermelho)}
.ad-tag.neu{background:var(--fundo);color:var(--texto-2)}.ad-tag.warn{background:var(--amarelo-bg);color:var(--amarelo)}
.ad-tit{font-size:15px;font-weight:600;color:var(--texto);margin:0 0 8px;display:flex;align-items:center;justify-content:space-between}
.ad-tit span{font-size:12px;font-weight:400;color:var(--texto-2)}
[class*="st-key-ad-box-"]{background:#fff;border:1px solid var(--linha);border-radius:14px;padding:16px 18px!important}
[class*="st-key-ad-acao-"] [data-testid="stButton"] button{justify-content:space-between!important;width:100%;background:#fff!important;border:1px solid var(--linha)!important;
  color:var(--texto)!important;border-radius:10px!important;min-height:44px!important;font-weight:500!important}
[class*="st-key-ad-acao-"] [data-testid="stButton"] button:hover{border-color:var(--azul)!important;color:var(--azul)!important}
[class*="st-key-ad-acao-"] [data-testid="stButton"] button>div{justify-content:flex-start!important;width:100%;gap:10px}
.ad-tab{width:100%;border-collapse:collapse;font-size:13px}
.ad-tab th{text-align:left;font-size:11.5px;font-weight:600;color:var(--texto-2);padding:9px 10px;background:var(--fundo);border-bottom:1px solid var(--linha)}
.ad-tab td{padding:10px;border-bottom:1px solid var(--linha);color:var(--texto)}
.ad-tab tr:last-child td{border-bottom:0}
.ad-tab td.n,.ad-tab th.n{text-align:right;font-variant-numeric:tabular-nums}
.ad-pill{display:inline-block;border-radius:999px;padding:3px 10px;font-size:11.5px;font-weight:600;white-space:nowrap}
.ad-pill.azul{background:var(--azul-bg);color:#0050c8}.ad-pill.verde{background:var(--verde-bg);color:var(--verde)}
.ad-pill.amarelo{background:var(--amarelo-bg);color:var(--amarelo)}.ad-pill.cinza{background:#eef0f3;color:#5b6472}
.ad-vazio{font-size:13px;color:var(--texto-2);padding:14px 0}
[data-testid="stMain"] [data-testid="stButton"] button[kind="primary"],[data-testid="stMain"] [data-testid="stFormSubmitButton"] button,
[data-testid="stMain"] [data-testid="stDownloadButton"] button[kind="primary"]{background:var(--azul)!important;border:0!important;color:#fff!important;border-radius:10px!important;font-weight:600!important}
[data-testid="stMain"] [data-testid="stButton"] button[kind="primary"]:hover{background:#0057d1!important}
.ad-ajuda{display:flex;gap:14px}
.ad-ajuda .ic{width:44px;height:44px;border-radius:12px;background:var(--azul-bg);color:var(--azul);display:flex;align-items:center;justify-content:center;font-size:24px;flex:0 0 44px}
.ad-ajuda b{font-size:15px;color:var(--texto)}.ad-ajuda p{font-size:13px;color:var(--texto-2);margin:2px 0 10px}
</style>
"""



_CSS_MOLDURA = """
<style>
html body [data-testid="stApp"] .material-symbols-rounded,
html body [data-testid="stApp"] [data-testid="stIconMaterial"]{font-family:"Material Symbols Rounded"!important;font-weight:400!important}
html body section[data-testid="stSidebar"] [data-testid="stButton"] button{justify-content:flex-start!important;border:0!important;background:transparent!important;
  color:#33415c!important;font-weight:500!important;font-size:13.5px!important;min-height:36px!important;height:36px!important;border-radius:9px!important;box-shadow:none!important;padding:0 10px!important}
html body section[data-testid="stSidebar"] [data-testid="stButton"] button *{color:inherit!important;-webkit-text-fill-color:currentColor!important;font-size:13.5px!important;font-weight:inherit!important}
html body section[data-testid="stSidebar"] [data-testid="stButton"] button{-webkit-text-fill-color:currentColor!important}
html body section[data-testid="stSidebar"] [data-testid="stButton"] button p{white-space:nowrap!important;letter-spacing:normal!important;line-height:1.2!important}
html body [data-testid="stMain"] .ad-trilha,html body [data-testid="stMain"] .ad-nome,html body [data-testid="stMain"] .ad-sino{-webkit-text-fill-color:currentColor!important}
html body section[data-testid="stSidebar"] [data-testid="stButton"] button:hover{background:#f5f8fc!important;color:#14213d!important}
html body section[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"]{background:#eaf3ff!important;color:#006aff!important;font-weight:600!important}
html body section[data-testid="stSidebar"] [data-testid="stButton"] button [data-testid="stIconMaterial"]{font-size:18px!important}
html body section[data-testid="stSidebar"]>div:first-child{background:#fff!important}
</style>
"""
# ---------------------------------------------------------------------------
# utilidades
# ---------------------------------------------------------------------------

def _fmt(n) -> str:
    return f"{int(round(float(n or 0))):,}".replace(",", ".")


def _e(v) -> str:
    return html.escape(str(v))


def _md(h: str) -> None:
    st.markdown(h, unsafe_allow_html=True)


def _ir(pagina: str, sub: str | None = None) -> None:
    st.session_state[CHAVE] = pagina
    if sub is not None:
        st.session_state[CHAVE_SUB] = sub
    st.rerun()


@functools.lru_cache(maxsize=4)
def _img_b64(nome: str) -> str:
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), nome)
    if not os.path.exists(caminho):
        return ""
    with open(caminho, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _pill(status: str) -> str:
    rot, cls = STATUS.get(str(status).upper(), (str(status).title(), "cinza"))
    return f"<span class='ad-pill {cls}'>{_e(rot)}</span>"


def _kpi(icone: str, rotulo: str, valor: str, tag: str = "", tag_cls: str = "neu") -> str:
    t = f"<span class='ad-tag {tag_cls}'>{_e(tag)}</span>" if tag else ""
    return (f"<div class='ad-card ad-kpi'><div class='ic'>{icone}</div><div>"
            f"<div class='l'>{_e(rotulo)}</div><div class='v'>{valor}</div>{t}</div></div>")


# ícones em SVG simples (traço), sem baixar fonte extra
_IC = {
    "saca": "<svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M9 3c1 2 5 2 6 0M9 3 8 7c-3 2-4 6-4 10 0 3 4 4 8 4s8-1 8-4c0-4-1-8-4-10l-1-4M8 7h8'/></svg>",
    "caixa": "<svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linejoin='round'><path d='m12 3 8 4.5v9L12 21l-8-4.5v-9z'/><path d='m4 7.5 8 4.5 8-4.5M12 12v9'/></svg>",
    "retorno": "<svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M4 12a8 8 0 0 1 14-5.3L20 9M20 4v5h-5M20 12a8 8 0 0 1-14 5.3L4 15M4 20v-5h5'/></svg>",
    "dinheiro": "<svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round'><rect x='3' y='6' width='18' height='12' rx='2'/><circle cx='12' cy='12' r='2.5'/></svg>",
    "taxa": "<svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round'><path d='M4 20 20 4'/><circle cx='7' cy='7' r='2.5'/><circle cx='17' cy='17' r='2.5'/></svg>",
}


def _cabecalho(titulo: str, sub: str) -> None:
    _md(f"<div class='ad-h1'>{_e(titulo)}</div><div class='ad-sub'>{_e(sub)}</div>")


def _layout_plotly(fig: go.Figure, altura: int = 260) -> go.Figure:
    fig.update_layout(
        height=altura, margin=dict(l=6, r=6, t=6, b=6), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Montserrat, sans-serif", size=11, color="#66728a"),
        legend=dict(orientation="h", y=1.12, x=1, xanchor="right", font=dict(size=11)),
        hoverlabel=dict(font_family="Montserrat"),
        separators=",.",  # formato brasileiro: 3.500 e 12,5
    )
    fig.update_xaxes(showgrid=False, linecolor="#e6ebf3")
    fig.update_yaxes(gridcolor="#eef2f7", zeroline=False)
    return fig


# ---------------------------------------------------------------------------
# dados (todos derivados das funções já em cache do data_processing)
# ---------------------------------------------------------------------------

def _retornos() -> pd.DataFrame:
    """Uma linha por devolução, com quantidades declaradas por tipo."""
    devs = dp.devolucoes_df()
    if devs.empty:
        return devs
    its = dp.itens_df()
    df = devs.copy()
    if not its.empty:
        piv = its.pivot_table(index="id_devolucao", columns="tipo", values="qtd_declarada",
                              aggfunc="sum", fill_value=0)
        df = df.merge(piv, left_on="id", right_index=True, how="left")
    for t in TIPOS:
        df[t] = pd.to_numeric(df[t], errors="coerce").fillna(0).astype(int) if t in df.columns else 0
    df["qtd"] = df[TIPOS].sum(axis=1)
    return df.sort_values("dt_criacao", ascending=False)


def _recebidos() -> pd.DataFrame:
    """Itens efetivamente recebidos no CD: tipo, q, dt, destino."""
    devs, its = dp.devolucoes_df(), dp.itens_df()
    if devs.empty or its.empty:
        return pd.DataFrame(columns=["tipo", "q", "dt", "destino"])
    d = devs[devs["status"].isin(dp.STATUS_RECEBIDOS)].copy()
    d["dt"] = d["dt_recebimento"].fillna(d["dt_criacao"])
    it = its.merge(d[["id", "dt", "destino"]], left_on="id_devolucao", right_on="id")
    it["q"] = pd.to_numeric(it["qtd_recebida"], errors="coerce").fillna(it["qtd_declarada"]).clip(lower=0)
    return it[["tipo", "q", "dt", "destino"]]


def _pendentes() -> pd.DataFrame:
    p = dp.pendencias_df()
    if p.empty:
        return p
    pr = dp.precos()
    p = p.copy()
    p["valor"] = p["pendente"] * p["tipo"].map(lambda t: float(pr.get(t, 0) or 0))
    return p


# ---------------------------------------------------------------------------
# moldura: menu lateral + barra superior
# ---------------------------------------------------------------------------

def _sidebar(user: dict, pagina: str, logout) -> None:
    with st.sidebar:
        logo = _img_b64("image_logo_loggi_azul.png")
        img = f'<img src="data:image/png;base64,{logo}" alt="Loggi">' if logo else "Loggi"
        _md(f"<div class='ad-logo'>{img}</div>")
        for secao, itens in _menu():
            _md(f"<div class='ad-sec'>{_e(secao)}</div>")
            for nome, icone in itens:
                if st.button(nome, icon=icone, key=f"ad-nav-{nome}", width="stretch",
                             type="primary" if nome == pagina else "secondary"):
                    st.session_state.pop(CHAVE_SUB, None)
                    _ir(nome)
        _md("<div class='ad-rodape'></div>")
        nome = str(user.get("nome", "")).strip()
        ini = "".join(x[0] for x in nome.split()[:2]).upper() or "?"
        papel = PAPEL_PERFIL.get(_perfil()) or f"Base {user.get('destino', '')}"
        _md(f"<div class='ad-user ad-user-menu'><div class='ad-av'>{_e(ini)}</div><div class='ad-nome'>{_e(nome)}"
            f"<span>{_e(papel)}</span></div></div>")
        if st.button("Atualizar dados", icon=":material/refresh:", key="ad-atualizar", width="stretch"):
            dados.limpar_cache()
            st.rerun()
        if st.button("Sair", icon=":material/logout:", key="ad-sair", width="stretch"):
            st.session_state.pop(CHAVE, None)
            logout()
            st.rerun()


def _barra_topo(user: dict, pagina: str, logout) -> None:
    c1, c2, c3 = st.columns([1.3, 1.6, 1.3], vertical_alignment="center")
    c1.markdown(f"<div class='ad-trilha'>Portal Leves / <b>{_e(pagina)}</b></div>", unsafe_allow_html=True)
    busca = c2.text_input("Buscar", placeholder="Buscar movimentação, base ou romaneio",
                          label_visibility="collapsed", key="ad-busca-in", icon=":material/search:")
    if busca and busca != st.session_state.get("_ad_busca_ultima"):
        st.session_state["_ad_busca_ultima"] = busca
        st.session_state[CHAVE_BUSCA] = busca
        _ir("Retornos e romaneios")
    nome = str(user.get("nome", "")).strip()
    ini = "".join(p[0] for p in nome.split()[:2]).upper() or "?"
    with c3:
        st.markdown(
            f"<div class='ad-user'><div class='ad-av'>{_e(ini)}</div><div class='ad-nome'>{_e(nome.split(' ')[0])}"
            f"<span>Gestão de Materiais</span></div></div>", unsafe_allow_html=True)
    _md("<div class='ad-topo-linha'></div>")


# ---------------------------------------------------------------------------
# 1. Início
# ---------------------------------------------------------------------------

def _inicio() -> None:
    hc1, hc2 = st.columns([3, 1], vertical_alignment="bottom")
    with hc1:
        _cabecalho("Visão geral", "Acompanhe as movimentações e retornos de sacas e gaylords.")
    periodo = hc2.selectbox("Período", ["Últimos 30 dias", "Últimos 60 dias", "Últimos 90 dias"],
                            label_visibility="collapsed", key="ad-ini-per")
    dias = int(re.search(r"\d+", periodo).group())

    pend = _pendentes()
    rec = _recebidos()
    agora = dp.agora_sp()
    ini_mes = agora.to_period("M").start_time
    ini_ant = (agora.to_period("M") - 1).start_time
    rec_mes = rec[rec["dt"] >= ini_mes]["q"].sum() if not rec.empty else 0
    rec_ant_mesmo_ponto = rec[(rec["dt"] >= ini_ant) & (rec["dt"] < ini_ant + (agora - ini_mes))]["q"].sum() if not rec.empty else 0
    var = ((rec_mes / rec_ant_mesmo_ponto - 1) * 100) if rec_ant_mesmo_ponto else None

    saca_ab = pend.loc[pend["tipo"] == "SACA", "pendente"].sum() if not pend.empty else 0
    gay_ab = pend.loc[pend["tipo"] == "GAYLORD", "pendente"].sum() if not pend.empty else 0
    custo = pend["valor"].sum() if not pend.empty else 0
    n_bases = pend["destino"].nunique() if not pend.empty else 0

    k = st.columns(4, gap="small")
    k[0].markdown(_kpi(_IC["saca"], "Sacas em aberto", _fmt(saca_ab), f"{n_bases} bases com saldo"), unsafe_allow_html=True)
    k[1].markdown(_kpi(_IC["caixa"], "Gaylords em aberto", _fmt(gay_ab), "+ mesmo nº de pallets"), unsafe_allow_html=True)
    tag = (f"{'+' if var >= 0 else ''}{var:.0f}% vs. mês anterior" if var is not None else "mês atual")
    k[2].markdown(_kpi(_IC["retorno"], "Retornados no mês", _fmt(rec_mes), tag,
                       "up" if var is not None and var >= 0 else ("down" if var is not None else "neu")), unsafe_allow_html=True)
    k[3].markdown(_kpi(_IC["dinheiro"], "Custo pendente", dp.fmt_brl(custo), "em aberto", "warn"), unsafe_allow_html=True)

    st.write("")
    g1, g2 = st.columns([2.2, 1], gap="medium")
    with g1, st.container(key="ad-box-mov"):
        env = dp.envios_df()
        corte = agora.normalize() - pd.Timedelta(days=dias - 1)
        e = env[(env["dt"] >= corte) & (env["tipo"].isin(["SACA", "GAYLORD"]))] if not env.empty else env
        _md(f"<div class='ad-tit'>Envios por dia (sacas e gaylords)<span>{_e(periodo.lower())}</span></div>")
        if e.empty:
            _md("<div class='ad-vazio'>Sem envios no período.</div>")
        else:
            serie = e.groupby([e["dt"].dt.normalize(), "tipo"])["total"].sum().unstack(fill_value=0)
            serie = serie.reindex(pd.date_range(corte, agora.normalize()), fill_value=0)
            fig = go.Figure()
            for t in ["SACA", "GAYLORD"]:
                if t in serie.columns:
                    fig.add_trace(go.Scatter(x=serie.index, y=serie[t], name=NOME[t], mode="lines",
                                             line=dict(color=COR[t], width=2.4, shape="spline"),
                                             fill="tozeroy" if t == "SACA" else None,
                                             fillcolor="rgba(0,106,255,.08)"))
            fig.update_xaxes(tickformat="%d %b")
            st.plotly_chart(_layout_plotly(fig, 250), width="stretch", config={"displayModeBar": False})
    with g2, st.container(key="ad-box-acoes"):
        _md("<div class='ad-tit'>Ações rápidas</div>")
        acoes = [
            ("Receber devoluções no CD", ":material/inbox:", "Recebimentos", None),
            ("Registrar devolução de uma base", ":material/assignment_return:", "Devolução", None),
            ("Consultar retornos e romaneios", ":material/assignment_return:", "Retornos e romaneios", None),
            ("Consultar bases", ":material/store:", "Bases e usuários", None),
        ]
        for i, (rot, ic, pag, sub) in enumerate(acoes):
            with st.container(key=f"ad-acao-{i}"):
                if st.button(rot, icon=ic, key=f"ad-acao-btn-{i}", width="stretch"):
                    _ir(pag, sub)

    st.write("")
    with st.container(key="ad-box-ult"):
        _md("<div class='ad-tit'>Últimos retornos<span>10 mais recentes</span></div>")
        _tabela_retornos(_retornos().head(10))


def _tabela_retornos(df: pd.DataFrame) -> None:
    if df.empty:
        _md("<div class='ad-vazio'>Nenhum retorno encontrado.</div>")
        return
    tem_local = "local_devolucao" in df.columns and df["local_devolucao"].astype(str).str.strip().ne("").any()
    linhas = []
    for _, r in df.iterrows():
        dt = r.get("dt_criacao")
        data = dt.strftime("%d/%m/%Y") if pd.notna(dt) else ""
        itens = " · ".join(f"{_fmt(r[t])} {NOME[t].lower()}" for t in TIPOS if r[t])
        local = str(r.get("local_devolucao") or "").split(" - ")[0].strip()
        linhas.append(
            f"<tr><td>{_e(data)}</td><td><b>{_e(r['id'])}</b></td><td>{_e(r['destino'])}</td>"
            + (f"<td>{('→ ' + _e(local)) if local else '—'}</td>" if tem_local else "") + f"<td>{_e(itens or '—')}</td><td class='n'>{_fmt(r['qtd'])}</td>"
            f"<td>{_pill(r['status'])}</td></tr>")
    cab_destino = "<th>Destino</th>" if tem_local else ""
    _md("<table class='ad-tab'><thead><tr><th>Data</th><th>Romaneio</th><th>Origem (base)</th>" + cab_destino
        + "<th>Material</th><th class='n'>Quantidade</th><th>Status</th></tr></thead><tbody>"
        + "".join(linhas) + "</tbody></table>")


# ---------------------------------------------------------------------------
# 2. Recebimentos (gravação pelas mesmas funções do page_4)
# ---------------------------------------------------------------------------

def _titulo_grande(titulo: str, sub: str) -> None:
    _md(f"<div class='ad-h1' style='font-size:27px;font-weight:700'>{_e(titulo)}</div>"
        f"<div class='ad-sub' style='font-weight:700'>{_e(sub)}</div>")


def _registrar(scan_id, scan_token) -> None:
    _titulo_grande("Recebimento de devoluções", "Receba no CD as devoluções que chegaram.")
    msg = st.session_state.pop("_ad_rec_msg", None)
    if msg:
        (st.warning if msg[0] == "aviso" else st.success)(msg[1])
    _receber(scan_id, scan_token)


def _receber(scan_id, scan_token) -> None:
    """Recebimento no CD — visual novo; gravação pelas mesmas funções do page_4."""
    from page_4 import _aguardando_recebimento, _confirmar

    user = st.session_state.get("usuario") or {}
    quem = user.get("nome", user.get("usuario", ""))
    devs = dp.devolucoes_df()
    if devs.empty:
        st.info("Nenhuma devolução registrada.")
        return

    # ---- Filtros ----
    with st.container(key="ad-box-rec-filtros"):
        lista = devs[devs.apply(lambda r: _aguardando_recebimento(r.to_dict()), axis=1)].sort_values("dt_criacao")
        if lista.empty:
            st.selectbox("Devoluções em trânsito", ["Nenhuma devolução em trânsito no momento"], disabled=True,
                         key="ad-rec-vazia")
            st.success("Nenhuma devolução aguardando recebimento.")
            return
        opcoes = {
            f"{r['id']} — {r['destino']} · {_fmt(r['total_declarado'])} itens · {STATUS.get(str(r['status']).upper(), (r['status'],))[0]}": r["id"]
            for _, r in lista.iterrows()
        }
        idx = 0
        if scan_id and scan_id in set(lista["id"].astype(str)):
            idx = list(opcoes.values()).index(scan_id)
        escolha = st.selectbox("Devoluções em trânsito", list(opcoes.keys()), index=idx, key="ad-rec-dev")

    dev = devs[devs["id"] == opcoes[escolha]].iloc[0].to_dict()
    if scan_id and dev["id"] == scan_id and scan_token and str(dev.get("token", "")) != scan_token:
        st.error("Token inválido para esta devolução. Verifique o QR.")
        return

    its = dp.itens_da_devolucao(dev["id"])
    ordem = {t: i for i, t in enumerate(TIPOS)}
    itens = sorted(({"tipo": str(r["tipo"]).upper(), "qtd_declarada": int(r["qtd_declarada"]),
                     "qtd_recebida": r.get("qtd_recebida")} for _, r in its.iterrows()),
                   key=lambda x: ordem.get(x["tipo"], 9))
    total_decl = sum(i["qtd_declarada"] for i in itens)
    aguardando = _aguardando_recebimento(dev)

    # ---- Cabeçalho da devolução ----
    comp = str(dev.get("competencia", "") or "")
    comp_txt = dp.rotulo_mes(comp) if len(comp) == 7 else "—"
    dt = dev.get("dt_criacao")
    emissao = dt.strftime("%d/%m/%Y %H:%M") if pd.notna(dt) else str(dev.get("data_criacao", ""))
    pill = (_pill("EM_TRANSITO").replace("Em trânsito", "Em conferência") if aguardando else _pill(dev.get("status")))
    meta = [("Operação", dev.get("usuario", "") or "—"), ("Destino", dev.get("destino", "") or "—"),
            ("Placa", dev.get("placa") or "—"), ("Emissão", emissao), ("Competência", comp_txt)]
    st.write("")
    with st.container(key="ad-box-rec-dev"):
        _md(f"<div class='rc-id'><span>{_e(dev['id'])}</span>{pill}</div>"
            "<div class='rc-meta'>" + "".join(
                f"<div><div class='rc-l'>{_e(l)}</div><div class='rc-v'>{_e(v)}</div></div>" for l, v in meta)
            + "</div>")
        if dev.get("local_devolucao"):
            st.caption(f"Local de devolução: {dev.get('local_devolucao')}")

    # ---- Já recebida: só consulta ----
    if not aguardando:
        quando = f" em {dev.get('data_recebimento', '')}" if dev.get("data_recebimento") else ""
        por = f" por {dev.get('recebido_por', '')}" if dev.get("recebido_por") else ""
        st.info(f"Esta devolução já foi recebida{quando}{por}.")
        linhas = "".join(
            f"<tr><td>{_e(NOME.get(i['tipo'], i['tipo']).upper())}</td><td class='b'>{_fmt(i['qtd_declarada'])}</td>"
            f"<td class='b'>{'—' if pd.isna(i['qtd_recebida']) or i['qtd_recebida'] is None else _fmt(i['qtd_recebida'])}</td></tr>"
            for i in itens)
        _md("<div class='ad-grade'><table class='ad-t2'><thead><tr><th>Insumo</th><th>Declarado</th><th>Recebido</th></tr></thead>"
            f"<tbody>{linhas}</tbody></table></div>")
        return

    # ---- Itens declarados  |  Contar e confirmar ----
    st.write("")
    c1, c2 = st.columns([1.35, 1], gap="medium")
    with c1, st.container(key="ad-box-rec-decl"):
        _md("<div class='ad-tit'>Itens declarados<span>conforme o romaneio</span></div>"
            "<table class='ad-t2'><thead><tr><th>Insumo</th><th>Quantidade</th></tr></thead><tbody>"
            + "".join(f"<tr><td>{_e(NOME.get(i['tipo'], i['tipo']).upper())}</td><td class='b'>{_fmt(i['qtd_declarada'])}</td></tr>"
                      for i in itens)
            + f"<tr class='tot'><td>Total declarado</td><td>{_fmt(total_decl)}</td></tr></tbody></table>")
        st.write("")
        if st.button("Aceitar o declarado sem contar", icon=":material/done_all:", key=f"ad-rec-aceitar-{dev['id']}",
                     width="stretch"):
            _confirmar(dev, [{"tipo": i["tipo"], "qtd_declarada": i["qtd_declarada"]} for i in itens], None, quem)
            st.session_state["_ad_rec_msg"] = ("ok", f"Recebimento de {dev['id']} confirmado (declarado aceito).")
            st.rerun()
    with c2, st.container(key="ad-box-rec-contar"):
        _md("<div class='ad-tit'>Contar e confirmar<span>ajuste se a contagem for diferente</span></div>")
        with st.form(f"ad-rec-form-{dev['id']}", border=False):
            recebidos = {}
            for i in itens:
                recebidos[i["tipo"]] = st.number_input(
                    f"{NOME.get(i['tipo'], i['tipo']).upper()} recebidos", min_value=0,
                    max_value=int(i["qtd_declarada"]), step=1, value=int(i["qtd_declarada"]),
                    key=f"ad-rec-q-{dev['id']}-{i['tipo']}",
                    help="Não pode passar da quantidade declarada no romaneio.")
            ok = st.form_submit_button("Confirmar recebimento", icon=":material/check:", type="primary")
        if ok:
            try:
                status = _confirmar(dev, [{"tipo": i["tipo"], "qtd_declarada": i["qtd_declarada"]} for i in itens],
                                    recebidos, quem)
            except ValueError as exc:
                st.error(str(exc))
            else:
                msg = ("Recebido com divergência entre declarado e contado." if status == dp.STATUS_DIVERGENTE
                       else "Recebimento conferido — quantidades batem.")
                st.session_state["_ad_rec_msg"] = ("aviso" if status == dp.STATUS_DIVERGENTE else "ok", f"{dev['id']}: {msg}")
                st.rerun()


# ---------------------------------------------------------------------------
# Devolução (registro em nome de uma base) — regras iguais às do page_3
# ---------------------------------------------------------------------------

def _dev_acima_do_saldo(destino: str, mes: str, itens: list[dict]) -> list[tuple]:
    """Confere o saldo com dados frescos na hora de gravar (mesma regra do page_3)."""
    dados.limpar_cache("devolucoes", "itens")
    atual = dp.pending_mes_tipo(destino, mes)
    return [(i["tipo"], i["qtd_declarada"], int(atual.get(i["tipo"], 0)))
            for i in itens if i["qtd_declarada"] > int(atual.get(i["tipo"], 0))]


def _confirmacao_devolucao(criada: dict) -> None:
    """Quadro verde com o ID logo abaixo do botão de registrar."""
    with st.container(key="ad-dev-ok"):
        c_ok1, c_ok2 = st.columns([3, 1], vertical_alignment="center")
        c_ok1.markdown(
            f"<div class='dv-sucesso'><b>Devolução realizada com sucesso!</b>"
            f"<span>ID <strong>{_e(criada['id'])}</strong> registrado para {_e(criada['destino'])}. "
            "Baixe o romaneio e envie impresso junto com os itens.</span></div>", unsafe_allow_html=True)
        c_ok2.download_button("Baixar romaneio", criada["pdf"], file_name=f"{criada['id']}.pdf",
                              mime="application/pdf", icon=":material/description:",
                              key=f"ad-dev-okrom-{criada['id']}", width="stretch")


def _devolucao_base() -> None:
    import uuid
    from datetime import datetime

    minha = _minha_base()
    so_ver = _perfil() == "gdl"  # GDL acompanha, mas não registra devolução
    if minha is not None:
        _titulo_grande("Registro de devoluções",
                       "Escolha o mês de referência, informe quanto vai devolver de cada insumo e gere o romaneio.")
    elif so_ver:
        _titulo_grande("Devoluções", "Saldo e devoluções de cada base. O registro de devoluções é feito pela base ou pelo administrador.")
    else:
        _titulo_grande("Registro de devoluções",
                       "Registre uma devolução em nome de uma base: escolha a operação e o mês de referência, "
                       "informe as quantidades e gere o romaneio.")
    user = st.session_state.get("usuario") or {}
    env = _da_minha_base(dp.envios_df())
    if env.empty:
        st.info("Nenhum envio registrado ainda.")
        return

    criada = st.session_state.pop("_ad_dev_criada", None)
    if criada:
        st.toast(f"Devolução {criada['id']} realizada com sucesso!", icon=":material/check_circle:")

    # ---- Filtros: operação e mês de referência ----
    ops = sorted(env["destino"].dropna().astype(str).unique(), key=str.lower)
    with st.container(key="ad-box-dev-filtros"):
        if minha is not None:
            f = st.columns([0.001, 2], gap=None, vertical_alignment="bottom")
            destino = minha
        else:
            f = st.columns([1.2, 2], gap="medium", vertical_alignment="bottom")
            destino = f[0].selectbox("Operação", ops, index=None, placeholder="Escolha a operação", key="ad-dev-op")
        mes = rot = None
        if destino:
            eleg = dp.competencias_elegiveis(destino)
            if eleg:
                rots = {dp.rotulo_mes(m): m for m in eleg}
                with f[1]:
                    escolha = st.segmented_control("Devolução referente ao saldo de qual mês?", list(rots),
                                                   default=list(rots)[0] if len(rots) == 1 else None,
                                                   key=f"ad-dev-mes-{destino}")
                if escolha:
                    mes, rot = rots[escolha], escolha
            else:
                f[1].caption("Nenhum mês aberto para devolução desta operação (prazos encerrados).")

    if not destino:
        _md("<div class='pd-faixa azul'>Escolha a operação para ver o saldo a devolver.</div>")
        return

    if mes:
        prazo = dp.prazo_devolucao(mes)
        ini = dp.agora_sp().normalize() + pd.Timedelta(days=1)
        dias = int(sum(1 for d in pd.date_range(ini, prazo.normalize()) if d.weekday() < 5)) if prazo.normalize() >= ini else 0
        _md(f"<div class='pd-faixa azul'>Saldo de <span class='ad-mes'>{_e(destino)}</span> em {_e(rot)} · prazo {prazo:%d/%m/%Y} · "
            + ("falta 1 dia útil" if dias == 1 else f"faltam {dias} dias úteis") + "</div>")

        resumo = dp.resumo_devolucao(destino, mes).set_index("tipo")
        pend = dp.pending_mes_tipo(destino, mes)
        pr = dp.precos()
        valor_total = sum(int(pend.get(t, 0)) * float(pr.get(t, 0) or 0) for t in TIPOS)

        if not any(int(pend.get(t, 0)) > 0 for t in TIPOS):
            _md(f"<div class='pd-faixa verde'>Nada a devolver: {_e(destino)} já devolveu tudo de {_e(rot)}.</div>")
            if criada:
                _confirmacao_devolucao(criada)
        elif so_ver:
            st.write("")
            cols = st.columns(4, gap="medium")
            for col, t in zip(cols[:3], TIPOS):
                saldo = int(pend.get(t, 0))
                envi = int(resumo.loc[t, "enviado"]) if t in resumo.index else 0
                dev = int(resumo.loc[t, "em_transito"] + resumo.loc[t, "recebido"]) if t in resumo.index else 0
                with col, st.container(key=f"ad-dev-card-{t}"):
                    _md(f"<div class='dv-nome'>{NOME[t].upper()}</div>"
                        f"<div class='dv-saldo{' zero' if saldo == 0 else ''}'>{_fmt(saldo)}</div>"
                        f"<div class='dv-sub'>pendentes · recebeu {_fmt(envi)} · já devolveu {_fmt(dev)}</div>")
            with cols[3], st.container(key="ad-dev-card-total"):
                _md(f"<div class='dv-nome'>VALOR TOTAL A DEVOLVER</div><div class='dv-saldo valor'>{dp.fmt_brl(valor_total)}</div>"
                    f"<div class='dv-sub'>{_fmt(sum(int(pend.get(t, 0)) for t in TIPOS))} itens pendentes em {_e(rot)}</div>")
        else:
            st.write("")
            with st.form(f"ad-dev-form-{destino}-{mes}", border=False):
                cols = st.columns(4, gap="medium")
                qtds = {}
                for col, t in zip(cols[:3], TIPOS):
                    saldo = int(pend.get(t, 0))
                    envi = int(resumo.loc[t, "enviado"]) if t in resumo.index else 0
                    dev = int(resumo.loc[t, "em_transito"] + resumo.loc[t, "recebido"]) if t in resumo.index else 0
                    with col, st.container(key=f"ad-dev-card-{t}"):
                        _md(f"<div class='dv-nome'>{NOME[t].upper()}</div>"
                            f"<div class='dv-saldo{' zero' if saldo == 0 else ''}'>{_fmt(saldo)}</div>"
                            f"<div class='dv-sub'>pendentes · recebeu {_fmt(envi)} · já devolveu {_fmt(dev)}</div>")
                        if saldo > 0:
                            qtds[t] = st.number_input(f"Devolver ({NOME[t].lower()})", min_value=0, max_value=saldo,
                                                      step=1, value=0, key=f"ad-dev-q-{destino}-{mes}-{t}",
                                                      help=f"Máximo {saldo}: não pode passar do pendente.")
                        else:
                            _md("<div class='dv-ok'>Tudo devolvido</div>")
                with cols[3], st.container(key="ad-dev-card-total"):
                    _md(f"<div class='dv-nome'>VALOR TOTAL A DEVOLVER</div><div class='dv-saldo valor'>{dp.fmt_brl(valor_total)}</div>"
                        f"<div class='dv-sub'>{_fmt(sum(int(pend.get(t, 0)) for t in TIPOS))} itens pendentes em {_e(rot)}</div>")
                c1, c2 = st.columns([1, 2], gap="medium")
                placa = c1.text_input("Placa do veículo", placeholder="ABC1D23", key=f"ad-dev-placa-{destino}")
                obs = c2.text_input("Observação (opcional)", placeholder="Alguma particularidade desta devolução",
                                    key=f"ad-dev-obs-{destino}")
                enviar = st.form_submit_button("Registrar devolução e gerar romaneio", icon=":material/assignment_return:",
                                               type="primary")
            if criada:
                _confirmacao_devolucao(criada)
            if enviar:
                itens = [{"tipo": t, "qtd_declarada": int(q)} for t, q in qtds.items() if q > 0]
                placa_norm = "".join(str(placa or "").upper().split()).replace("-", "")
                if not itens:
                    st.error("Informe a quantidade de pelo menos um insumo.")
                elif not placa_norm:
                    st.error("Informe a placa do veículo.")
                elif excedentes := _dev_acima_do_saldo(destino, mes, itens):
                    st.error("O saldo mudou e esta devolução passou do limite. Nada foi registrado. Saldo atual: "
                             + ", ".join(f"{NOME.get(t, t)} {_fmt(d)} (informado {_fmt(q)})" for t, q, d in excedentes))
                else:
                    dev_reg = {
                        "id": dados.proximo_codigo_devolucao(), "token": uuid.uuid4().hex,
                        "data_criacao": datetime.now(dp.TZ).strftime("%Y-%m-%d %H:%M:%S"),
                        "usuario": user.get("nome", user.get("usuario", "")), "destino": destino,
                        "status": dp.STATUS_TRANSITO, "total_declarado": sum(i["qtd_declarada"] for i in itens),
                        "total_recebido": "", "data_recebimento": "", "recebido_por": "", "obs": obs,
                        "placa": placa_norm, "competencia": mes,
                    }
                    dados.criar_devolucao(dev_reg, itens)  # pode trocar o id em caso de concorrência
                    st.session_state["_ad_dev_criada"] = {
                        "id": dev_reg["id"], "destino": destino,
                        "pdf": romaneio.gerar_romaneio_pdf(dev_reg, itens, dp.base_url())}
                    st.rerun()

    # ---- Devoluções da operação ----
    st.write("")
    devs = _retornos()
    devs = devs[devs["destino_norm"] == dp._normalizar(destino)] if not devs.empty else devs
    with st.container(key="ad-box-dev-lista"):
        _md(f"<div class='ad-tit'><div>Devoluções de <span class='ad-mes'>{_e(destino)}</span></div>"
            f"<span>{_fmt(len(devs))} registro(s)</span></div>")
        if devs.empty:
            _md("<div class='dv-vazio'><b>Nenhuma devolução registrada para esta operação.</b>"
                "<span>As devoluções registradas aqui (ou pela própria base) vão aparecer nesta lista.</span></div>")
            return
        pesos = [1.6, 1.2, 1.0, 0.8, 1.0]
        with st.container(key="ad-dev-cab"):
            h = st.columns(pesos, gap="small")
            for c, nome in zip(h, ["Registro", "Status", "Placa", "Qtd", "Anexo"]):
                c.markdown(f"<div class='dv-th'>{nome}</div>", unsafe_allow_html=True)
        for _, d in devs.head(20).iterrows():
            with st.container(key=f"ad-dev-linha-{d['id']}"):
                r = st.columns(pesos, gap="small", vertical_alignment="center")
                dt = d.get("dt_criacao")
                quando = dt.strftime("%d/%m/%Y") if pd.notna(dt) else ""
                comp = str(d.get("competencia") or "")
                comp_txt = dp.rotulo_mes(comp) if len(comp) == 7 else ""
                r[0].markdown(f"<div class='dv-td'><b>{_e(d['id'])}</b><span>{_e(quando)}{' · ' + _e(comp_txt) if comp_txt else ''}</span></div>",
                              unsafe_allow_html=True)
                r[1].markdown(f"<div class='dv-td'>{_pill_dev(d['status'])}</div>", unsafe_allow_html=True)
                r[2].markdown(f"<div class='dv-td'><b>{_e(d.get('placa') or '—')}</b></div>", unsafe_allow_html=True)
                r[3].markdown(f"<div class='dv-td'><b>{_fmt(d['total_declarado'] or d['qtd'])}</b></div>", unsafe_allow_html=True)
                its = [{"tipo": t, "qtd_declarada": int(d[t])} for t in TIPOS if d[t]]
                dd = d.to_dict()
                with r[4]:
                    st.download_button("Romaneio", data=lambda dd=dd, its=its: romaneio.gerar_romaneio_pdf(dd, its, dp.base_url()),
                                       file_name=f"{d['id']}.pdf", mime="application/pdf", icon=":material/description:",
                                       key=f"ad-dev-rom-{d['id']}", on_click="ignore")
        if len(devs) > 20:
            st.caption(f"Mostrando as 20 mais recentes de {_fmt(len(devs))}. Veja todas em Retornos e romaneios.")


def _pill_dev(status: str) -> str:
    s_ = str(status).upper()
    rot, _ = STATUS.get(s_, (str(status).title(), "cinza"))
    cls = {"CONFERIDO": "verde", "RECEBIDO": "verde", "EM_TRANSITO": "azul", "DIVERGENTE": "amarelo",
           "CANCELADO": "vermelho"}.get(s_, "cinza")
    return f"<span class='ad-pill {cls}'>{_e(rot)}</span>"


# ---------------------------------------------------------------------------
# 3. Retornos e romaneios
# ---------------------------------------------------------------------------

def _retornos_tela() -> None:
    hc1, hc2 = st.columns([3, 1], vertical_alignment="bottom")
    with hc1:
        _cabecalho("Retornos e romaneios", "Acompanhe as devoluções por base, período, material e status, e baixe os romaneios.")
    df = _retornos()
    if df.empty:
        st.info("Nenhuma devolução registrada ainda.")
        return
    hoje = dp.agora_sp().date()
    with st.container(key="ad-box-filtros"):
        f = st.columns([1.5, 1, 1.2, 1, 1.4], gap="small", vertical_alignment="bottom")
        per = f[0].date_input("Período", value=(hoje - pd.Timedelta(days=30), hoje), format="DD/MM/YYYY", key="ad-ret-per")
        mat = f[1].selectbox("Material", ["Todos"] + [NOME[t] for t in TIPOS], key="ad-ret-mat")
        bases = sorted(df["destino"].dropna().astype(str).unique())
        base = f[2].selectbox("Base (origem)", ["Todas"] + bases, key="ad-ret-base")
        stt = f[3].selectbox("Status", ["Todos"] + [v[0] for v in STATUS.values()], key="ad-ret-st")
        busca = f[4].text_input("Buscar", value=st.session_state.get(CHAVE_BUSCA, ""), key="ad-ret-busca",
                                placeholder="Romaneio, base ou placa")
    v = df
    if isinstance(per, tuple) and len(per) == 2:
        ini, fim = pd.Timestamp(per[0]), pd.Timestamp(per[1]) + pd.Timedelta(days=1)
        v = v[(v["dt_criacao"] >= ini) & (v["dt_criacao"] < fim)]
    if mat != "Todos":
        t = next(k for k, n in NOME.items() if n == mat)
        v = v[v[t] > 0]
    if base != "Todas":
        v = v[v["destino"].astype(str) == base]
    if stt != "Todos":
        cod = next(k for k, (r, _) in STATUS.items() if r == stt)
        v = v[v["status"] == cod]
    if busca:
        b = busca.strip().lower()
        v = v[v["id"].astype(str).str.lower().str.contains(b, regex=False)
              | v["destino"].astype(str).str.lower().str.contains(b, regex=False)
              | v["placa"].astype(str).str.lower().str.contains(b, regex=False)]
        st.session_state[CHAVE_BUSCA] = busca

    tot = {t: int(v[t].sum()) for t in TIPOS}
    st.write("")
    with st.container(key="ad-box-ret"):
        _md(f"<div class='ad-tit'>{_fmt(len(v))} devoluções<span>"
            + " · ".join(f"{_fmt(tot[t])} {NOME[t].lower()}" for t in TIPOS) + "</span></div>")
        _tabela_retornos(v.head(100))
        if len(v) > 100:
            st.caption(f"Mostrando 100 de {_fmt(len(v))}. Baixe o CSV para ver tudo.")
    c1, c2, c3 = st.columns([1.6, 1, 1], vertical_alignment="bottom")
    sel = c1.selectbox("Romaneio", v["id"].astype(str).tolist(), index=None, placeholder="Escolha para baixar o romaneio",
                       key="ad-ret-rom")
    if sel:
        d = v[v["id"].astype(str) == sel].iloc[0]
        itens = [{"tipo": t, "qtd_declarada": int(d[t])} for t in TIPOS if d[t]]
        c2.download_button("Baixar romaneio", romaneio.gerar_romaneio_pdf(d.to_dict(), itens, dp.base_url()),
                           file_name=f"{sel}.pdf", mime="application/pdf", icon=":material/download:", key=f"ad-rom-{sel}")
    csv = v.assign(Data=v["dt_criacao"].dt.strftime("%d/%m/%Y"))[
        ["Data", "id", "destino", "local_devolucao", "placa", "SACA", "GAYLORD", "PALLET", "status"]]
    c3.download_button("Baixar CSV", csv.to_csv(index=False).encode("utf-8-sig"), file_name="retornos.csv",
                       mime="text/csv", icon=":material/table:", key="ad-ret-csv")


# ---------------------------------------------------------------------------
# 5. Bases e usuários
# ---------------------------------------------------------------------------

def _uf(nome: str) -> str:
    m = re.search(r"\b([A-Z]{2})\b", str(nome).replace("Leve -", ""))
    return m.group(1) if m else "—"


def _bases() -> None:
    _titulo_grande("Bases e usuários", "Bases atendidas pela Loggi e as pessoas com acesso ao portal.")
    aba = st.segmented_control("Visão", ["Bases", "Usuários"], default="Bases", key="ad-bases-aba",
                               label_visibility="collapsed") or "Bases"
    if aba == "Usuários":
        _usuarios()
        return
    us = pd.DataFrame(dados.ler_usuarios())
    pend = _pendentes()
    pend_base = pend.groupby(pend["destino"].map(dp._normalizar))[["pendente", "valor"]].sum() if not pend.empty else pd.DataFrame()
    if us.empty:
        st.info("Nenhum usuário cadastrado.")
        return
    ops = us[us["perfil"].astype(str).str.lower().isin(["operacao", "operação", ""])].copy()
    ops["sig"] = ops["destino"].map(dp._normalizar)
    b = (ops.sort_values("ativo", ascending=False).groupby("sig")
         .agg(sigla=("destino", "first"), base=("nome", "first"), ativo=("ativo", "max"), usuarios=("usuario", "count")))
    b["uf"] = b["base"].map(_uf)
    b = b.join(pend_base, how="left").fillna({"pendente": 0, "valor": 0})
    busca = st.text_input("Buscar base", placeholder="Sigla ou nome da base", key="ad-bases-busca", icon=":material/search:")
    v = b
    if busca:
        s = busca.lower()
        v = b[b["sigla"].str.lower().str.contains(s, regex=False) | b["base"].str.lower().str.contains(s, regex=False)]
    v = v.sort_values("valor", ascending=False)
    linhas = "".join(
        f"<tr><td><span class='ad-mes'>{_e(x.sigla)}</span></td><td class='bs-nome'>{_e(str(x.base).replace('Leve - ', ''))}</td><td>{_e(x.uf)}</td>"
        f"<td>{_fmt(x.usuarios)}</td><td class='b'>{_fmt(x.pendente)}</td><td class='b'>{dp.fmt_brl(x.valor)}</td>"
        f"<td><span class='ad-pill {'verde' if x.ativo else 'cinza'}'>{'Ativa' if x.ativo else 'Inativa'}</span></td></tr>"
        for _, x in v.iterrows())
    with st.container(key="ad-box-bases"):
        _md(f"<div class='ad-tit'>{_fmt(len(v))} bases<span>ordenadas pelo valor em aberto</span></div>"
            "<div class='ad-grade'><table class='ad-t2 bs-t'><thead><tr><th>Sigla</th><th>Base</th><th>UF</th><th>Usuários</th>"
            "<th>Itens em aberto</th><th>Valor em aberto</th><th>Status</th></tr></thead><tbody>"
            + linhas + "</tbody></table></div>")


PERFIL_ROT = {"admin": "Administrador", "recebimento": "Recebimento", "gdl": "GDL", "operacao": "Operação"}


def _usuarios() -> None:
    """Busca e criação de usuários (gravação pelo auth.criar_usuario, igual ao page_2)."""
    import auth

    c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
    busca = c1.text_input("Buscar usuário", placeholder="Nome, login, base ou e-mail", key="ad-us-busca",
                          icon=":material/search:")
    novo = c2.toggle("Novo usuário", key="ad-us-novo")

    if novo:
        env = dp.envios_df()
        destinos = sorted(env["destino"].dropna().astype(str).unique()) if not env.empty else []
        with st.container(key="ad-box-us-novo"):
            _md("<div class='ad-tit'>Novo usuário<span>preencha e clique em Criar usuário</span></div>")
            with st.form("ad-us-form", clear_on_submit=True, border=False):
                a, b, c = st.columns(3, gap="medium")
                nome = a.text_input("Nome da operação", placeholder="Ex.: Leve - SP Base São Paulo")
                usuario = b.text_input("Usuário (login)", placeholder="ex.: base_sp")
                senha = c.text_input("Senha", placeholder="mínimo 6 caracteres", type="password")
                a2, b2, c2_ = st.columns(3, gap="medium")
                email = a2.text_input("E-mail (para cobrança)", placeholder="base_sp@empresa.com")
                perfil_lbl = b2.selectbox("Perfil", ["Operação", "Administrador", "Recebimento", "GDL"]
                                          if _eh_admin() else ["Operação"])
                destino = c2_.selectbox("Base (sigla)", [""] + destinos, help="Admin e Recebimento não usam base.")
                destino_livre = st.text_input("...ou digite uma sigla nova", placeholder="Só se a base ainda não aparece na lista")
                criar = st.form_submit_button("Criar usuário", icon=":material/person_add:", type="primary")
            if criar:
                perfil = {"Administrador": auth.PERFIL_ADM, "Recebimento": auth.PERFIL_RECEB,
                          "GDL": auth.PERFIL_GDL}.get(perfil_lbl, auth.PERFIL_OP)
                dest = (destino_livre or "").strip() or destino
                if perfil in (auth.PERFIL_ADM, auth.PERFIL_RECEB, auth.PERFIL_GDL) and not dest.strip():
                    dest = "*"
                ok, msg = auth.criar_usuario(usuario, senha, dest, nome, perfil, email=email)
                (st.success if ok else st.error)(msg)

    us = dados.ler_usuarios()
    if not _eh_admin():  # GDL vê e cadastra só usuários de operação
        us = [u for u in us if str(u.get("perfil", "")).lower() in ("operacao", "operação", "")]
        st.caption("Perfil GDL: você vê e cadastra apenas usuários de operação (bases).")
    if busca:
        b_ = busca.strip().lower()
        us = [u for u in us if b_ in f"{u['nome']} {u['usuario']} {u['destino']} {u.get('email', '')}".lower()]
    us = sorted(us, key=lambda u: (not u.get("ativo"), str(u.get("destino", "")).lower(), str(u.get("nome", "")).lower()))
    st.write("")
    with st.container(key="ad-box-us-lista"):
        ativos = sum(1 for u in us if u.get("ativo"))
        _md(f"<div class='ad-tit'>Usuários<span>{_fmt(len(us))} encontrado(s) · {_fmt(ativos)} ativo(s)</span></div>")
        if not us:
            _md("<div class='dv-vazio'><b>Nenhum usuário encontrado.</b><span>Tente outro termo na busca.</span></div>")
            return
        linhas = "".join(
            f"<tr><td>{_e(u['nome'] or '—')}</td><td>{_e(u['usuario'])}</td>"
            f"<td>{'<span class=ad-mes>' + _e(u['destino']) + '</span>' if u['destino'] and u['destino'] != '*' else '—'}</td>"
            f"<td>{_e(u.get('email') or '—')}</td><td>{_e(PERFIL_ROT.get(u.get('perfil'), 'Operação'))}</td>"
            f"<td><span class='ad-pill {'verde' if u.get('ativo') else 'vermelho'}'>{'Ativo' if u.get('ativo') else 'Inativo'}</span></td></tr>"
            for u in us)
        _md("<div class='ad-grade'><table class='ad-t2 us-t'><thead><tr><th>Nome</th><th>Login</th><th>Base</th>"
            "<th>E-mail</th><th>Perfil</th><th>Status</th></tr></thead><tbody>" + linhas + "</tbody></table></div>")


# ---------------------------------------------------------------------------
# 6. Indicadores
# ---------------------------------------------------------------------------

def _indicadores() -> None:
    hc1, hc2 = st.columns([3, 1], vertical_alignment="bottom")
    with hc1:
        _cabecalho("Indicadores", "Desempenho de retornos, pendências e evolução por período.")
    per = hc2.selectbox("Período", ["Últimos 3 meses", "Últimos 6 meses", "Últimos 12 meses"], index=1,
                        label_visibility="collapsed", key="ad-ind-per")
    n = int(re.search(r"\d+", per).group())
    agora = dp.agora_sp()
    ini = (agora.to_period("M") - (n - 1)).start_time
    rec = _recebidos()
    rec = rec[rec["dt"] >= ini] if not rec.empty else rec
    env = dp.envios_df()
    env = env[env["dt"] >= ini] if not env.empty else env
    enviado = env["total"].sum() if not env.empty else 0
    retornado = rec["q"].sum() if not rec.empty else 0
    taxa = 100 * retornado / enviado if enviado else 0
    pr = dp.precos()
    evitado = sum(rec.loc[rec["tipo"] == t, "q"].sum() * float(pr.get(t, 0) or 0) for t in TIPOS) if not rec.empty else 0

    k = st.columns(4, gap="small")
    k[0].markdown(_kpi(_IC["taxa"], "Taxa de retorno", f"{taxa:.1f}%".replace(".", ","), "recebido ÷ enviado"), unsafe_allow_html=True)
    k[1].markdown(_kpi(_IC["saca"], "Sacas retornadas", _fmt(rec.loc[rec["tipo"] == "SACA", "q"].sum() if not rec.empty else 0), per.lower()), unsafe_allow_html=True)
    k[2].markdown(_kpi(_IC["caixa"], "Gaylords retornados", _fmt(rec.loc[rec["tipo"] == "GAYLORD", "q"].sum() if not rec.empty else 0), per.lower()), unsafe_allow_html=True)
    k[3].markdown(_kpi(_IC["dinheiro"], "Custo evitado", dp.fmt_brl(evitado), "itens que voltaram", "up"), unsafe_allow_html=True)

    st.write("")
    g1, g2, g3 = st.columns([1.5, 1, 1.4], gap="medium")
    with g1, st.container(key="ad-box-mes"):
        _md("<div class='ad-tit'>Retornos por mês</div>")
        if rec.empty:
            _md("<div class='ad-vazio'>Sem retornos no período.</div>")
        else:
            m = rec.assign(mes=rec["dt"].dt.to_period("M").astype(str)).groupby(["mes", "tipo"])["q"].sum().unstack(fill_value=0)
            fig = go.Figure()
            for t in ["SACA", "GAYLORD"]:
                if t in m.columns:
                    fig.add_trace(go.Bar(x=[dp.rotulo_mes(x).split("/")[0][:3].lower() for x in m.index], y=m[t],
                                         name=NOME[t], marker_color=COR[t]))
            fig.update_layout(barmode="group", bargap=.35)
            st.plotly_chart(_layout_plotly(fig, 240), width="stretch", config={"displayModeBar": False})
    with g2, st.container(key="ad-box-mat"):
        _md("<div class='ad-tit'>Retornos por material</div>")
        if rec.empty:
            _md("<div class='ad-vazio'>Sem retornos.</div>")
        else:
            t = rec.groupby("tipo")["q"].sum().reindex(TIPOS).dropna()
            fig = go.Figure(go.Pie(labels=[NOME[x] for x in t.index], values=t.values, hole=.68,
                                   marker=dict(colors=[COR[x] for x in t.index]), textinfo="percent", sort=False))
            fig.add_annotation(text=f"<b>{_fmt(t.sum())}</b><br>total", showarrow=False, font=dict(size=14, color="#14213d"))
            fig = _layout_plotly(fig, 240)
            fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center", yanchor="top"),
                              margin=dict(l=6, r=6, t=6, b=30))
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    with g3, st.container(key="ad-box-top"):
        _md("<div class='ad-tit'>Top 5 bases com pendência<span>valor em aberto</span></div>")
        pend = _pendentes()
        if pend.empty:
            _md("<div class='ad-vazio'>Nenhuma pendência.</div>")
        else:
            top = pend.groupby("destino")["valor"].sum().nlargest(5).sort_values()
            fig = go.Figure(go.Bar(x=top.values, y=top.index, orientation="h", marker_color="#006aff",
                                   text=[dp.fmt_brl(v) for v in top.values], textposition="inside",
                                   insidetextanchor="end", textfont=dict(color="#ffffff", size=11)))
            fig.update_xaxes(visible=False)
            st.plotly_chart(_layout_plotly(fig, 240), width="stretch", config={"displayModeBar": False})


# ---------------------------------------------------------------------------
# telas existentes encaixadas
# ---------------------------------------------------------------------------

def _limpar_filtros_cob() -> None:
    for k in ("ad-cb-mes", "ad-cb-op"):
        st.session_state.pop(k, None)


def _conciliacao_cobrancas() -> None:
    """Notas de crédito dos insumos não devolvidos (aba Cobrancas da LEVES APP)."""
    _titulo_grande("Cobranças",
                   "Insumos não devolvidos cobrados das bases: uma nota por base, por mês.")
    minha = _minha_base()
    notas = _da_minha_base(dp.notas_credito())
    if notas.empty:
        if minha is not None:
            _md("<div class='dv-vazio'><b>Nenhuma nota de débito para a sua base.</b>"
                "<span>Quando houver cobrança por insumos não devolvidos no prazo, a nota aparece aqui.</span></div>")
        else:
            _md("<div class='dv-vazio'><b>Nenhuma nota de crédito lançada ainda.</b>"
                "<span>As notas lançadas na aba Cobrancas da planilha LEVES APP aparecem aqui.</span></div>")
        return

    meses = sorted([m for m in notas["mes"].unique() if m], reverse=True)
    rot = {dp.rotulo_mes(m): m for m in meses}
    with st.container(key="ad-box-cb-filtros"):
        f = st.columns([1.4, 2, 0.9] if minha is None else [2, 1.4, 0.9], gap="small", vertical_alignment="bottom")
        mes_sel = f[0].multiselect("Competência", list(rot), default=[], key="ad-cb-mes", placeholder="Todas as competências")
        op_sel = []
        if minha is None:
            ops = sorted([d for d in notas["destino"].unique() if d], key=str.lower)
            op_sel = f[1].multiselect("Operação", ops, default=[], key="ad-cb-op", placeholder="Todas as operações")
        with f[2]:
            st.button("Limpar filtros", icon=":material/filter_alt_off:", key="ad-cb-limpar",
                      on_click=_limpar_filtros_cob, width="stretch")

    v = notas
    if mes_sel:
        v = v[v["mes"].isin([rot[m] for m in mes_sel])]
    if op_sel:
        v = v[v["destino"].isin(op_sel)]

    sem_base = v[v["destino"] == ""]
    if not sem_base.empty:
        _md(f"<div class='pd-faixa amarelo'>{len(sem_base)} nota(s) sem base preenchida na planilha: "
            f"{_e(', '.join(sem_base['nota']))}.</div>")

    total = float(v["valor"].sum())
    n_notas = len(v)
    n_bases = v.loc[v["destino"] != "", "destino"].nunique()
    medio = total / n_notas if n_notas else 0
    cards = [
        (dp.fmt_brl(total), "VALOR TOTAL REGISTRADO", f"{len(set(v['mes']))} competência(s)"),
        (_fmt(n_notas), "NOTAS DE DÉBITO", "uma por base, por mês"),
        (_fmt(n_bases), "OPERAÇÕES", "com pelo menos uma nota"),
    ]
    if minha is not None:
        cards[1] = (_fmt(n_notas), "NOTAS DE DÉBITO", "uma por mês cobrado")
        cards[2] = (dp.fmt_brl(medio), "VALOR MÉDIO POR NOTA", "por competência cobrada")
    st.write("")
    k = st.columns(3, gap="medium")
    for col, (valor_c, rotulo, sub) in zip(k, cards):
        col.markdown(f"<div class='ad-big'><div class='v pd-v'>{valor_c}</div>"
                     f"<div class='l'>{_e(rotulo)}</div><div class='s'>{_e(sub)}</div></div>", unsafe_allow_html=True)

    # ---- ranking de bases e evolução por competência ----
    st.write("")
    g1, g2 = st.columns([1.15, 1], gap="medium") if minha is None else (st.empty(), st.container())
    por_base = v[v["destino"] != ""].groupby("destino").agg(valor=("valor", "sum"), notas=("nota", "count")) \
                .sort_values("valor", ascending=False)
    if minha is None:
      with g1, st.container(key="ad-box-cb-top"):
        _md("<div class='ad-tit'>Bases com maior valor cobrado<span>top 5 · % do total</span></div>")
        top = por_base.head(5)
        if top.empty:
            _md("<div class='ad-vazio'>Sem notas para os filtros escolhidos.</div>")
        else:
            maior = float(top["valor"].max()) or 1.0
            _md("<div class='rk-lista'>" + "".join(
                f"<div class='rk'><div class='rk-n'>{i}</div><div class='rk-c'>"
                f"<div class='rk-l'><b>{_e(d)}</b><span>{_fmt(r['notas'])} nota(s) · {100 * r['valor'] / (total or 1):.1f}% do total</span>"
                f"<em>{dp.fmt_brl(r['valor'])}</em></div>"
                f"<div class='rk-b'><span style='width:{100 * r['valor'] / maior:.0f}%'></span></div></div></div>"
                for i, (d, r) in enumerate(top.iterrows(), start=1)) + "</div>")
    with g2, st.container(key="ad-box-cb-mes"):
        _md("<div class='ad-tit'>Por competência<span>valor e quantidade de notas</span></div>")
        pm = v.groupby("mes").agg(valor=("valor", "sum"), notas=("nota", "count")).sort_index(ascending=False)
        maior_m = float(pm["valor"].max()) if not pm.empty else 1.0
        _md("".join(
            f"<div class='pd-ins'><div class='pd-ins-top'><b>{_e(dp.rotulo_mes(m) if m else '—')}</b><span>{dp.fmt_brl(r['valor'])}</span></div>"
            f"<div class='pd-barra'><span style='width:{100 * r['valor'] / (maior_m or 1):.0f}%'></span></div>"
            f"<div class='pd-ins-sub'>{_fmt(r['notas'])} nota(s) emitida(s)</div></div>"
            for m, r in pm.iterrows()))

    # ---- tabela de notas ----
    st.write("")
    with st.container(key="ad-box-cb-tab"):
        _md(f"<div class='ad-tit'>Notas de débito<span>{_fmt(n_notas)} nota(s) · maiores valores primeiro</span></div>")
        t = v.sort_values(["mes", "valor"], ascending=[False, False])
        linhas = []
        for _, r in t.iterrows():
            data_txt = r["dt"].strftime("%d/%m/%Y") if pd.notna(r["dt"]) else "—"
            base_txt = f"<b>{_e(r['destino'])}</b>" if r["destino"] else "<span class='ad-pill vermelho'>Sem base</span>"
            linhas.append(f"<tr><td>{_e(r['nota'])}</td><td><span class='ad-mes'>{_e(r['rotulo'])}</span></td>"
                          f"<td>{_e(data_txt)}</td><td>{base_txt}</td><td class='b'>{dp.fmt_brl(r['valor'])}</td>"
                          f"<td>{_e(r['emitida_por'] or '—')}</td></tr>")
        rod = (f"<tr class='tot'><td>Total</td><td></td><td></td><td>{_fmt(n_bases)} base(s)</td>"
               f"<td>{dp.fmt_brl(total)}</td><td></td></tr>")
        _md("<div class='ad-grade'><table class='ad-t2 cb-t'><thead><tr><th>Nota</th><th>Competência</th><th>Emissão</th>"
            "<th>Base</th><th>Valor</th><th>Emitida por</th></tr></thead><tbody>" + "".join(linhas) + rod + "</tbody></table></div>")
        exp = t.assign(Emissão=t["dt"].dt.strftime("%d/%m/%Y"))[["nota", "rotulo", "Emissão", "destino", "valor", "emitida_por"]] \
               .rename(columns={"nota": "Nota", "rotulo": "Competência", "destino": "Base", "valor": "Valor (R$)",
                                "emitida_por": "Emitida por"})
        st.download_button("Exportar Excel", _excel_pendencias(exp, por_base.reset_index().rename(
                               columns={"destino": "Base", "valor": "Valor (R$)", "notas": "Notas"}), "Cobranças"),
                           file_name="cobrancas.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           icon=":material/download:", key="ad-cb-xlsx")


def _limpar_filtros_pend() -> None:
    for k in ("ad-pd-comp", "ad-pd-op", "ad-pd-ins"):
        st.session_state.pop(k, None)


def _excel_pendencias(por_base: pd.DataFrame, detalhe: pd.DataFrame, titulo: str) -> bytes:
    import io

    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        for nome, df in (("Por base", por_base), ("Base x insumo", detalhe)):
            df.to_excel(w, index=False, sheet_name=nome, startrow=1)
            ws = w.sheets[nome]
            ws["A1"] = titulo
            ws["A1"].font = Font(bold=True, size=12, color="14213D")
            for c in ws[2]:
                c.font = Font(bold=True, color="FFFFFF")
                c.fill = PatternFill("solid", fgColor="006AFF")
            for i, col in enumerate(df.columns, start=1):
                ws.column_dimensions[get_column_letter(i)].width = max(12, len(str(col)) + 4)
    return buf.getvalue()


def _pendencias() -> None:
    """Conciliação + pendências num módulo só (mesma base: dp.conciliacao)."""
    import emailer

    minha = _minha_base()
    _titulo_grande("Pendências de devolução",
                   "Enviado × devolvido por competência e o valor que ainda falta devolver."
                   if minha is not None else
                   "Enviado × devolvido por competência, valor pendente e cobrança das bases.")
    env = _da_minha_base(dp.envios_df())
    if env.empty:
        st.info("Nenhum envio registrado ainda.")
        return
    meses = sorted(env["mes"].unique(), reverse=True)
    rot_mes = {dp.rotulo_mes(m): m for m in meses}
    pr = dp.precos()

    # ---- Filtros ----
    with st.container(key="ad-box-pd-filtros"):
        f = (st.columns([1.1, 1.4, 0.9], gap="small", vertical_alignment="bottom") if minha is not None
             else st.columns([1.1, 1.8, 1.4, 0.9], gap="small", vertical_alignment="bottom"))
        comp_rot = f[0].selectbox("Competência", list(rot_mes), index=0, key="ad-pd-comp")
        mes = rot_mes[comp_rot]
        base = dp.conciliacao(mes)
        if base.empty:
            st.info(f"Sem envios em {comp_rot}.")
            return
        base = _da_minha_base(base[base["tipo"].isin(TIPOS)]).copy()
        op_sel = []
        if minha is None:
            ops = sorted(base["destino"].astype(str).unique(), key=str.lower)
            op_sel = f[1].multiselect("Operação", ops, default=[], key="ad-pd-op", placeholder="Todas as operações")
        ins_sel = f[-2].multiselect("Insumo", [NOME[t].upper() for t in TIPOS], default=[], key="ad-pd-ins",
                                    placeholder="Todos os insumos")
        with f[-1]:
            st.button("Limpar filtros", icon=":material/filter_alt_off:", key="ad-pd-limpar",
                      on_click=_limpar_filtros_pend, width="stretch")

    base["valor"] = base["cobravel"] * base["tipo"].map(lambda t: float(pr.get(t, 0) or 0))
    v = base
    if op_sel:
        v = v[v["destino"].astype(str).isin(op_sel)]
    tipos = [t for t in TIPOS if NOME[t].upper() in ins_sel] or TIPOS
    v = v[v["tipo"].isin(tipos)]

    # ---- Situação da competência ----
    prazo = dp.prazo_devolucao(mes)
    fechada = dados.competencia_ja_fechada(mes)
    fechavel = dp.competencia_fechavel(mes)
    if fechada:
        faixa = ("verde", f"Competência fechada — os itens cobrados de {comp_rot} já receberam baixa.")
    elif fechavel:
        faixa = ("amarelo", f"Prazo encerrado em {prazo:%d/%m/%Y} — o pendente já pode ser cobrado"
                            + (" (fechamento no fim da tela)." if _eh_admin() else "."))
    else:
        ini = dp.agora_sp().normalize() + pd.Timedelta(days=1)
        dias = int(sum(1 for d in pd.date_range(ini, prazo.normalize()) if d.weekday() < 5)) if prazo.normalize() >= ini else 0
        faixa = ("azul", f"Devoluções de {comp_rot} aceitas até {prazo:%d/%m/%Y} — "
                         + ("falta 1 dia útil." if dias == 1 else f"faltam {dias} dias úteis."))
    _md(f"<div class='pd-faixa {faixa[0]}'>{_e(faixa[1])}</div>")

    # ---- Cards ----
    pend_itens = int(v["cobravel"].sum())
    valor = float(v["valor"].sum())
    enviado = int(v["enviado"].sum())
    recebido = int(v["devolvido"].sum())
    taxa = 100 * recebido / enviado if enviado else 0
    bases_pend = v.loc[v["cobravel"] > 0, "destino"].nunique()
    bases_tot = v["destino"].nunique()
    por_tipo = v.groupby("tipo")["cobravel"].sum()
    detalhe_tipo = " · ".join(f"{_fmt(por_tipo.get(t, 0))} {NOME[t].lower()}" for t in tipos)
    cards = [
        (dp.fmt_brl(valor), "VALOR PENDENTE", "itens não devolvidos × preço"),
        (_fmt(pend_itens), "INSUMOS PENDENTES", detalhe_tipo),
        (f"{_fmt(bases_pend)}", "BASES COM PENDÊNCIA", f"de {_fmt(bases_tot)} bases com envio")
        if minha is None else
        (f"{_fmt(enviado)}", "INSUMOS RECEBIDOS", f"enviados pela Loggi em {comp_rot}"),
        (f"{taxa:.1f}%".replace(".", ","), "TAXA DE DEVOLUÇÃO", f"{_fmt(recebido)} recebidos de {_fmt(enviado)} enviados"),
    ]
    st.write("")
    k = st.columns(4, gap="medium")
    for i, (col, (valor_c, rotulo, sub)) in enumerate(zip(k, cards)):
        col.markdown(f"<div class='ad-big pd-card{' pd-card-destaque' if i == 0 else ''}'><div class='v pd-v'>{valor_c}</div>"
                     f"<div class='l'>{_e(rotulo)}</div><div class='s'>{_e(sub)}</div></div>", unsafe_allow_html=True)

    # ---- Por base ----
    piv_q = v.pivot_table(index="destino", columns="tipo", values="cobravel", aggfunc="sum", fill_value=0).reindex(columns=tipos, fill_value=0)
    agg = v.groupby("destino").agg(enviado=("enviado", "sum"), recebido=("devolvido", "sum"),
                                   pendente=("cobravel", "sum"), valor=("valor", "sum"))
    por_base = agg.join(piv_q)
    por_base["taxa"] = (100 * por_base["recebido"] / por_base["enviado"]).where(por_base["enviado"] > 0, 0)
    por_base = por_base[por_base["pendente"] > 0]  # só bases com pendência
    por_base = por_base.sort_values(["valor", "pendente"], ascending=False)
    emails = {d: dp.emails_por_destino(d) for d in por_base.index}

    st.write("")
    g1, g2 = st.columns([1.15, 1], gap="medium") if minha is None else (st.empty(), st.container())
    if minha is None:
      with g1, st.container(key="ad-box-pd-top"):
        _md("<div class='ad-tit'>Bases com maior valor pendente<span>top 5 · % do total pendente</span></div>")
        top = por_base[por_base["valor"] > 0].head(5)
        if top.empty:
            _md("<div class='ad-vazio'>Nenhuma pendência para os filtros escolhidos.</div>")
        else:
            total_val = float(por_base["valor"].sum()) or 1.0
            maior = float(top["valor"].max()) or 1.0
            itens = "".join(
                f"<div class='rk'><div class='rk-n'>{i}</div><div class='rk-c'>"
                f"<div class='rk-l'><b>{_e(d)}</b><span>{_fmt(r['pendente'])} itens · {100 * r['valor'] / total_val:.1f}% do total</span>"
                f"<em>{dp.fmt_brl(r['valor'])}</em></div>"
                f"<div class='rk-b'><span style='width:{100 * r['valor'] / maior:.0f}%'></span></div></div></div>"
                for i, (d, r) in enumerate(top.iterrows(), start=1))
            _md(f"<div class='rk-lista'>{itens}</div>")
    with g2, st.container(key="ad-box-pd-ins"):
        _md("<div class='ad-tit'>Pendente por insumo<span>quantidade e valor</span></div>")
        linhas = ""
        for t in tipos:
            q = int(v.loc[v["tipo"] == t, "cobravel"].sum())
            val = float(v.loc[v["tipo"] == t, "valor"].sum())
            env_t = int(v.loc[v["tipo"] == t, "enviado"].sum())
            pct = 100 * q / env_t if env_t else 0
            linhas += (f"<div class='pd-ins'><div class='pd-ins-top'><b>{NOME[t].upper()}</b><span>{dp.fmt_brl(val)}</span></div>"
                       f"<div class='pd-barra'><span style='width:{min(pct, 100):.0f}%'></span></div>"
                       f"<div class='pd-ins-sub'>{_fmt(q)} pendentes de {_fmt(env_t)} enviados ({pct:.0f}%)</div></div>")
        _md(linhas)

    # ---- Tabela por base ----
    st.write("")
    with st.container(key="ad-box-pd-tab"):
        _md(f"<div class='ad-tit'>Pendência por base<span>{_fmt(len(por_base))} base(s) · ordenadas pelo valor</span></div>")
        if por_base.empty:
            _md("<div class='ad-vazio'>Nenhuma base com pendência nos filtros escolhidos.</div>")
        else:
            cab = ["Base", "Enviado", "Recebido"] + [f"{NOME[t]} pend." for t in tipos] + ["Valor pendente", "% devolvido", "E-mail"]
            corpo = "".join(
                f"<tr><td>{_e(d)}</td><td>{_fmt(r['enviado'])}</td><td>{_fmt(r['recebido'])}</td>"
                + "".join(f"<td class='b'>{_fmt(r[t])}</td>" for t in tipos)
                + f"<td class='b'>{dp.fmt_brl(r['valor'])}</td><td>{r['taxa']:.0f}%</td>"
                + (f"<td><span class='ad-pill verde'>Sim</span></td>" if emails.get(d) else "<td><span class='ad-pill vermelho'>Sem e-mail</span></td>")
                + "</tr>"
                for d, r in por_base.iterrows())
            tot = por_base.sum(numeric_only=True)
            rod = ("<tr class='tot'><td>Total</td>" + f"<td>{_fmt(tot['enviado'])}</td><td>{_fmt(tot['recebido'])}</td>"
                   + "".join(f"<td>{_fmt(tot[t])}</td>" for t in tipos) + f"<td>{dp.fmt_brl(tot['valor'])}</td><td></td><td></td></tr>")
            _md("<div class='ad-grade'><table class='ad-t2'><thead><tr>" + "".join(f"<th>{_e(c)}</th>" for c in cab)
                + f"</tr></thead><tbody>{corpo}{rod}</tbody></table></div>")
            exp_base = por_base.reset_index().rename(columns={"destino": "Base", "enviado": "Enviado", "recebido": "Recebido no CD",
                                                             "pendente": "Pendente", "valor": "Valor pendente (R$)", "taxa": "% devolvido",
                                                             **{t: f"{NOME[t]} pendentes" for t in tipos}})
            exp_base["E-mail"] = exp_base["Base"].map(lambda d: ", ".join(emails.get(d, [])))
            exp_det = v.rename(columns={"destino": "Base", "tipo": "Insumo", "enviado": "Enviado", "devolvido": "Recebido no CD",
                                        "cobrado": "Já cobrado", "cobravel": "Pendente", "valor": "Valor pendente (R$)"}
                               ).drop(columns=["em_aberto"], errors="ignore")
            st.download_button("Exportar Excel", _excel_pendencias(exp_base, exp_det, f"Pendências — {comp_rot}"),
                               file_name=f"pendencias_{mes}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               icon=":material/download:", key="ad-pd-xlsx")

    # E-mail às bases e fechamento da competência: só o administrador.
    if not _eh_admin():
        return

    # ---- E-mail de pendências ----
    st.write("")
    grupos = []
    pend_mail = base[base["cobravel"] > 0]
    if op_sel:
        pend_mail = pend_mail[pend_mail["destino"].astype(str).isin(op_sel)]
    for d, g in pend_mail.groupby("destino"):
        grupos.append({"destino": str(d), "total": int(g["cobravel"].sum()), "emails": dp.emails_por_destino(d),
                       "itens": [{"tipo": r["tipo"], "enviado": int(r["enviado"]), "devolvido": int(r["devolvido"]),
                                  "pendente": int(r["cobravel"])} for _, r in g.iterrows()]})
    com_email = [g for g in grupos if g["emails"]]
    with st.container(key="ad-box-pd-mail"):
        _md(f"<div class='ad-tit'>Enviar e-mail de pendências<span>{len(com_email)} de {len(grupos)} base(s) com e-mail cadastrado</span></div>")
        if not grupos:
            _md("<div class='ad-vazio'>Nenhuma base com pendência para avisar.</div>")
        elif not emailer.smtp_configurado():
            st.warning("Configure o servidor de e-mail em Configurações para enviar as pendências.")
        else:
            c1, c2 = st.columns([2.2, 1], vertical_alignment="bottom")
            ops_mail = {f"{g['destino']} · {_fmt(g['total'])} pendentes": g for g in com_email}
            alvo = c1.selectbox("Destinatários", [f"Todas as bases com e-mail ({len(com_email)})"] + list(ops_mail),
                                key="ad-pd-mail-alvo")
            if c2.button("Enviar e-mail", icon=":material/send:", type="primary", key="ad-pd-mail-btn", width="stretch"):
                envio = [ops_mail[alvo]] if alvo in ops_mail else com_email
                ok_n, falhas = 0, []
                with st.spinner("Enviando e-mails..."):
                    for g in envio:
                        ok, msg = emailer.enviar_pendencia(
                            g["emails"][0], g["destino"], g["itens"], g["total"], precos=pr,
                            competencia_label=comp_rot, destinatarios_adicionais=g["emails"][1:])
                        if ok:
                            ok_n += 1
                        else:
                            falhas.append(f"{g['destino']}: {msg}")
                if ok_n:
                    st.success(f"{ok_n} e-mail(s) de pendência de {comp_rot} enviado(s).")
                for fa in falhas:
                    st.error(fa)
            sem = [g["destino"] for g in grupos if not g["emails"]]
            if sem:
                st.caption("Sem e-mail cadastrado (não recebem): " + ", ".join(sem))

    # ---- Fechamento da competência (baixa definitiva) ----
    st.write("")
    with st.container(key="ad-box-pd-fecha"):
        _md(f"<div class='ad-tit'>Fechar cobrança de {_e(comp_rot)}<span>registra o pendente como cobrado e dá baixa</span></div>")
        total_cobravel = int(base["cobravel"].sum())  # sempre todas as bases e insumos
        if fechada:
            st.success(f"{comp_rot} já foi fechada. Os itens cobrados receberam baixa e não aceitam mais devolução.")
        elif not fechavel:
            st.info(f"Ainda dentro do prazo de devolução (até {prazo:%d/%m/%Y}). O fechamento fica disponível depois dessa data.")
        elif total_cobravel == 0:
            st.caption("Nenhum item pendente nesta competência. Nada a fechar.")
        else:
            valor_total = float(base["valor"].sum())
            _md(f"<div class='pd-faixa amarelo'>Ao fechar, <b>{_fmt(total_cobravel)}</b> itens de <b>todas as bases</b> "
                f"({dp.fmt_brl(valor_total)}) serão registrados como cobrados e recebem <b>baixa definitiva</b>: "
                "saem do saldo e não aceitam mais devolução.</div>")
            confirma = st.checkbox("Confirmo o fechamento desta competência (ação irreversível).", key=f"ad-pd-conf-{mes}")
            if st.button("Registrar cobrança e dar baixa", icon=":material/gavel:", type="primary",
                         disabled=not confirma, key=f"ad-pd-fechar-{mes}"):
                from datetime import datetime
                agora = datetime.now(dp.TZ).strftime("%Y-%m-%d %H:%M:%S")
                quem = (st.session_state.get("usuario") or {}).get("nome", "admin")
                cobraveis = base[base["cobravel"] > 0]
                rows = [{"id": f"COB-{mes}-{i:03d}", "data": agora, "competencia": mes, "destino": r["destino"],
                         "tipo": r["tipo"], "qtd": int(r["cobravel"]), "prazo_dias": f"{prazo:%d/%m/%Y}", "gerado_por": quem}
                        for i, (_, r) in enumerate(cobraveis.iterrows(), start=1)]
                dados.registrar_cobrancas(rows)
                st.success(f"Cobrança de {comp_rot} registrada. Itens baixados.")
                st.rerun()

def _excel_envios(tab: pd.DataFrame, titulo: str) -> bytes:
    """Planilha .xlsx da tabela de envios, com cabeçalho e linha de total formatados."""
    import io

    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        tab.to_excel(w, index=False, sheet_name="Envios", startrow=1)
        ws = w.sheets["Envios"]
        ws["A1"] = titulo
        ws["A1"].font = Font(bold=True, size=12, color="14213D")
        azul = PatternFill("solid", fgColor="006AFF")
        for c in ws[2]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = azul
            c.alignment = Alignment(horizontal="center")
        ultima = ws.max_row
        for c in ws[ultima]:
            c.font = Font(bold=True)
            c.fill = PatternFill("solid", fgColor="EAF3FF")
        for i, col in enumerate(tab.columns, start=1):
            ws.column_dimensions[get_column_letter(i)].width = max(12, len(str(col)) + 4)
            if i > 2:
                for (cel,) in ws.iter_rows(min_row=3, min_col=i, max_col=i):
                    cel.number_format = "#,##0"
    return buf.getvalue()


def _limpar_filtros_envios() -> None:
    for k in list(st.session_state.keys()):
        if str(k).startswith(("ad-env-dia-", "ad-env-op-")) or k in ("ad-env-mes", "ad-env-ins"):
            del st.session_state[k]


def _envios() -> None:
    minha = _minha_base()
    para = "para a sua base" if minha is not None else "para as bases"
    _md("<div class='ad-h1' style='font-size:27px;font-weight:700'>Visão geral de envios</div>"
        f"<div class='ad-sub' style='font-weight:700'>Insumos enviados pela Loggi {para}, dia a dia.</div>")
    env = _da_minha_base(dp.envios_df())
    if env.empty:
        st.info("Nenhum envio registrado ainda.")
        return
    env = env[env["tipo"].isin(TIPOS)]

    # ---- Filtros: mês, dia, insumo (e operação) ----
    meses = sorted(env["mes"].unique(), reverse=True)
    rot_mes = {dp.rotulo_mes(m): m for m in meses}
    with st.container(key="ad-box-env-filtros"):
        f = (st.columns([1.1, 1.45, 1.3, 1.0], gap="small", vertical_alignment="bottom") if minha is not None
             else st.columns([1.1, 1.45, 1.3, 1.4, 1.0], gap="small", vertical_alignment="bottom"))
        mes_rot = f[0].selectbox("Mês", list(rot_mes), index=0, key="ad-env-mes")
        mes = rot_mes[mes_rot]
        dm = env[env["mes"] == mes]
        dias_disp = sorted(dm["dia"].unique())
        rot_dia = {pd.Timestamp(d).strftime("%d/%m/%Y"): d for d in dias_disp}
        dias_sel = f[1].multiselect("Dia", list(rot_dia), default=[], key=f"ad-env-dia-{mes}",
                                    placeholder="Todos os dias")
        ins_sel = f[2].multiselect("Insumo", [NOME[t].upper() for t in TIPOS], default=[], key="ad-env-ins",
                                   placeholder="Todos os insumos")
        op_sel = []
        if minha is None:
            ops = sorted(dm["destino"].dropna().astype(str).unique())
            op_sel = f[3].multiselect("Operação", ops, default=[], key=f"ad-env-op-{mes}",
                                      placeholder="Todas as operações")
        with f[-1]:
            st.button("Limpar filtros", icon=":material/filter_alt_off:", key="ad-env-limpar",
                      on_click=_limpar_filtros_envios, width="stretch")

    v = dm
    if dias_sel:
        v = v[v["dia"].isin([rot_dia[d] for d in dias_sel])]
    tipos = [t for t in TIPOS if NOME[t].upper() in ins_sel] or TIPOS
    v = v[v["tipo"].isin(tipos)]
    if op_sel:
        v = v[v["destino"].astype(str).isin(op_sel)]

    # ---- Resumo do período ----
    tot = v.groupby("tipo")["total"].sum()
    _md(f"<div class='ad-tit' style='margin-top:14px'>Resumo do período<span>{_e(mes_rot)}"
        + (f" · {len(dias_sel)} dia(s)" if dias_sel else "") + (f" · {len(op_sel)} operação(ões)" if op_sel else "")
        + "</span></div>")
    n_dias = len(dias_sel) if dias_sel else v["dia"].nunique()
    cards = [
        (_fmt(tot.sum()), "TOTAL DE INSUMOS", f"em {n_dias} dia(s) com envio"),
        (_fmt(tot.get("SACA", 0)), "SACAS", f"{_fmt(tot.get('SACA', 0) / n_dias if n_dias else 0)} por dia, em média"),
        (_fmt(tot.get("GAYLORD", 0)), "GAYLORDS", f"{_fmt(tot.get('GAYLORD', 0) / n_dias if n_dias else 0)} por dia, em média"),
        (_fmt(tot.get("PALLET", 0)), "PALLETS", "1 para cada gaylord enviado"),
    ]
    k = st.columns(4, gap="medium")
    for i, (col, (valor, rotulo, sub)) in enumerate(zip(k, cards)):
        col.markdown(f"<div class='ad-big{' ad-big-destaque' if i == 0 else ''}'><div class='v'>{valor}</div><div class='l'>{_e(rotulo)}</div>"
                     f"<div class='s'>{_e(sub)}</div></div>", unsafe_allow_html=True)

    # ---- Evolução dia a dia (gráfico grande, todos os dias do mês) ----
    por_dia = (v.pivot_table(index="dia", columns="tipo", values="total", aggfunc="sum", fill_value=0)
                 .reindex(columns=tipos, fill_value=0))
    if not dias_sel:  # mostra todos os dias do mês, inclusive os sem envio
        per = pd.Period(mes, freq="M")
        ultimo = dp.envios_atualizados_ate()
        fim = min(per.end_time.normalize(), (ultimo if ultimo is not None and pd.notna(ultimo) else dp.agora_sp()).normalize())
        todos = [d.date() for d in pd.date_range(per.start_time, fim)]
        por_dia = por_dia.reindex(todos, fill_value=0)
    por_dia = por_dia.sort_index()

    st.write("")
    with st.container(key="ad-box-env-graf"):
        _md(f"<div class='ad-tit'>Evolução dos envios (dia a dia)<span>{_e(mes_rot)}</span></div>")
        if por_dia.empty:
            _md("<div class='ad-vazio'>Sem envios para os filtros escolhidos.</div>")
        else:
            datas = pd.to_datetime(pd.Index(por_dia.index))
            meses_abrev = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
            estilo = {
                "SACA": dict(cor="#0a6cff", dash="solid", largura=2.6),
                "GAYLORD": dict(cor="#00b4f0", dash="solid", largura=2.4),
                "PALLET": dict(cor="#8fb4ff", dash="dot", largura=2.4),  # 1:1 com gaylord
            }
            fig = go.Figure()
            for i, t in enumerate(tipos):
                e = estilo[t]
                fig.add_trace(go.Scatter(
                    x=datas, y=por_dia[t], name=NOME[t], mode="lines",
                    line=dict(color=e["cor"], width=e["largura"], shape="spline", smoothing=0.9, dash=e["dash"]),
                    fill="tozeroy" if i == 0 else None,
                    fillcolor="rgba(10,108,255,0.07)" if i == 0 else None,
                    hovertemplate=f"{NOME[t]}: %{{y:,.0f}}<extra></extra>",
                ))
            fig = _layout_plotly(fig, 300)
            fig.update_layout(
                margin=dict(l=4, r=4, t=30, b=4), hovermode="x unified",
                font=dict(family="Montserrat, sans-serif", size=12, color="#5b6b82"),
                legend=dict(orientation="h", y=1.14, x=1, xanchor="right",
                            font=dict(family="Montserrat, sans-serif", size=12, color="#14213d")),
                hoverlabel=dict(font=dict(family="Montserrat, sans-serif")),
            )
            # todos os dias embaixo (01, 02, 03 ...), sem grade e sem eixos
            meio_dia = pd.Timedelta(hours=14)  # folga nas pontas para o 1º e o último dia aparecerem
            fig.update_xaxes(range=[datas.min() - meio_dia, datas.max() + meio_dia],
                             tickvals=list(datas), ticktext=[f"{d:%d}" for d in datas], tickangle=0,
                             showgrid=False, showline=False, zeroline=False, ticks="",
                             tickfont=dict(family="Montserrat, sans-serif", size=11, color="#5b6b82"))
            fig.update_yaxes(visible=False, showgrid=False, zeroline=False, rangemode="tozero")
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    # ---- Tabela: Dia | Mês | Saca | Gaylord | Pallet (+ total) ----
    tab = por_dia.copy()
    tab = tab[(tab.sum(axis=1) > 0)] if dias_sel else tab
    tab = pd.DataFrame({
        "Dia": [pd.Timestamp(d).strftime("%d/%m/%Y") for d in tab.index],
        "Mês": mes_rot,
        **{NOME[t][:-1] if t != "PALLET" else "Pallet": tab[t].astype(int).values for t in tipos},
    })
    cols_qtd = [c for c in tab.columns if c not in ("Dia", "Mês")]
    total = {"Dia": "Total", "Mês": mes_rot, **{c: int(tab[c].sum()) for c in cols_qtd}}
    tab_total = pd.concat([tab, pd.DataFrame([total])], ignore_index=True)

    st.write("")
    with st.container(key="ad-box-env-tab"):
        _md(f"<div class='ad-tit'>Envios por dia<span>{_fmt(len(tab))} dia(s)</span></div>")
        corpo = "".join(
            f"<tr><td>{_e(r['Dia'])}</td><td><span class='ad-mes'>{_e(r['Mês'])}</span></td>"
            + "".join(f"<td class='b'>{_fmt(r[c])}</td>" for c in cols_qtd) + "</tr>"
            for _, r in tab.iterrows())
        rodape = ("<tr class='tot'><td>Total</td><td><span class='ad-mes'>" + _e(mes_rot) + "</span></td>"
                  + "".join(f"<td>{_fmt(total[c])}</td>" for c in cols_qtd) + "</tr>")
        cab = "".join(f"<th>{_e(c)}</th>" for c in ["Dia", "Mês"] + cols_qtd)
        _md(f"<div class='ad-grade'><table class='ad-t2'><thead><tr>{cab}</tr></thead>"
            f"<tbody>{corpo}{rodape}</tbody></table></div>")
        sufixo = minha or ("_".join(op_sel)[:40] if op_sel else "todas")
        st.download_button(
            "Exportar Excel", _excel_envios(tab_total, f"Envios — {mes_rot}"),
            file_name=f"envios_{mes}_{sufixo}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            icon=":material/download:", key="ad-env-xlsx",
        )




def _relatorios() -> None:
    from page_5 import page_5
    page_5()


def _configuracoes() -> None:
    """Configurações do portal — mesmas chaves da aba Config usadas pelo page_7."""
    import emailer

    _titulo_grande("Configurações", "Valores dos insumos, e-mail de envio das cobranças e locais de devolução.")
    cfg = dados.get_config()
    msg = st.session_state.pop("_ad_cfg_msg", None)
    if msg:
        st.toast(msg, icon=":material/check_circle:")
        _md(f"<div class='pd-faixa verde'>{_e(msg)}</div>")

    # ---- Valores dos insumos ----
    with st.container(key="ad-box-cfg-precos"):
        _md("<div class='ad-tit'>Valores dos insumos<span>preço unitário usado no saldo, nas pendências e nas cobranças</span></div>")
        with st.form("ad-cfg-precos", border=False):
            tipos = list(dp.CORES_TIPO.keys())
            cols = st.columns(len(tipos) + 1, gap="medium")
            vals = {}
            for col, t in zip(cols, tipos):
                atual = dp._to_float(cfg.get(f"preco_{t}", ""))
                vals[t] = col.number_input(f"{NOME.get(t, t.title()).upper()} (R$)", min_value=0.0, value=float(atual),
                                           step=0.5, format="%.2f", key=f"ad-cfg-preco-{t}")
            with cols[-1]:
                st.write("")
                salvar_precos = st.form_submit_button("Salvar valores", icon=":material/save:", type="primary", width="stretch")
        if salvar_precos:
            dados.set_config({f"preco_{t}": f"{v:.2f}" for t, v in vals.items()})
            st.session_state["_ad_cfg_msg"] = "Valores dos insumos salvos."
            st.rerun()

    st.write("")
    c_mail, c_dest = st.columns([1.35, 1], gap="medium")

    # ---- E-mail de envio (SMTP) ----
    with c_mail, st.container(key="ad-box-cfg-smtp"):
        ok_smtp = emailer.smtp_configurado()
        selo = "<span class='ad-pill verde'>Configurado</span>" if ok_smtp else "<span class='ad-pill vermelho'>Não configurado</span>"
        _md(f"<div class='ad-tit'><div>E-mail de envio {selo}</div><span>usado nos e-mails de pendência e no canal de dúvidas</span></div>")
        with st.form("ad-cfg-smtp", border=False):
            a, b = st.columns([2, 1], gap="small")
            host = a.text_input("Servidor SMTP", value=cfg.get("smtp_host", ""), placeholder="smtp.gmail.com")
            port = b.text_input("Porta", value=cfg.get("smtp_port", "587"), placeholder="587 ou 465")
            a, b = st.columns(2, gap="small")
            user = a.text_input("Usuário (e-mail de login)", value=cfg.get("smtp_user", ""), placeholder="cobranca@empresa.com")
            pwd = b.text_input("Senha de app", value=cfg.get("smtp_password", ""), type="password")
            remetente = st.text_input("Remetente (como aparece para as bases)", value=cfg.get("smtp_from", ""),
                                      placeholder="Portal LEVES <cobranca@empresa.com>")
            a, b = st.columns([1.4, 1], gap="small", vertical_alignment="bottom")
            suporte = a.text_input("E-mail que recebe as dúvidas das bases", value=cfg.get("email_suporte", ""),
                                   placeholder="suporte.leves@empresa.com")
            usar_tls = b.checkbox("Usar TLS (porta 587)",
                                  value=str(cfg.get("smtp_tls", "true")).lower() in ("true", "1", "sim"))
            salvar_smtp = st.form_submit_button("Salvar e-mail", icon=":material/save:", type="primary")
        if salvar_smtp:
            dados.set_config({
                "smtp_host": host.strip(), "smtp_port": port.strip(), "smtp_user": user.strip(),
                "smtp_password": pwd, "smtp_from": remetente.strip(),
                "smtp_tls": "true" if usar_tls else "false", "email_suporte": suporte.strip(),
            })
            st.session_state["_ad_cfg_msg"] = "Configuração de e-mail salva."
            st.rerun()
        st.caption("Use uma senha de app dedicada (não a senha principal do e-mail). "
                   "Ela fica guardada na aba Config da planilha: restrinja quem tem acesso a ela.")

    # ---- Locais de devolução ----
    with c_dest, st.container(key="ad-box-cfg-dest"):
        atuais = [d for d in str(cfg.get("destinos_devolucao", "")).splitlines() if d.strip()]
        _md(f"<div class='ad-tit'>Locais de devolução<span>{len(atuais)} cadastrado(s) · um por linha</span></div>")
        with st.form("ad-cfg-dest", border=False):
            destinos_txt = st.text_area("Locais (sigla - nome)", value=cfg.get("destinos_devolucao", ""), height=300,
                                        placeholder="CAJ2 - XD Cajamar II\nXDRJ - XD Rio de Janeiro III",
                                        label_visibility="collapsed")
            salvar_dest = st.form_submit_button("Salvar locais", icon=":material/save:", type="primary")
        if salvar_dest:
            dados.set_config({"destinos_devolucao": destinos_txt.strip()})
            st.session_state["_ad_cfg_msg"] = "Locais de devolução salvos."
            st.rerun()

    # ---- Testes de e-mail ----
    st.write("")
    with st.container(key="ad-box-cfg-teste"):
        _md("<div class='ad-tit'>Testar o e-mail<span>confira a conexão antes de enviar cobranças</span></div>")
        t1, t2, t3 = st.columns([1, 1, 2], gap="small", vertical_alignment="bottom")
        if t1.button("Testar conexão", icon=":material/lan:", key="ad-cfg-conexao", width="stretch"):
            with st.spinner("Testando conexão com o servidor..."):
                st.session_state["_ad_cfg_conexao"] = emailer.diagnosticar_conexao()
        if t2.button("Testar login", icon=":material/key:", key="ad-cfg-auth", width="stretch"):
            with st.spinner("Validando usuário e senha..."):
                st.session_state["_ad_cfg_auth"] = emailer.diagnosticar_autenticacao()
        with t3:
            d1, d2 = st.columns([2, 1], gap="small", vertical_alignment="bottom")
            destino_teste = d1.text_input("Enviar e-mail de teste para", placeholder="seu@email.com", key="ad-cfg-teste-dest")
            if d2.button("Enviar teste", icon=":material/send:", key="ad-cfg-teste-btn", width="stretch"):
                if not ok_smtp:
                    st.error("Salve o e-mail de envio antes de testar.")
                elif not destino_teste.strip():
                    st.error("Informe para quem enviar o teste.")
                else:
                    ok, m = emailer.enviar_email(destino_teste.strip(), "Teste — Portal LEVES",
                                                 "<p>Este é um <b>e-mail de teste</b> do Portal LEVES. "
                                                 "Se você recebeu, o envio está funcionando.</p>")
                    (st.success if ok else st.error)(m)
        for r in st.session_state.get("_ad_cfg_conexao", []) or []:
            (st.success if r.get("ok") else st.error)(f"Conexão — porta {r.get('porta')} ({r.get('etapa')}): {r.get('detalhe')}")
        auth_res = st.session_state.get("_ad_cfg_auth")
        if auth_res:
            for r in auth_res.get("detalhe", []):
                (st.success if r.get("ok") else st.error)(f"Login — porta {r.get('porta')} ({r.get('modo')}): {r.get('detalhe')}")


def _ajuda(user: dict) -> None:
    _titulo_grande("Manual e ajuda", "Abra um chamado com o suporte ou consulte o manual do portal.")
    c1, c2 = st.columns([1.7, 1], gap="medium")
    with c1, st.container(key="ad-box-aj"):
        _md("<div class='aj-cab'><div class='aj-ic'><span class='material-symbols-rounded'>support_agent</span></div>"
            "<div><b>Abrir chamado</b><span>Conte o que aconteceu e, se puder, anexe um print da tela.</span></div>"
            "<div class='aj-sla'>SLA até 24h úteis</div></div>")
        contato.form_contato(key="admin", nome=user.get("nome", ""), email=user.get("email", ""))
    with c2, st.container(key="ad-box-aj-info"):
        _md("<div class='ad-tit'>Como funciona</div>"
            "<div class='aj-passo'><span>1</span><div><b>Descreva o problema</b>O que você estava fazendo e o que apareceu na tela.</div></div>"
            "<div class='aj-passo'><span>2</span><div><b>Anexe imagens</b>Até 3 prints (PNG ou JPG, até 5 MB cada).</div></div>"
            "<div class='aj-passo'><span>3</span><div><b>Aguarde o retorno</b>Respondemos por e-mail em até <b class='az'>24 horas</b>, somente em dias úteis.</div></div>")
    st.write("")
    with st.container(key="ad-box-man"):
        a, b, _ = st.columns([2.4, 1.3, 2.7], vertical_alignment="center")
        a.markdown("<div class='ad-ajuda'><div class='ic'><span class='material-symbols-rounded'>menu_book</span></div><div>"
                   "<b>Manual do portal</b><p>Guia completo de uso do Portal Leves, em PDF.</p></div></div>",
                   unsafe_allow_html=True)
        with b:
            manual.botao_manual(key="ad-manual", label="Baixar manual (PDF)")


# ---------------------------------------------------------------------------
# entrada
# ---------------------------------------------------------------------------

def render(user: dict, logout) -> None:
    st.html(_CSS)
    scan_id = st.query_params.get("dev")
    scan_token = st.query_params.get("t")
    if scan_id and _eh_admin() and not st.session_state.get("_ad_scan_visto") == scan_id:
        st.session_state["_ad_scan_visto"] = scan_id
        st.session_state[CHAVE] = "Recebimentos"
        st.session_state[CHAVE_SUB] = "Receber no CD"
    pagina = st.session_state.get(CHAVE, "Envios")
    permitidas = {n for _, itens in _menu() for n, _ in itens}
    if pagina not in permitidas:  # também barra página de outro perfil guardada na sessão
        pagina = "Envios"
    _sidebar(user, pagina, logout)
    try:
        if pagina == "Início":
            _inicio()
        elif pagina == "Devoluções":
            _devolucao_base()
        elif pagina == "Recebimentos":
            _registrar(scan_id, scan_token)
        elif pagina == "Retornos e romaneios":
            _retornos_tela()
        elif pagina == "Envios":
            _envios()
        elif pagina == "Indicadores":
            _indicadores()
        elif pagina == "Cobranças":
            _conciliacao_cobrancas()
        elif pagina == "Pendências":
            _pendencias()
        elif pagina == "Bases e usuários":
            _bases()
        elif pagina == "Relatórios":
            _relatorios()
        elif pagina == "Configurações":
            _configuracoes()
        else:
            _ajuda(user)
    except Exception as e:  # noqa: BLE001
        st.error(f"Não foi possível carregar esta tela: {e}")
    # As telas antigas injetam o próprio CSS; reaplicar o do portal por último
    # garante que menu, ícones e barra superior mantenham o visual novo.
    st.html(_CSS_MOLDURA)
