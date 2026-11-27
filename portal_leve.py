"""
portal_leve.py — Portal da Leve (parceira Loggi), feito do zero para ser leve.

Só para o perfil de operação. Admin, GDL e Recebimento continuam no app antigo.

Princípios:
- Branco + azul Loggi (#006aff / #00baff), texto escuro, Montserrat em pesos
  normais — sem o CSS global antigo (que forçava negrito em tudo).
- 4 módulos no menu lateral, sem telas repetidas:
    Início      → o que importa agora (quanto devolver, prazo, avisos)
    Envios      → o que a Loggi mandou, mês a mês
    Devoluções  → saldo e quantidade a devolver no MESMO cartão + histórico
    Pendências  → mês a mês e cobranças da operação
- Mesmas regras de cálculo do portal (data_processing); só a tela é nova.
"""

from __future__ import annotations

import base64
import functools
import html
import os
import uuid
from datetime import datetime

import pandas as pd
import streamlit as st

import contato
import data_extraction as dados
import data_processing as dp
import manual
import romaneio

CHAVE_PAGINA = "leve_pagina"
PAGINAS = [
    ("Início", ":material/home:"),
    ("Envios", ":material/local_shipping:"),
    ("Devoluções", ":material/assignment_return:"),
    ("Pendências", ":material/pending_actions:"),
]
TIPOS = ["SACA", "GAYLORD", "PALLET"]
NOME_TIPO = {"SACA": "Sacas", "GAYLORD": "Gaylords", "PALLET": "Pallets"}
STATUS = {  # rótulo, classe do selo
    "EM_TRANSITO": ("Em trânsito", "azul"),
    "RECEBIDO": ("Recebida no CD", "verde"),
    "CONFERIDO": ("Conferida", "verde"),
    "DIVERGENTE": ("Divergente", "amarelo"),
    "CANCELADO": ("Cancelada", "cinza"),
}

_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--azul:#006aff;--azul-claro:#00baff;--azul-bg:#eaf3ff;--texto:#1a1a1a;--texto-2:#626d7c;
  --linha:#e7ecf2;--fundo:#f7f9fc;--amarelo-bg:#fbeccc;--amarelo:#8a5a00;--verde-bg:#e3f6ee;--verde:#0f7b5f}
