"""
page_inicio.py — Tela inicial do Portal LEVES (logo após o login).

Visual claro, no padrão do app da Loggi: barra superior com a lebre e um
destaque à direita, título grande, um cartão principal de ação (devolver o
mês atual) e um cartão de aviso para o que é urgente. Abaixo, os indicadores
do mês e o acesso rápido aos módulos.
"""

from __future__ import annotations

import base64
import functools
import html
import os

import pandas as pd
import streamlit as st

import data_processing as dp
import tema

CHAVE_PAGINA = "pagina_navegacao_leves"
_LEBRE = "image_simbolo_lebre_azul.png"

# slug, ícone (Tabler), descrição curta
MODULOS = {
    "Envios": ("envios", "ti-truck-delivery", "Insumos que chegaram para a operação."),
    "Devoluções": ("devolucoes", "ti-arrow-back-up", "Registre e acompanhe devoluções."),
    "Pendências": ("pendencias", "ti-alert-circle", "O que falta devolver, mês a mês."),
    "Cobranças": ("cobrancas", "ti-receipt", "Valores cobrados por competência."),
    "Recebimentos": ("recebimentos", "ti-inbox", "Receba e confira devoluções no CD."),
    "Conciliação": ("conciliacao", "ti-scale", "Enviado × devolvido e fechamento."),
    "Usuários": ("usuarios", "ti-users", "Cadastro e acesso ao portal."),
    "Relatórios": ("relatorios", "ti-chart-bar", "Relatórios consolidados."),
    "Configurações": ("configuracoes", "ti-settings", "Preços, e-mail e parâmetros."),
}


def _fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def _e(v) -> str:
    return html.escape(str(v))


