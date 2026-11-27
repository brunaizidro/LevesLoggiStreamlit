"""
tema.py — identidade visual Loggi do Portal LEVES (guia "Território de Marca").

Paleta oficial: Azul Claro #00baff (protagonista), Azul Médio #006aff (apoio,
botões), Azul Escuro #002766 (detalhes e texto — nunca dominante), branco.
Degradê: só linear, só Azul Claro → Azul Médio, usado apenas no cabeçalho.
Fonte: Montserrat. Ícones: linha (Tabler, padrão Material outline).

Uso: chame `aplicar_tema()` no início da página (depois do CSS próprio dela,
para que estas regras prevaleçam) e use os componentes abaixo.
"""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

AZUL_CLARO = "#00baff"
AZUL_MEDIO = "#006aff"
AZUL_ESCURO = "#002766"

_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.19.0/dist/tabler-icons.min.css');
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');
:root{
  --lv-claro:#00baff; --lv-medio:#006aff; --lv-escuro:#002766;
  --lv-fundo:#f6f8fb; --lv-linha:#e6ebf2; --lv-texto:#1a1a1a; --lv-texto-2:#5f6b7a;
  --lv-azul-bg:#e6f2ff; --lv-cinza-bg:#eef1f5;
  --lv-ok:#0f7b5f; --lv-ok-bg:#e3f6ef; --lv-alerta:#8a5a00; --lv-alerta-bg:#fff4d9;
  --lv-erro:#a12a2a; --lv-erro-bg:#fdeaea;
  --lv-degrade:linear-gradient(90deg,#00baff 25%,#006aff 75%);
}
.lv-topo{background:transparent;color:var(--lv-texto);padding:6px 0 4px;margin:0 0 18px;text-align:left}
.lv-topo h1,.lv-topo p,.lv-topo .lv-trilha,.lv-sec h2,.lv-mod h3,.lv-mod p{text-align:left!important}
.lv-topo .lv-trilha{display:flex;align-items:center;gap:6px;font-size:14px;font-weight:500;color:var(--lv-texto)}
.lv-topo .lv-trilha i{font-size:18px}
.lv-topo h1{color:var(--lv-texto)!important;font-size:30px!important;font-weight:600!important;margin:18px 0 4px!important;padding:0!important;line-height:1.2!important}
.lv-topo p{color:var(--lv-texto-2)!important;margin:0!important;font-size:14px;font-weight:400;max-width:720px}
.lv-topo .lv-atualizado{display:inline-flex;align-items:center;gap:6px;margin-top:10px;background:var(--lv-azul-bg);color:#0050c8;border-radius:999px;padding:5px 12px;font-size:12px;font-weight:500}
.lv-card{background:#fff;border:1px solid var(--lv-linha);border-radius:14px;padding:18px 20px;box-sizing:border-box}
.lv-prazo{display:flex;align-items:center;gap:16px;margin:0 0 16px}
.lv-prazo .lv-ico{width:46px;height:46px;flex:0 0 46px;border-radius:12px;background:var(--lv-azul-bg);display:flex;align-items:center;justify-content:center;color:var(--lv-medio);font-size:24px}
.lv-prazo .lv-txt{flex:1;color:var(--lv-texto)}
.lv-prazo .lv-txt b{font-size:16px;font-weight:700}
.lv-prazo .lv-txt div{color:var(--lv-texto-2);font-size:13px;margin-top:2px}
.lv-prazo.lv-urgente .lv-ico{background:var(--lv-alerta-bg);color:var(--lv-alerta)}
.lv-contagem{text-align:right}
.lv-contagem b{display:block;font-size:30px;font-weight:700;color:var(--lv-medio);line-height:1}
.lv-urgente .lv-contagem b{color:var(--lv-alerta)}
.lv-contagem span{font-size:12px;color:var(--lv-texto-2);font-weight:500}
.lv-sec{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:6px 2px 10px;color:var(--lv-texto)}
.lv-sec h2{font-size:17px!important;font-weight:700!important;margin:0!important;padding:0!important;display:flex;align-items:center;gap:8px;color:var(--lv-texto)!important}
.lv-sec h2 i{color:var(--lv-medio)}
.lv-sec span{font-size:13px;color:var(--lv-texto-2)}
.lv-sec span b{color:var(--lv-texto);font-size:15px}
.lv-insumos{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin:0 0 16px}
.lv-insumo .lv-cab{display:flex;align-items:center;gap:10px;margin-bottom:12px;color:var(--lv-texto)}
.lv-insumo .lv-cab i{font-size:22px;color:var(--lv-medio)}
.lv-insumo .lv-cab b{font-size:13px;letter-spacing:.06em;font-weight:700}
.lv-insumo .lv-tag{margin-left:auto;font-size:11px;color:var(--lv-texto-2);background:var(--lv-cinza-bg);border-radius:6px;padding:3px 8px;font-weight:500}
.lv-num{font-size:34px;font-weight:700;line-height:1;color:var(--lv-texto)}
.lv-lbl{font-size:12px;color:var(--lv-texto-2);font-weight:500;margin-top:4px}
.lv-barra{height:8px;background:var(--lv-cinza-bg);border-radius:999px;margin:14px 0 8px;overflow:hidden}
.lv-barra span{display:block;height:100%;background:var(--lv-medio);border-radius:999px}
.lv-barra-info{display:flex;justify-content:space-between;gap:8px;font-size:12px;color:var(--lv-texto-2)}
.lv-barra-info b{color:var(--lv-texto)}
.lv-valor{margin-top:12px;padding-top:10px;border-top:1px dashed var(--lv-linha);display:flex;justify-content:space-between;font-size:13px;color:var(--lv-texto-2)}
.lv-valor b{font-weight:700;color:var(--lv-texto)}
.lv-passos{display:flex;align-items:flex-start;width:100%}
.lv-passo{display:flex;flex-direction:column;align-items:center;gap:5px;min-width:70px;font-size:11px;font-weight:600;color:var(--lv-texto-2);text-align:center;line-height:1.2}
.lv-passo .lv-bola{width:24px;height:24px;border-radius:50%;border:2px solid var(--lv-linha);background:#fff;display:flex;align-items:center;justify-content:center;font-size:13px;box-sizing:border-box}
.lv-passo.lv-feito{color:var(--lv-texto)}
.lv-passo.lv-feito .lv-bola{background:var(--lv-medio);border-color:var(--lv-medio);color:#fff}
.lv-passo.lv-atual{color:var(--lv-medio)}
.lv-passo.lv-atual .lv-bola{border-color:var(--lv-medio);color:var(--lv-medio)}
.lv-passo.lv-alerta{color:var(--lv-alerta)}
.lv-passo.lv-alerta .lv-bola{border-color:var(--lv-alerta);color:var(--lv-alerta);background:var(--lv-alerta-bg)}
.lv-passo.lv-cancelado{color:var(--lv-erro)}
.lv-passo.lv-cancelado .lv-bola{border-color:var(--lv-erro);color:var(--lv-erro);background:var(--lv-erro-bg)}
.lv-trilho{flex:1;height:2px;background:var(--lv-linha);margin-top:11px;min-width:12px}
.lv-trilho.lv-feito{background:var(--lv-medio)}
.lv-selo{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:5px 11px;font-size:12px;font-weight:600;white-space:nowrap}
.lv-selo.lv-transito{background:var(--lv-azul-bg);color:#00489e}
.lv-selo.lv-ok{background:var(--lv-ok-bg);color:var(--lv-ok)}
.lv-selo.lv-div{background:var(--lv-alerta-bg);color:var(--lv-alerta)}
.lv-selo.lv-cancel{background:var(--lv-erro-bg);color:var(--lv-erro)}
.lv-reg b{display:block;font-size:14px;font-weight:700;color:var(--lv-texto)}
.lv-reg span{display:block;font-size:12px;color:var(--lv-texto-2);margin-top:2px}
.lv-formula{font-size:12px;color:var(--lv-texto-2);margin-top:6px}
.lv-formula b{color:var(--lv-texto)}
/* Botões e formulários na paleta oficial (prevalece sobre estilos antigos) */
div[data-testid="stFormSubmitButton"] button,
div[data-testid="stButton"] button[kind="primary"],
div[data-testid="stDownloadButton"] button[kind="primary"]{
  background:var(--lv-medio)!important;border:0!important;color:#fff!important;box-shadow:none!important;border-radius:10px!important;font-weight:700!important}
div[data-testid="stFormSubmitButton"] button:hover,
div[data-testid="stButton"] button[kind="primary"]:hover{background:#0057d1!important}
div[data-testid="stDownloadButton"] button:not([kind="primary"]){
  border:1px solid var(--lv-medio)!important;color:var(--lv-medio)!important;background:#fff!important;border-radius:10px!important;font-weight:600!important}
.st-key-dev-new-panel{border:1px solid var(--lv-linha)!important;border-radius:14px!important;box-shadow:none!important;background:#fff!important}
[class*="st-key-dev-qtd-"]{background:var(--lv-fundo)!important;border:1px solid var(--lv-linha)!important;box-shadow:none!important}
.dev-qty-icon{background:var(--lv-azul-bg)!important;color:var(--lv-medio)!important}
.st-key-lv-devs [data-testid="stVerticalBlockBorderWrapper"]{border:1px solid var(--lv-linha)!important;border-radius:14px!important}
/* Tela inicial: cartões de módulo */
[class*="st-key-lv-mod-"]{background:#fff;border:1px solid var(--lv-linha);border-radius:16px;padding:18px 18px 8px!important;transition:border-color .15s ease}
[class*="st-key-lv-mod-"]:hover{border-color:var(--lv-medio)}
.lv-mod-ico{width:40px;height:40px;border-radius:10px;background:var(--lv-azul-bg);color:var(--lv-medio);display:flex;align-items:center;justify-content:center;font-size:22px;margin-bottom:10px}
.lv-mod h3{font-size:16px!important;font-weight:600!important;color:var(--lv-texto)!important;margin:0 0 2px!important;padding:0!important}
.lv-mod p{font-size:13px;color:var(--lv-texto-2);margin:0 0 6px!important;min-height:36px}
.lv-mod-info{font-size:13px;color:var(--lv-texto);background:var(--lv-fundo);border-radius:10px;padding:10px 12px;min-height:44px;box-sizing:border-box}
.lv-mod-info b{color:var(--lv-medio)}
.lv-mod-info.lv-alerta-txt b{color:var(--lv-alerta)}
[class*="st-key-lv-mod-"] div[data-testid="stButton"] button{justify-content:flex-start!important;padding:0!important;border:0!important;color:var(--lv-medio)!important;background:transparent!important;font-weight:600!important;min-height:30px!important}
[class*="st-key-lv-mod-"] div[data-testid="stButton"] button:hover{text-decoration:underline}
.lv-barra-topo{display:flex;align-items:center;gap:16px;padding:2px 0 14px;border-bottom:1px solid var(--lv-linha);margin:0 0 26px}
.lv-barra-topo img{height:30px}
.lv-barra-topo .lv-sep{width:1px;height:24px;background:var(--lv-linha)}
.lv-barra-topo .lv-onde{display:flex;align-items:center;gap:6px;font-size:15px;color:var(--lv-texto)}
.lv-barra-topo .lv-onde i{font-size:19px}
.lv-barra-topo .lv-dir{margin-left:auto;display:flex;align-items:center;gap:14px;font-size:15px;color:var(--lv-texto-2)}
.lv-barra-topo .lv-dir b{color:var(--lv-texto);font-weight:700}
.lv-avatar{width:38px;height:38px;border-radius:50%;background:var(--lv-azul-bg);color:var(--lv-medio);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px}
.lv-h1{font-size:30px;font-weight:600;color:var(--lv-texto);margin:0 0 4px;line-height:1.2}
.lv-sub{font-size:14px;color:var(--lv-texto-2);margin:0 0 18px}
.lv-rotulo-sec{font-size:13px;font-weight:500;letter-spacing:.04em;color:var(--lv-texto-2);text-transform:uppercase;margin:26px 2px 10px}
.st-key-lv-acao{background:#fff;border:1px solid var(--lv-linha);border-radius:22px;padding:22px 24px!important}
.lv-acao-lbl{font-size:13px;color:var(--lv-texto-2);display:flex;align-items:center;gap:6px}
.lv-acao-lbl i{color:var(--lv-medio);font-size:17px}
.lv-acao-num{font-size:32px;font-weight:700;color:var(--lv-texto);line-height:1.1;margin:6px 0 4px}
.lv-acao-num small{font-size:15px;font-weight:500;color:var(--lv-texto-2);margin-left:6px}
.lv-acao-det{font-size:13px;color:var(--lv-texto-2)}
.lv-acao-det b{color:var(--lv-texto)}
.st-key-lv-acao div[data-testid="stButton"] button{min-height:58px!important;border-radius:16px!important;font-size:16px!important;padding:0 28px!important}
.st-key-lv-aviso{background:#fbeccc;border-radius:22px;padding:22px 24px 6px!important}
.st-key-lv-aviso-ok{background:var(--lv-azul-bg);border-radius:22px;padding:22px 24px 6px!important}
.lv-aviso-t{display:flex;align-items:center;gap:10px;font-size:17px;font-weight:700;color:var(--lv-texto)}
.lv-aviso-t i{font-size:22px;color:#d99a00}
.st-key-lv-aviso-ok .lv-aviso-t i{color:var(--lv-medio)}
.lv-aviso-x{font-size:13px;color:#3d3d3d;margin:8px 0 0 32px;line-height:1.5}
.st-key-lv-aviso div[data-testid="stButton"],.st-key-lv-aviso-ok div[data-testid="stButton"]{margin-left:32px}
.st-key-lv-aviso div[data-testid="stButton"] button,.st-key-lv-aviso-ok div[data-testid="stButton"] button{padding:0!important;border:0!important;background:transparent!important;color:var(--lv-texto)!important;font-weight:700!important;justify-content:flex-start!important}
.st-key-lv-aviso div[data-testid="stButton"] button:hover,.st-key-lv-aviso-ok div[data-testid="stButton"] button:hover{text-decoration:underline}
.lv-kpi{background:#fff;border:1px solid var(--lv-linha);border-radius:16px;padding:16px 18px}
.lv-kpi .lv-k-l{font-size:13px;color:var(--lv-texto-2);display:flex;align-items:center;gap:6px}
.lv-kpi .lv-k-l i{color:var(--lv-medio);font-size:17px}
.lv-kpi .lv-k-v{font-size:26px;font-weight:700;color:var(--lv-texto);margin-top:6px;line-height:1.1}
.lv-kpi .lv-k-s{font-size:12px;color:var(--lv-texto-2);margin-top:2px}
.lv-status{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:4px 10px;font-size:12px;font-weight:600;white-space:nowrap}
@media (max-width:700px){
  .lv-topo{padding:18px 18px 20px}.lv-topo h1{font-size:23px!important}
  .lv-prazo{flex-wrap:wrap}.lv-contagem{text-align:left}
  .lv-passo{min-width:54px;font-size:10px}
}
</style>
"""


def aplicar_tema() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def _e(v) -> str:
    return html.escape(str(v))


def _fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def cabecalho(trilha: str, titulo: str, subtitulo: str = "", atualizado_ate=None) -> None:
    """Faixa de cabeçalho com o degradê oficial (único uso do degradê na tela)."""
    partes_trilha = [x.strip() for x in trilha.split("/") if x.strip()]
    onde = partes_trilha[-1].capitalize() if len(partes_trilha) > 1 else "Início"
    trilha_html = f"<i class='ti ti-home'></i>{_e(onde)}"
    selo = ""
    if atualizado_ate is not None and pd.notna(atualizado_ate):
        selo = (f"<div class='lv-atualizado'><i class='ti ti-calendar-check'></i>"
                f"Envios atualizados até {atualizado_ate.strftime('%d/%m/%Y')}</div>")
    st.markdown(
        f"<div class='lv-topo'><div class='lv-trilha'>{trilha_html}</div>"
        f"<h1>{_e(titulo)}</h1>"
        + (f"<p>{_e(subtitulo)}</p>" if subtitulo else "")
        + selo + "</div>",
        unsafe_allow_html=True,
    )


def dias_uteis_ate(prazo: pd.Timestamp, hoje: pd.Timestamp) -> int:
    """Dias úteis (seg–sex) depois de hoje até o prazo, inclusive."""
    ini = (hoje.normalize() + pd.Timedelta(days=1))
    fim = prazo.normalize()
    if fim < ini:
        return 0
    return int(sum(1 for d in pd.date_range(ini, fim) if d.weekday() < 5))


def card_prazo(rotulo_mes: str, prazo: pd.Timestamp, hoje: pd.Timestamp) -> None:
    dias = dias_uteis_ate(prazo, hoje)
    urgente = dias <= 3
    st.markdown(
        f"<div class='lv-card lv-prazo{' lv-urgente' if urgente else ''}'>"
        f"<div class='lv-ico'><i class='ti ti-clock-hour-4'></i></div>"
        f"<div class='lv-txt'><b>Prazo para devolver {_e(rotulo_mes)}: {prazo.strftime('%d/%m/%Y')}</b>"
        f"<div>Depois dessa data, o que não foi devolvido vira cobrança.</div></div>"
        f"<div class='lv-contagem'><b>{dias}</b><span>{'dia útil restante' if dias == 1 else 'dias úteis restantes'}</span></div>"
        f"</div>",
        unsafe_allow_html=True,
    )


_ICONE_INSUMO = {"SACA": "ti-shopping-bag", "GAYLORD": "ti-box", "PALLET": "ti-stack-2"}
_PLURAL = {"SACA": "sacas", "GAYLORD": "gaylords", "PALLET": "pallets"}


def cards_insumos(titulo: str, saldo: pd.DataFrame, ordem: list[str], precos: dict, fmt_brl) -> None:
    """Um card por insumo: saldo, barra 'devolveu X de Y' e valor do saldo.

    `saldo` precisa das colunas tipo, enviado, em_transito, recebido, saldo.
    """
    linhas, total = [], 0.0
    por_tipo = {str(r["tipo"]).upper(): r for _, r in saldo.iterrows()}
    for tipo in ordem:
        r = por_tipo.get(tipo)
        enviado = int(r["enviado"]) if r is not None else 0
        transito = int(r["em_transito"]) if r is not None else 0
        recebido = int(r["recebido"]) if r is not None else 0
        qtd = int(r["saldo"]) if r is not None else 0
        devolvido = transito + recebido
        pct = round(100 * devolvido / enviado) if enviado else 0
        preco = float(precos.get(tipo, 0) or 0)
        total += qtd * preco
        tag = "<span class='lv-tag'>1 por gaylord</span>" if tipo == "PALLET" else ""
        extra_transito = f" · {_fmt(transito)} em trânsito" if transito else ""
        valor = (f"<div class='lv-valor'><span>Valor do saldo</span><b>{fmt_brl(qtd * preco)}</b></div>"
                 if preco > 0 else "")
        linhas.append(
            f"<div class='lv-card lv-insumo'>"
            f"<div class='lv-cab'><i class='ti {_ICONE_INSUMO.get(tipo, 'ti-package')}'></i><b>{_e(tipo)}</b>{tag}</div>"
            f"<div class='lv-num'>{_fmt(qtd)}</div>"
            f"<div class='lv-lbl'>{_PLURAL.get(tipo, tipo.lower())} ainda com a operação</div>"
            f"<div class='lv-barra'><span style='width:{min(pct, 100)}%'></span></div>"
            f"<div class='lv-barra-info'><span>Devolveu <b>{_fmt(devolvido)}</b> de <b>{_fmt(enviado)}</b>{extra_transito}</span><b>{pct}%</b></div>"
            f"{valor}</div>"
        )
    resumo = (f"<span>Valor total a devolver: <b>{fmt_brl(total)}</b></span>"
              if total > 0 else "")
    st.markdown(
        f"<div class='lv-sec'><h2><i class='ti ti-package'></i>{_e(titulo)}</h2>{resumo}</div>"
        f"<div class='lv-insumos'>{''.join(linhas)}</div>",
        unsafe_allow_html=True,
    )


def cartao_modulo(slug: str, icone: str, titulo: str, descricao: str,
                  info_html: str = "", alerta: bool = False) -> bool:
    """Cartão clicável de módulo para a tela inicial. Retorna True se clicado."""
    with st.container(key=f"lv-mod-{slug}"):
        st.markdown(
            f"<div class='lv-mod'><div class='lv-mod-ico'><i class='ti {icone}'></i></div>"
            f"<h3>{_e(titulo)}</h3><p>{_e(descricao)}</p>"
            + (f"<div class='lv-mod-info{' lv-alerta-txt' if alerta else ''}'>{info_html}</div>" if info_html else "")
            + "</div>",
            unsafe_allow_html=True,
        )
        return st.button(f"Abrir {titulo.lower()}  →", key=f"lv-abrir-{slug}", type="tertiary")


def titulo_secao(titulo: str, icone: str = "ti-list-details", direita: str = "") -> None:
    st.markdown(
        f"<div class='lv-sec'><h2><i class='ti {icone}'></i>{_e(titulo)}</h2>"
        + (f"<span>{direita}</span>" if direita else "") + "</div>",
        unsafe_allow_html=True,
    )


# Etapas da devolução, no estilo rastreio de pacote.
_ETAPAS = ["Registrada", "Em trânsito", "Recebida no CD", "Conferida"]


def linha_do_tempo(status: str) -> str:
    """HTML da linha do tempo para um status de devolução."""
    s = str(status or "").upper()
    # (quantas etapas concluídas, índice da etapa atual, classe da atual, rótulo da atual)
    if s == "EM_TRANSITO":
        feitas, atual, cls, rot = 1, 1, "lv-atual", None
    elif s == "RECEBIDO":
        feitas, atual, cls, rot = 3, 3, "lv-atual", "Aguardando conferência"
    elif s == "CONFERIDO":
        feitas, atual, cls, rot = 4, None, "", None
    elif s == "DIVERGENTE":
        feitas, atual, cls, rot = 3, 3, "lv-alerta", "Divergente"
    elif s == "CANCELADO":
        feitas, atual, cls, rot = 1, 1, "lv-cancelado", "Cancelada"
    else:
        feitas, atual, cls, rot = 1, None, "", None
    icones_atual = {"lv-atual": "ti-truck", "lv-alerta": "ti-alert-triangle", "lv-cancelado": "ti-x"}
    partes = []
    for i, nome in enumerate(_ETAPAS):
        if s == "CANCELADO" and i > 1:
            break
        if i == atual:
            c, ico, nome_v = cls, icones_atual.get(cls, "ti-point"), (rot or nome)
            if s == "RECEBIDO":
                ico = "ti-clipboard-check"
        elif i < feitas:
            c, ico, nome_v = "lv-feito", "ti-check", nome
        else:
            c, ico, nome_v = "", "", nome
        if i > 0:
            partes.append(f"<div class='lv-trilho{' lv-feito' if i < feitas or (i == atual and i <= feitas) else ''}'></div>")
        bola = f"<i class='ti {ico}'></i>" if ico else ""
        partes.append(f"<div class='lv-passo {c}'><div class='lv-bola'>{bola}</div>{_e(nome_v)}</div>")
    return f"<div class='lv-passos'>{''.join(partes)}</div>"


_SELO = {
    "EM_TRANSITO": ("lv-transito", "ti-truck", "Em trânsito"),
    "RECEBIDO": ("lv-ok", "ti-inbox", "Recebida no CD"),
    "CONFERIDO": ("lv-ok", "ti-circle-check", "Conferida"),
    "DIVERGENTE": ("lv-div", "ti-alert-triangle", "Divergente"),
    "CANCELADO": ("lv-cancel", "ti-x", "Cancelada"),
}


def selo_status(status: str) -> str:
    cls, ico, rot = _SELO.get(str(status or "").upper(), ("lv-transito", "ti-point", str(status)))
    return f"<span class='lv-selo {cls}'><i class='ti {ico}'></i>{_e(rot)}</span>"