[data-testid="stApp"] *:not([data-testid="stIconMaterial"]):not(.material-symbols-rounded){font-family:Montserrat,sans-serif!important}
[data-testid="stApp"]{background:#fff;color:var(--texto)}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"],[data-testid="stSidebarCollapseButton"],[data-testid="stSidebarHeader"]{display:none!important}
[data-testid="stMainBlockContainer"]{max-width:1120px;padding:28px 40px 60px!important}
section[data-testid="stSidebar"]{width:260px!important;min-width:260px!important;max-width:260px!important;transform:none!important;visibility:visible!important}
section[data-testid="stSidebar"]>div:first-child{background:#fff!important;border-right:1px solid var(--linha);padding:20px 14px!important}
[data-testid="stSidebar"] button[aria-label*="Close"],[data-testid="stSidebar"] button[title*="Close"],[data-testid="stSidebar"] button[aria-label*="Fechar"]{display:none!important}
.lv-logo{display:flex;align-items:center;gap:10px;margin:0 6px 18px}
.lv-logo img{height:26px}
.lv-logo span{font-size:13px;color:var(--texto-2);border-left:1px solid var(--linha);padding-left:10px}
.lv-op{background:var(--fundo);border-radius:12px;padding:10px 12px;margin:0 2px 18px}
.lv-op b{display:block;font-size:13px;font-weight:600;color:var(--texto)}
.lv-op span{font-size:12px;color:var(--texto-2)}
.lv-menu-rot{font-size:11px;letter-spacing:.08em;color:#8a95a5;margin:6px 8px 6px;text-transform:uppercase}
[data-testid="stSidebar"] [data-testid="stButton"] button{justify-content:flex-start!important;border:0!important;background:transparent!important;
  color:var(--texto)!important;font-weight:500!important;font-size:15px!important;min-height:42px!important;border-radius:10px!important;box-shadow:none!important;padding:0 12px!important}
[data-testid="stSidebar"] [data-testid="stButton"] button>div,[data-testid="stSidebar"] [data-testid="stDownloadButton"] button>div{justify-content:flex-start!important;width:100%;gap:10px}
[data-testid="stSidebar"] [data-testid="stButton"] button p{text-align:left!important}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover{background:var(--fundo)!important}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"]{background:var(--azul-bg)!important;color:var(--azul)!important;font-weight:600!important}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] *{color:var(--azul)!important}
[data-testid="stSidebar"] [data-testid="stDownloadButton"] button{border:0!important;background:transparent!important;color:var(--texto-2)!important;font-weight:500!important;justify-content:flex-start!important;padding:0 12px!important}
[data-testid="stSidebar"] [data-testid="stExpander"]{border:0!important}
[data-testid="stSidebar"] [data-testid="stExpander"] summary{padding-left:12px!important;color:var(--texto-2)!important;font-weight:500}
.lv-sep{height:1px;background:var(--linha);margin:14px 6px}
.lv-h1{font-size:28px;font-weight:600;color:var(--texto);margin:0 0 4px;line-height:1.2}
.lv-sub{font-size:14px;color:var(--texto-2);margin:0 0 22px}
.lv-rot{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:#8a95a5;margin:26px 0 10px}
.lv-card{background:#fff;border:1px solid var(--linha);border-radius:18px;padding:20px 22px}
.lv-hero-l{font-size:14px;color:var(--texto-2)}
.lv-hero-n{font-size:40px;font-weight:700;color:var(--texto);line-height:1.1;margin:4px 0}
.lv-hero-n small{font-size:16px;font-weight:500;color:var(--texto-2);margin-left:6px}
.lv-chips{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 4px}
.lv-chip{background:var(--fundo);border-radius:999px;padding:6px 12px;font-size:13px;color:var(--texto)}
.lv-chip b{font-weight:700}
.lv-prazo{font-size:14px;color:var(--texto-2);margin-top:8px}
.lv-prazo b{color:var(--texto);font-weight:600}
.lv-prazo .urg{color:var(--amarelo);font-weight:700}
.lv-aviso{background:var(--amarelo-bg);border-radius:18px;padding:18px 20px;font-size:14px;color:#3d3d3d;line-height:1.5}
.lv-aviso b{color:var(--texto)}
.lv-aviso .t{font-size:16px;font-weight:700;color:var(--texto);margin-bottom:4px}
.lv-info{background:var(--azul-bg);border-radius:18px;padding:18px 20px;font-size:14px;color:#2b3a52;line-height:1.5}
.lv-info .t{font-size:16px;font-weight:700;color:var(--texto);margin-bottom:4px}
.lv-kpi{border:1px solid var(--linha);border-radius:16px;padding:14px 18px}
.lv-kpi .l{font-size:13px;color:var(--texto-2)}
.lv-kpi .v{font-size:26px;font-weight:700;color:var(--texto);margin-top:4px}
.lv-kpi .s{font-size:12px;color:var(--texto-2)}
.lv-linha{display:flex;align-items:center;gap:14px;padding:14px 4px;border-bottom:1px solid var(--linha);font-size:14px}
.lv-linha:last-child{border-bottom:0}
.lv-linha .p{flex:1;min-width:0}
.lv-linha .p b{display:block;font-weight:600;color:var(--texto)}
.lv-linha .p span{font-size:13px;color:var(--texto-2)}
.lv-linha .n{text-align:right;min-width:110px}
.lv-linha .n b{display:block;font-size:18px;font-weight:700}
.lv-linha .n span{font-size:12px;color:var(--texto-2)}
.lv-selo{display:inline-block;border-radius:999px;padding:4px 12px;font-size:12px;font-weight:600;white-space:nowrap}
.lv-selo.azul{background:var(--azul-bg);color:#0050c8}.lv-selo.verde{background:var(--verde-bg);color:var(--verde)}
.lv-selo.amarelo{background:var(--amarelo-bg);color:var(--amarelo)}.lv-selo.cinza{background:#eef0f3;color:#5b6472}
[class*="st-key-lv-insbox-"]{background:#fff;border:1px solid var(--linha);border-radius:16px;padding:16px 18px 14px!important;gap:8px!important}
.lv-ins{padding:0}
.lv-ins .nome{font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--texto-2);font-weight:600}
.lv-ins .saldo{font-size:34px;font-weight:700;color:var(--texto);line-height:1.1;margin-top:6px}
.lv-ins .saldo small{font-size:14px;font-weight:500;color:var(--texto-2);margin-left:4px}
.lv-ins .det{font-size:12px;color:var(--texto-2);margin:4px 0 10px}
.lv-ins.ok .saldo{color:var(--verde);font-size:22px}
[data-testid="stForm"]{border:0!important;padding:0!important}
[data-testid="stMain"] [data-testid="stButton"] button[kind="primary"],[data-testid="stFormSubmitButton"] button{background:var(--azul)!important;border:0!important;color:#fff!important;
  border-radius:14px!important;min-height:50px!important;font-weight:600!important;font-size:15px!important;padding:0 26px!important}
[data-testid="stMain"] [data-testid="stButton"] button[kind="primary"]:hover,[data-testid="stFormSubmitButton"] button:hover{background:#0057d1!important}
[data-testid="stMain"] [data-testid="stNumberInput"] input{font-size:20px!important;font-weight:600!important}
.lv-total{font-size:14px;color:var(--texto-2);margin:4px 0 0}
.lv-total b{color:var(--texto)}
.lv-tab{width:100%;border-collapse:separate;border-spacing:0;font-size:14px}
.lv-tab th{background:#f4f6fa;color:#5f6b7d;font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:14px;text-align:center}
.lv-tab th:first-child{border-radius:10px 0 0 0}.lv-tab th:last-child{border-radius:0 10px 0 0}
.lv-tab td{padding:13px 14px;border-bottom:1px solid #edf0f5;text-align:center;color:#1f2a3d}
.lv-tab tr.tot td{border-top:2px solid #d9e2f0;border-bottom:0;font-weight:800;background:#fafcff}
.lv-mes{display:inline-block;background:#e6f0ff;color:#0050c8;font-weight:700;font-size:13px;border-radius:999px;padding:5px 14px}
[class*='st-key-ct_anexo_'] [data-testid='stFileUploaderDropzoneInstructions'] span{display:none!important}
[class*='st-key-ct_anexo_'] [data-testid='stFileUploaderDropzoneInstructions']::after{content:'PNG ou JPG · até 3 imagens de 5 MB';font-size:12px;color:#6b7a90}
@media (max-width:800px){[data-testid="stMainBlockContainer"]{padding:18px 16px 40px!important}.lv-hero-n{font-size:32px}}
</style>
"""


# ---------------------------------------------------------------------------
# utilidades
# ---------------------------------------------------------------------------

def _fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def _e(v) -> str:
    return html.escape(str(v))


def _md(h: str) -> None:
    st.markdown(h, unsafe_allow_html=True)


@functools.lru_cache(maxsize=4)
def _img_b64(nome: str) -> str:
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), nome)
    if not os.path.exists(caminho):
        return ""
    with open(caminho, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _ir(pagina: str) -> None:
    st.session_state[CHAVE_PAGINA] = pagina
    st.rerun()


def _dias_uteis(prazo: pd.Timestamp) -> int:
    ini = dp.agora_sp().normalize() + pd.Timedelta(days=1)
    fim = prazo.normalize()
    if fim < ini:
        return 0
    return int(sum(1 for d in pd.date_range(ini, fim) if d.weekday() < 5))


def _txt_dias(d: int) -> str:
    return "1 dia útil" if d == 1 else f"{d} dias úteis"


def _plural(tipo: str, n: int) -> str:
    nome = NOME_TIPO.get(tipo, tipo.title()).lower()
    return nome[:-1] if n == 1 else nome


def _selo(status: str) -> str:
    rot, cls = STATUS.get(str(status).upper(), (str(status), "cinza"))
    return f"<span class='lv-selo {cls}'>{_e(rot)}</span>"


def _cabecalho(titulo: str, sub: str) -> None:
    _md(f"<div class='lv-h1'>{_e(titulo)}</div><div class='lv-sub'>{sub}</div>")


def _atualizado_txt() -> str:
    ate = dp.envios_atualizados_ate()
    return f"envios atualizados até {ate.strftime('%d/%m/%Y')}" if ate is not None and pd.notna(ate) else ""


def _minhas_devolucoes(destino: str) -> pd.DataFrame:
    devs = dp.devolucoes_df()
    if devs.empty:
        return devs
    m = devs[devs["destino_norm"] == dp._normalizar(destino)]
    return m.sort_values("dt_criacao", ascending=False)


def _resumo_itens(id_dev: str) -> tuple[str, list[dict]]:
    its = dp.itens_da_devolucao(id_dev)
    lista = [{"tipo": str(r["tipo"]).upper(), "qtd_declarada": int(r["qtd_declarada"])} for _, r in its.iterrows()]
    ordem = {t: i for i, t in enumerate(TIPOS)}
    lista.sort(key=lambda x: ordem.get(x["tipo"], 9))
    txt = " · ".join(f"{_fmt(i['qtd_declarada'])} {_plural(i['tipo'], i['qtd_declarada'])}"
                     for i in lista if i["qtd_declarada"])
    return txt, lista


def _linha_devolucao(d) -> str:
    resumo, _ = _resumo_itens(d["id"])
    dt = d.get("dt_criacao")
    data_txt = dt.strftime("%d/%m/%Y") if pd.notna(dt) else str(d.get("data_criacao", ""))
    comp = str(d.get("competencia") or "")
    comp_txt = f" · ref. {dp.rotulo_mes(comp)}" if len(comp) == 7 else ""
    return (f"<div class='lv-linha'><div class='p'><b>{_e(d['id'])}</b>"
            f"<span>{_e(data_txt + comp_txt)} · {_e(resumo or str(d.get('total_declarado', '')) + ' itens')}</span></div>"
            f"{_selo(d['status'])}</div>")


# ---------------------------------------------------------------------------
# menu lateral
# ---------------------------------------------------------------------------

def _sidebar(user: dict, pagina: str, logout) -> None:
    with st.sidebar:
        logo = _img_b64("image_logo_loggi_azul.png")
        img = f'<img src="data:image/png;base64,{logo}" alt="Loggi">' if logo else ""
        _md(f"<div class='lv-logo'>{img}<span>Portal Leves</span></div>")
        _md(f"<div class='lv-op'><b>{_e(user.get('nome', ''))}</b><span>Operação {_e(user.get('destino', ''))}</span></div>")
        _md("<div class='lv-menu-rot'>Menu</div>")
        for nome, icone in PAGINAS:
            if st.button(nome, icon=icone, key=f"lv-nav-{nome}", width="stretch",
                         type="primary" if nome == pagina else "secondary"):
                _ir(nome)
        _md("<div class='lv-sep'></div>")
        if st.button("Atualizar dados", icon=":material/refresh:", key="lv-atualizar", width="stretch"):
            dados.limpar_cache()
            st.rerun()
        manual.botao_manual(key="lv-manual", label="Manual do portal")
        with st.expander("Falar com o suporte"):
            contato.form_contato(key="leve", nome=user.get("nome", ""), email=user.get("email", ""))
        if st.button("Sair", icon=":material/logout:", key="lv-sair", width="stretch"):
            st.session_state.pop(CHAVE_PAGINA, None)
            logout()
            st.rerun()


# ---------------------------------------------------------------------------
# Início
# ---------------------------------------------------------------------------

def _inicio(user: dict) -> None:
    destino = str(user.get("destino", "")).strip()
    primeiro = str(user.get("nome", "")).split(" ")[0] or "olá"
    _cabecalho(f"Olá, {primeiro}", f"Operação {_e(destino)} · {_e(_atualizado_txt())}")

    pend = dp.pendencias_da_operacao(destino)
    no_prazo = pend[pend["situacao"] == "No prazo"] if not pend.empty else pend
    vencidos = pend[(pend["situacao"] == "Prazo encerrado") & (pend["saldo"] > 0)] if not pend.empty else pend

    c1, c2 = st.columns([1.7, 1], gap="medium")
    with c1:
        with st.container(border=False):
            if not no_prazo.empty and int(no_prazo["saldo"].sum()) > 0:
                mes = no_prazo["mes"].max()
                g = no_prazo[no_prazo["mes"] == mes]
                prazo = g["prazo"].iloc[0]
                dias = _dias_uteis(prazo)
                chips = "".join(f"<span class='lv-chip'><b>{_fmt(r['saldo'])}</b> {_plural(r['tipo'], r['saldo'])}</span>"
                                for _, r in g.iterrows() if r["saldo"] > 0)
                urg = " class='urg'" if dias <= 3 else ""
                _md(f"<div class='lv-card'><div class='lv-hero-l'>Para devolver de {_e(dp.rotulo_mes(mes))}</div>"
                    f"<div class='lv-hero-n'>{_fmt(g['saldo'].sum())}<small>itens</small></div>"
                    f"<div class='lv-chips'>{chips}</div>"
                    f"<div class='lv-prazo'>Prazo <b>{prazo.strftime('%d/%m/%Y')}</b> · <span{urg}>{_txt_dias(dias)}</span>"
                    f" · valor {dp.fmt_brl(g['valor'].sum())}</div></div>")
                st.write("")
                if st.button("Devolver agora", type="primary", key="lv-ini-devolver"):
                    _ir("Devoluções")
            else:
                _md("<div class='lv-card'><div class='lv-hero-l'>Devoluções</div>"
                    "<div class='lv-hero-n' style='font-size:26px'>Nada a devolver no momento</div>"
                    "<div class='lv-prazo'>Quando chegarem novos envios, o saldo aparece aqui.</div></div>")
    with c2:
        if not vencidos.empty:
            n = vencidos["mes"].nunique()
            meses = " e ".join(dp.rotulo_mes(m).split("/")[0].lower() for m in sorted(set(vencidos["mes"])))
            _md(f"<div class='lv-aviso'><div class='t'>Prazo encerrado</div>"
                f"<b>{_fmt(vencidos['saldo'].sum())} itens</b> ({dp.fmt_brl(vencidos['valor'].sum())}) de "
                f"{_e(meses)} não podem mais ser devolvidos e entram na cobrança.</div>")
            st.write("")
            if st.button("Ver pendências", key="lv-ini-pend", type="tertiary", icon=":material/arrow_forward:"):
                _ir("Pendências")
        else:
            _md("<div class='lv-info'><div class='t'>Tudo dentro do prazo</div>"
                "Nenhum mês com prazo vencido. Devolva o saldo até a data indicada para evitar cobrança.</div>")

    if not pend.empty:
        mes_atual = pend["mes"].max()
        m = pend[pend["mes"] == mes_atual]
        enviados, devolvidos = int(m["enviado"].sum()), int(m["devolvido"].sum())
        devs = _minhas_devolucoes(destino)
        transito = int((devs["status"] == dp.STATUS_TRANSITO).sum()) if not devs.empty else 0
        _md(f"<div class='lv-rot'>{_e(dp.rotulo_mes(mes_atual))}</div>")
        k = st.columns(3, gap="medium")
        k[0].markdown(f"<div class='lv-kpi'><div class='l'>Recebidos da Loggi</div><div class='v'>{_fmt(enviados)}</div>"
                      "<div class='s'>sacas, gaylords e pallets</div></div>", unsafe_allow_html=True)
        pct = round(100 * devolvidos / enviados) if enviados else 0
        k[1].markdown(f"<div class='lv-kpi'><div class='l'>Devolvidos</div><div class='v'>{_fmt(devolvidos)}</div>"
                      f"<div class='s'>{pct}% do que chegou</div></div>", unsafe_allow_html=True)
        k[2].markdown(f"<div class='lv-kpi'><div class='l'>A caminho do CD</div><div class='v'>{_fmt(transito)}</div>"
                      "<div class='s'>devoluções em trânsito</div></div>", unsafe_allow_html=True)

    devs = _minhas_devolucoes(destino)
    if not devs.empty:
        _md("<div class='lv-rot'>Últimas devoluções</div>")
        _md("<div class='lv-card' style='padding:6px 20px'>" + "".join(_linha_devolucao(d) for _, d in devs.head(3).iterrows()) + "</div>")


# ---------------------------------------------------------------------------
# Envios
# ---------------------------------------------------------------------------

def _envios(user: dict) -> None:
    _cabecalho("Envios", f"O que a Loggi enviou para a sua operação · {_e(_atualizado_txt())}")
    df = dp.envios_do_usuario(user)
    if df.empty:
        st.info("Nenhum envio encontrado para a sua operação.")
        return
    meses = sorted(df["mes"].unique(), reverse=True)
    rot = {dp.rotulo_mes(m): m for m in meses}
    escolha = st.selectbox("Mês", list(rot), index=0, label_visibility="collapsed")
    mes = rot[escolha]
    d = df[df["mes"] == mes]
    tot = d.groupby("tipo")["total"].sum()
    cols = st.columns(3, gap="medium")
    for col, t in zip(cols, TIPOS):
        sub = "1 por gaylord recebido" if t == "PALLET" else f"em {escolha}"
        col.markdown(f"<div class='lv-kpi'><div class='l'>{NOME_TIPO[t]}</div><div class='v'>{_fmt(tot.get(t, 0))}</div>"
                     f"<div class='s'>{_e(sub)}</div></div>", unsafe_allow_html=True)

    _md("<div class='lv-rot'>Dia a dia</div>")
    tab = (d.pivot_table(index="dia", columns="tipo", values="total", aggfunc="sum", fill_value=0)
             .reindex(columns=TIPOS, fill_value=0).sort_index(ascending=False))
    tab.index = pd.to_datetime(tab.index).strftime("%d/%m/%Y")
    tab = tab.rename(columns=NOME_TIPO).reset_index().rename(columns={"dia": "Data"})
    st.dataframe(tab, hide_index=True, width="stretch",
                 column_config={c: st.column_config.NumberColumn(c, format="%d") for c in NOME_TIPO.values()})
    st.download_button("Baixar CSV", tab.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"envios_{mes}.csv", mime="text/csv", icon=":material/download:")


# ---------------------------------------------------------------------------
# Devoluções — saldo e quantidade no mesmo cartão
# ---------------------------------------------------------------------------

def _acima_do_saldo(destino: str, mes: str, itens: list[dict]) -> list[tuple]:
    """Confere o saldo com dados frescos na hora de gravar (mesma regra do page_3)."""
    dados.limpar_cache("devolucoes", "itens")
    atual = dp.pending_mes_tipo(destino, mes)
    return [(i["tipo"], i["qtd_declarada"], int(atual.get(i["tipo"], 0)))
            for i in itens if i["qtd_declarada"] > int(atual.get(i["tipo"], 0))]


def _devolucoes(user: dict) -> None:
    destino = str(user.get("destino", "")).strip()
    _cabecalho("Devoluções", "Informe quanto vai devolver de cada insumo, a placa do veículo e gere o romaneio.")

    ultimo = st.session_state.pop("lv_dev_criada", None)
    if ultimo:
        st.success(f"Devolução **{ultimo['id']}** registrada. Baixe o romaneio e envie impresso junto com os itens.")
        st.download_button("Baixar romaneio (PDF)", ultimo["pdf"], file_name=f"{ultimo['id']}.pdf",
                           mime="application/pdf", type="primary", icon=":material/description:",
                           key=f"lv-rom-novo-{ultimo['id']}")

    elegiveis = dp.competencias_elegiveis(destino)
    if not elegiveis:
        _md("<div class='lv-info'><div class='t'>Nenhum mês aberto para devolução</div>"
            "Os prazos dos meses anteriores já encerraram. Novos envios liberam saldo automaticamente.</div>")
    else:
        rot = {dp.rotulo_mes(m): m for m in elegiveis}
        if len(elegiveis) > 1:
            _md("<div class='lv-rot' style='margin-top:0'>Os itens que você vai devolver são de qual mês?</div>")
            escolha = st.segmented_control("Mês", list(rot), default=None, key="lv-dev-mes",
                                           label_visibility="collapsed")
            if not escolha:
                st.caption("Escolha o mês para ver o saldo e registrar a devolução.")
        else:
            escolha = list(rot)[0]
        if escolha:
            _form_devolucao(user, destino, rot[escolha], escolha)

    devs = _minhas_devolucoes(destino)
    _md("<div class='lv-rot'>Minhas devoluções</div>")
    if devs.empty:
        st.caption("Nenhuma devolução registrada ainda.")
        return
    _md("<div class='lv-card' style='padding:6px 20px'>" + "".join(_linha_devolucao(d) for _, d in devs.head(15).iterrows()) + "</div>")

    c1, c2 = st.columns([2, 1], vertical_alignment="bottom")
    ids = devs["id"].astype(str).tolist()
    sel = c1.selectbox("Romaneio ou cancelamento", ids, index=None, placeholder="Escolha uma devolução",
                       key="lv-dev-sel")
    if sel:
        d = devs[devs["id"].astype(str) == sel].iloc[0]
        _, lista = _resumo_itens(sel)
        with c2:
            st.download_button("Baixar romaneio", romaneio.gerar_romaneio_pdf(d.to_dict(), lista, dp.base_url()),
                               file_name=f"{sel}.pdf", mime="application/pdf", icon=":material/description:",
                               key=f"lv-rom-{sel}")
        if d["status"] == dp.STATUS_TRANSITO:
            if st.button(f"Cancelar a devolução {sel}", key=f"lv-can-{sel}", icon=":material/close:"):
                dados.atualizar_devolucao(sel, {"status": dp.STATUS_CANCELADO})
                st.rerun()


def _form_devolucao(user: dict, destino: str, mes: str, rotulo: str) -> None:
    resumo = dp.resumo_devolucao(destino, mes).set_index("tipo")
    pend = dp.pending_mes_tipo(destino, mes)  # saldo que pode ser devolvido
    pr = dp.precos()
    prazo = dp.prazo_devolucao(mes)
    dias = _dias_uteis(prazo)
    valor = sum(int(pend.get(t, 0)) * float(pr.get(t, 0) or 0) for t in TIPOS)
    urg = " class='urg'" if dias <= 3 else ""
    _md(f"<div class='lv-prazo' style='margin:0 0 14px'>Saldo de <b>{_e(rotulo)}</b> · prazo <b>{prazo.strftime('%d/%m/%Y')}</b>"
        f" · <span{urg}>{_txt_dias(dias)}</span>" + (f" · valor do saldo <b>{dp.fmt_brl(valor)}</b>" if valor else "") + "</div>")

    if not any(int(pend.get(t, 0)) > 0 for t in TIPOS):
        _md(f"<div class='lv-info'><div class='t'>Tudo devolvido em {_e(rotulo)}</div>"
            "Não há saldo para devolver neste mês. Novos envios liberam saldo automaticamente.</div>")
        return

    with st.form("lv-form-dev", clear_on_submit=True):
        cols = st.columns(3, gap="medium")
        qtds = {}
        for col, t in zip(cols, TIPOS):
            saldo = int(pend.get(t, 0))
            env = int(resumo.loc[t, "enviado"]) if t in resumo.index else 0
            dev = int(resumo.loc[t, "em_transito"] + resumo.loc[t, "recebido"]) if t in resumo.index else 0
            with col, st.container(key=f"lv-insbox-{t}"):
                if saldo > 0:
                    _md(f"<div class='lv-ins'><div class='nome'>{NOME_TIPO[t]}</div>"
                        f"<div class='saldo'>{_fmt(saldo)}<small>com você</small></div>"
                        f"<div class='det'>Recebeu {_fmt(env)} · já devolveu {_fmt(dev)}"
                        f"{' · 1 por gaylord' if t == 'PALLET' else ''}</div></div>")
                    qtds[t] = st.number_input(f"Vou devolver ({NOME_TIPO[t].lower()})", min_value=0,
                                              max_value=saldo, step=1, value=0, key=f"lv-q-{t}")
                else:
                    _md(f"<div class='lv-ins ok'><div class='nome'>{NOME_TIPO[t]}</div>"
                        f"<div class='saldo'>Tudo devolvido</div><div class='det'>Recebeu {_fmt(env)}</div></div>")
        c1, c2 = st.columns([1, 2], gap="medium")
        placa = c1.text_input("Placa do veículo", placeholder="ABC1D23")
        obs = c2.text_input("Observação (opcional)", placeholder="Alguma particularidade desta devolução")
        enviar = st.form_submit_button("Gerar devolução e romaneio", icon=":material/assignment_return:")

    if not enviar:
        return
    itens = [{"tipo": t, "qtd_declarada": int(q)} for t, q in qtds.items() if q > 0]
    placa_norm = "".join(str(placa or "").upper().split()).replace("-", "")
    if not itens:
        st.error("Informe a quantidade de pelo menos um insumo.")
        return
    if not placa_norm:
        st.error("Informe a placa do veículo.")
        return
    excedentes = _acima_do_saldo(destino, mes, itens)
    if excedentes:
        st.error("O saldo mudou e esta devolução passou do limite. Nada foi registrado. Saldo atual: "
                 + ", ".join(f"{NOME_TIPO.get(t, t)} {_fmt(disp)} (você informou {_fmt(q)})" for t, q, disp in excedentes))
        return
    dev = {
        "id": dados.proximo_codigo_devolucao(), "token": uuid.uuid4().hex,
        "data_criacao": datetime.now(dp.TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "usuario": user.get("nome", user.get("usuario", "")), "destino": destino,
        "status": dp.STATUS_TRANSITO, "total_declarado": sum(i["qtd_declarada"] for i in itens),
        "total_recebido": "", "data_recebimento": "", "recebido_por": "", "obs": obs,
        "placa": placa_norm, "competencia": mes,
    }
    dados.criar_devolucao(dev, itens)  # pode trocar o id se houve concorrência
    st.session_state["lv_dev_criada"] = {
        "id": dev["id"], "pdf": romaneio.gerar_romaneio_pdf(dev, itens, dp.base_url()),
    }
    st.rerun()


# ---------------------------------------------------------------------------
# Pendências (inclui cobranças)
# ---------------------------------------------------------------------------

_SIT = {"No prazo": "azul", "Prazo encerrado": "amarelo", "Cobrado": "cinza", "Em dia": "verde"}


def _cobrancas(destino: str) -> pd.DataFrame:
    """Notas de crédito SÓ da própria operação (mesma leitura do admin)."""
    notas = dp.notas_credito()
    if notas.empty:
        return notas
    return notas[notas["destino_norm"] == dp._normalizar(destino)].sort_values(["mes", "nota"], ascending=[False, True])


def _pendencias(user: dict) -> None:
    destino = str(user.get("destino", "")).strip()
    _cabecalho("Pendências", "O que ainda falta devolver, mês a mês, e as cobranças da sua operação.")
    pend = dp.pendencias_da_operacao(destino)
    if pend.empty:
        st.info("Nenhum envio encontrado para a sua operação.")
        return
    abertos = pend[pend["situacao"].isin(["No prazo", "Prazo encerrado"])]
    venc = pend[(pend["situacao"] == "Prazo encerrado") & (pend["saldo"] > 0)]
    cob = _cobrancas(destino)
    k = st.columns(3, gap="medium")
    k[0].markdown(f"<div class='lv-kpi'><div class='l'>Itens em aberto</div><div class='v'>{_fmt(abertos['saldo'].sum())}</div>"
                  f"<div class='s'>{dp.fmt_brl(abertos['valor'].sum())}</div></div>", unsafe_allow_html=True)
    k[1].markdown(f"<div class='lv-kpi'><div class='l'>Com prazo encerrado</div><div class='v'>{_fmt(venc['saldo'].sum())}</div>"
                  f"<div class='s'>{dp.fmt_brl(venc['valor'].sum())}</div></div>", unsafe_allow_html=True)
    total_cob = float(cob["valor"].sum()) if not cob.empty else 0.0
    k[2].markdown(f"<div class='lv-kpi'><div class='l'>Já cobrado</div><div class='v'>{dp.fmt_brl(total_cob)}</div>"
                  f"<div class='s'>{len(cob)} nota(s) de crédito</div></div>", unsafe_allow_html=True)

    _md("<div class='lv-rot'>Mês a mês</div>")
    linhas = []
    for mes, g in pend.groupby("mes", sort=False):
        sit = g["situacao"].iloc[0]
        prazo = g["prazo"].iloc[0]
        det = " · ".join(f"{_fmt(r['saldo'])} {_plural(r['tipo'], r['saldo'])}" for _, r in g.iterrows() if r["saldo"] > 0) \
            or "nada a devolver"
        quando = f"prazo {prazo.strftime('%d/%m/%Y')}"
        if sit == "No prazo":
            quando += f" · {_txt_dias(_dias_uteis(prazo))}"
        linhas.append(
            f"<div class='lv-linha'><div class='p'><b>{_e(g['rotulo'].iloc[0])}</b><span>{_e(det)} · {_e(quando)}</span></div>"
            f"<div class='n'><b>{_fmt(g['saldo'].sum())}</b><span>{dp.fmt_brl(g['valor'].sum())}</span></div>"
            f"<span class='lv-selo {_SIT.get(sit, 'cinza')}'>{_e(sit)}</span></div>")
    _md("<div class='lv-card' style='padding:6px 20px'>" + "".join(linhas) + "</div>")
    if not venc.empty:
        st.caption("Prazo encerrado: esses itens não podem mais ser devolvidos e entram na cobrança "
                   "quando o mês for fechado.")
    if not pend[pend["situacao"] == "No prazo"].empty:
        if st.button("Devolver agora", type="primary", key="lv-pend-devolver"):
            _ir("Devoluções")

    _md("<div class='lv-rot'>Notas de crédito</div>")
    if cob.empty:
        _md("<div class='lv-info'><div class='t'>Nenhuma nota de crédito</div>"
            "Sua operação não tem cobrança por insumos não devolvidos.</div>")
    else:
        linhas = "".join(
            f"<tr><td><b>{_e(r['nota'])}</b></td><td><span class='lv-mes'>{_e(r['rotulo'])}</span></td>"
            f"<td>{_e(r['dt'].strftime('%d/%m/%Y') if pd.notna(r['dt']) else '—')}</td>"
            f"<td><b>{dp.fmt_brl(r['valor'])}</b></td></tr>"
            for _, r in cob.iterrows())
        _md("<table class='lv-tab'><thead><tr><th>Nota</th><th>Competência</th><th>Emissão</th><th>Valor</th></tr></thead>"
            f"<tbody>{linhas}<tr class='tot'><td>Total</td><td></td><td></td><td>{dp.fmt_brl(total_cob)}</td></tr></tbody></table>")
        st.caption("Notas de crédito referentes aos insumos que não foram devolvidos dentro do prazo, uma por mês.")


# ---------------------------------------------------------------------------
# entrada
# ---------------------------------------------------------------------------

def render(user: dict, logout) -> None:
    st.html(_CSS)
    pagina = st.session_state.get(CHAVE_PAGINA, "Início")
    if pagina not in dict(PAGINAS):
        pagina = "Início"
    _sidebar(user, pagina, logout)
    {"Início": _inicio, "Envios": _envios, "Devoluções": _devolucoes, "Pendências": _pendencias}[pagina](user)