@functools.lru_cache(maxsize=1)
def _lebre_b64() -> str:
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), _LEBRE)
    if not os.path.exists(caminho):
        return ""
    with open(caminho, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _ir(pagina: str) -> None:
    st.session_state[CHAVE_PAGINA] = pagina
    st.rerun()


def _barra_topo(user: dict, rotulo_dir: str = "", valor_dir: str = "") -> None:
    nome = str(user.get("nome", "")).strip()
    iniciais = "".join(p[0] for p in nome.split()[:2]).upper() or "?"
    lebre = _lebre_b64()
    img = f"<img src='data:image/png;base64,{lebre}' alt='Loggi'><div class='lv-sep'></div>" if lebre else ""
    dir_html = (f"<span>{_e(rotulo_dir)}</span><b>{_e(valor_dir)}</b>" if rotulo_dir else "")
    st.markdown(
        f"<div class='lv-barra-topo'>{img}<div class='lv-onde'><i class='ti ti-home'></i>Início</div>"
        f"<div class='lv-dir'>{dir_html}<div class='lv-avatar' title='{_e(nome)}'>{_e(iniciais)}</div></div></div>",
        unsafe_allow_html=True,
    )


def _kpi(icone: str, rotulo: str, valor: str, sub: str = "") -> str:
    return (f"<div class='lv-kpi'><div class='lv-k-l'><i class='ti {icone}'></i>{_e(rotulo)}</div>"
            f"<div class='lv-k-v'>{valor}</div>"
            + (f"<div class='lv-k-s'>{_e(sub)}</div>" if sub else "") + "</div>")


def _modulos(opcoes: list[str], info: dict | None = None) -> None:
    info = info or {}
    modulos = [m for m in opcoes if m in MODULOS]
    por_linha = 4 if len(modulos) <= 4 else 3
    for i in range(0, len(modulos), por_linha):
        cols = st.columns(por_linha, gap="medium")
        for col, nome_mod in zip(cols, modulos[i:i + por_linha]):
            slug, icone, desc = MODULOS[nome_mod]
            with col:
                if tema.cartao_modulo(slug, icone, nome_mod, info.get(nome_mod, desc)):
                    _ir(nome_mod)


def _inicio_operacao(user: dict, opcoes: list[str]) -> None:
    destino = str(user.get("destino", "")).strip()
    primeiro = str(user.get("nome", "")).split(" ")[0] or "olá"
    pend = dp.pendencias_da_operacao(destino)
    agora = dp.agora_sp()

    abertos = pend[pend["situacao"].isin(["No prazo", "Prazo encerrado"])] if not pend.empty else pend
    vencidos = pend[pend["situacao"] == "Prazo encerrado"] if not pend.empty else pend
    no_prazo = pend[pend["situacao"] == "No prazo"] if not pend.empty else pend
    valor_aberto = float(abertos["valor"].sum()) if not abertos.empty else 0.0

    _barra_topo(user, "Saldo a devolver", dp.fmt_brl(valor_aberto))

    ate = dp.envios_atualizados_ate()
    ate_txt = f" · envios atualizados até {ate.strftime('%d/%m/%Y')}" if ate is not None and pd.notna(ate) else ""
    st.markdown(
        f"<div class='lv-h1'>Olá, {_e(primeiro)}</div>"
        f"<div class='lv-sub'>Operação {_e(destino)}{_e(ate_txt)}</div>",
        unsafe_allow_html=True,
    )

    col_acao, col_aviso = st.columns([1.75, 1], gap="medium")

    # ---- Cartão principal: devolver o mês aberto ----
    with col_acao:
        with st.container(key="lv-acao"):
            if not no_prazo.empty:
                mes = no_prazo["mes"].max()
                g = no_prazo[no_prazo["mes"] == mes]
                prazo = g["prazo"].iloc[0]
                dias = tema.dias_uteis_ate(prazo, agora)
                detalhe = " · ".join(
                    f"<b>{_fmt(r['saldo'])}</b> {r['tipo'].lower()}{'s' if r['saldo'] != 1 else ''}"
                    for _, r in g.iterrows() if r["saldo"] > 0
                )
                c1, c2 = st.columns([1.6, 1], vertical_alignment="center")
                c1.markdown(
                    f"<div class='lv-acao-lbl'><i class='ti ti-arrow-back-up'></i>Devolução de {_e(dp.rotulo_mes(mes))}</div>"
                    f"<div class='lv-acao-num'>{_fmt(g['saldo'].sum())}<small>itens a devolver</small></div>"
                    f"<div class='lv-acao-det'>{detalhe}</div>"
                    f"<div class='lv-acao-det' style='margin-top:6px'>Prazo <b>{prazo.strftime('%d/%m/%Y')}</b> · "
                    f"<b>{dias}</b> {'dia útil' if dias == 1 else 'dias úteis'} · valor <b>{dp.fmt_brl(g['valor'].sum())}</b></div>",
                    unsafe_allow_html=True,
                )
                with c2:
                    if st.button("Registrar devolução", type="primary", width="stretch", key="lv-acao-btn"):
                        _ir("Devoluções")
            else:
                st.markdown(
                    "<div class='lv-acao-lbl'><i class='ti ti-circle-check'></i>Devoluções</div>"
                    "<div class='lv-acao-num' style='font-size:24px'>Nenhum mês aberto para devolução agora</div>"
                    "<div class='lv-acao-det'>Quando chegarem novos envios, o saldo aparece aqui.</div>",
                    unsafe_allow_html=True,
                )
                if st.button("Ver devoluções", key="lv-acao-btn"):
                    _ir("Devoluções")

    # ---- Cartão de aviso: o que é urgente ----
    with col_aviso:
        if not vencidos.empty and int(vencidos["saldo"].sum()) > 0:
            n_meses = vencidos["mes"].nunique()
            with st.container(key="lv-aviso"):
                st.markdown(
                    "<div class='lv-aviso-t'><i class='ti ti-alert-triangle'></i>Prazo encerrado</div>"
                    f"<div class='lv-aviso-x'><b>{_fmt(vencidos['saldo'].sum())} itens</b> "
                    f"({dp.fmt_brl(vencidos['valor'].sum())}) de {n_meses} {'mês' if n_meses == 1 else 'meses'} "
                    "não podem mais ser devolvidos e entram na cobrança.</div>",
                    unsafe_allow_html=True,
                )
                if st.button("Ver pendências  →", key="lv-aviso-btn", type="tertiary"):
                    _ir("Pendências")
        else:
            with st.container(key="lv-aviso-ok"):
                st.markdown(
                    "<div class='lv-aviso-t'><i class='ti ti-shield-check'></i>Tudo dentro do prazo</div>"
                    "<div class='lv-aviso-x'>Nenhum mês com prazo encerrado. Devolva o saldo do mês "
                    "até a data indicada para evitar cobrança.</div>",
                    unsafe_allow_html=True,
                )
                if st.button("Ver pendências  →", key="lv-aviso-btn", type="tertiary"):
                    _ir("Pendências")

    # ---- Indicadores do mês ----
    if not pend.empty:
        mes_atual = pend["mes"].max()
        m = pend[pend["mes"] == mes_atual]
        enviados = int(m["enviado"].sum())
        devolvidos = int(m["devolvido"].sum())
        pct = round(100 * devolvidos / enviados) if enviados else 0
        devs = dp.devolucoes_df()
        transito = 0
        if not devs.empty:
            transito = int(((devs["destino_norm"] == dp._normalizar(destino))
                            & (devs["status"] == dp.STATUS_TRANSITO)).sum())
        st.markdown(f"<div class='lv-rotulo-sec'>Acompanhamento · {_e(dp.rotulo_mes(mes_atual))}</div>",
                    unsafe_allow_html=True)
        k = st.columns(4, gap="medium")
        k[0].markdown(_kpi("ti-truck-delivery", "Recebidos da Loggi", _fmt(enviados), "sacas, gaylords e pallets"), unsafe_allow_html=True)
        k[1].markdown(_kpi("ti-arrow-back-up", "Devolvidos", _fmt(devolvidos), f"{pct}% do que chegou"), unsafe_allow_html=True)
        k[2].markdown(_kpi("ti-truck", "A caminho do CD", _fmt(transito), "devoluções em trânsito"), unsafe_allow_html=True)
        k[3].markdown(_kpi("ti-wallet", "Em aberto no total", _fmt(abertos["saldo"].sum()) if not abertos.empty else "0",
                           dp.fmt_brl(valor_aberto)), unsafe_allow_html=True)

    st.markdown("<div class='lv-rotulo-sec'>Acesso rápido</div>", unsafe_allow_html=True)
    _modulos([o for o in opcoes if o != "Início"])


def page_inicio(opcoes: list[str]):
    user = st.session_state.get("usuario") or {}
    perfil = str(user.get("perfil", "")).lower()
    tema.aplicar_tema()

    if perfil not in ("admin", "gdl") and user.get("destino"):
        _inicio_operacao(user, opcoes)
        return

    _barra_topo(user)
    primeiro = str(user.get("nome", "")).split(" ")[0] or "olá"
    ate = dp.envios_atualizados_ate()
    ate_txt = f"Envios atualizados até {ate.strftime('%d/%m/%Y')}" if ate is not None and pd.notna(ate) else ""
    st.markdown(
        f"<div class='lv-h1'>Olá, {_e(primeiro)}</div><div class='lv-sub'>{_e(ate_txt)}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='lv-rotulo-sec'>Módulos</div>", unsafe_allow_html=True)
    _modulos([o for o in opcoes if o != "Início"])
