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
        .dev-title-wrap { width:100%; display:block; text-align:left; }
        .dev-page-title { color:#172B4D !important; display:block; width:100%; font-size:clamp(28px,2.3vw,34px) !important; line-height:1.18 !important; font-weight:800 !important; letter-spacing:-.8px !important; margin:0 !important; text-align:left !important; }
        .dev-page-subtitle { color:#7188a6; font-size:16px; line-height:1.5; font-weight:600; margin:0 0 18px; text-align:center; }
        .dev-section-title { color:#12345d; background:#eaf3ff; border:1px solid #d4e6ff; border-radius:12px; padding:12px 16px; font-size:19px; font-weight:750; margin:16px 0 12px; }
        .dev-balance-card { background:linear-gradient(135deg,#f0f6ff 0%,#e6f1ff 100%); border:1px solid #d5e6ff; border-radius:15px; padding:19px 20px; min-height:132px; box-shadow:0 3px 12px rgba(25,91,170,.05); }
        .dev-balance-label { color:#315d91; font-size:14px; font-weight:700; margin-bottom:7px; }
        .dev-balance-qty { color:#102f59; font-size:30px; line-height:1.1; font-weight:800; margin-bottom:9px; }
        .dev-balance-caption { color:#6683a8; font-size:12px; font-weight:600; margin-bottom:2px; }
        .dev-balance-value { color:#12345d; font-size:18px; font-weight:800; }
        .dev-total-banner { background:#e7f2ff; border:1px solid #cfe3ff; border-radius:12px; padding:14px 18px; margin:16px 0 20px; color:#164b88; font-size:16px; font-weight:700; }
        div[data-testid="stSelectbox"] label, div[data-testid="stNumberInput"] label, div[data-testid="stTextInput"] label { color:#17385f !important; font-weight:650 !important; }
        div[data-testid="stSelectbox"] > div > div, div[data-testid="stNumberInput"] input, div[data-testid="stTextInput"] input { border-radius:10px !important; }
        div[data-testid="stExpander"] { border:1px solid #d5e6ff !important; border-radius:12px !important; background:#f7faff !important; }
        div[data-testid="stForm"] { border:1px solid #d5e6ff; border-radius:15px; padding:20px 18px 12px; background:#fbfdff; }
        div[data-testid="stFormSubmitButton"] button { background:#075BEA !important; color:white !important; border:0 !important; border-radius:10px !important; font-weight:700 !important; padding:10px 22px !important; }
        div[data-testid="stAlert"][kind="success"] { background:#e8f8f2 !important; border:1px solid #c9efdf !important; color:#126b62 !important; border-radius:11px !important; }
        hr.sb-sep { border-color:#d8e7f8 !important; margin:22px 0 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='dev-page-kicker'>Portal Leves&nbsp; / &nbsp;Devoluções</div>"
        "<div class='dev-title-wrap'><h1 class='dev-page-title'>Devoluções</h1></div>",
        unsafe_allow_html=True,
    )
    if eh_admin or eh_gdl:
        st.markdown(
            "<p class='dev-page-subtitle'>Selecione a operação e registre uma devolução manual "
            "em nome dela. O saldo e a competência serão calculados para a operação selecionada.</p>",
            unsafe_allow_html=True,
        )

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

    else:
        st.markdown(
            "<p class='dev-page-subtitle'>Declare o que está devolvendo, gere o romaneio com "
            "QR e envie impresso junto com os itens.</p>",
            unsafe_allow_html=True,
        )

    if manual.disponivel():
        with st.expander("📘 Manual de devolução (treinamento)"):
            manual.botao_manual(key="manual_page3")

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

        escolha_mes = st.radio(
            "Selecione a competência da devolução",
            options=[rot_mes[m] for m in elegiveis],
            index=None,
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
            f"<div class='dev-total-banner'>💰 &nbsp; Valor total a devolver: <strong>{dp.fmt_brl(total_val)}</strong></div>",
            unsafe_allow_html=True,
        )

    st.markdown("<hr class='sb-sep' style='border-top-color:#e6e6e6;'>", unsafe_allow_html=True)

    # ---- Nova devolução ----
    if eh_gdl:
        _minhas_devolucoes(destino, eh_admin=False, eh_gdl=True)
        return

    st.markdown("<div class='dev-section-title'>＋ &nbsp; Nova devolução</div>", unsafe_allow_html=True)
    pend = {t: q for t, q in dp.pending_mes_tipo(destino, mes_ref).items() if q > 0}
    if not pend:
        st.success(f"Sem pendência de devolução para {escolha_mes}. 🎉")
    else:
        with st.form("nova_devolucao", clear_on_submit=True):
            qtds = {}
            itens_pend = sorted(pend.items())
            fcols = st.columns(len(itens_pend))
            for i, (t, q) in enumerate(itens_pend):
                qtds[t] = fcols[i].number_input(
                    f"{t.title()} (máx. {_fmt(q)})",
                    min_value=0, max_value=int(q), step=1, value=0,
                )
            placa = st.text_input("Placa do veículo", placeholder="ex.: ABC1D23")
            obs = st.text_input("Observação (opcional)")
            enviar = st.form_submit_button("Gerar devolução", type="primary")

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
    st.markdown("#### Devoluções da operação" if (eh_admin or eh_gdl) else "#### Minhas devoluções")
    devs = dp.devolucoes_df()
    if devs.empty:
        st.caption("Nenhuma devolução registrada ainda.")
        return
    minhas = devs[devs["destino"].map(dp._normalizar) == dp._normalizar(destino)]
    minhas = minhas.sort_values("dt_criacao", ascending=False)
    if minhas.empty:
        st.caption("Nenhuma devolução registrada ainda.")
        return

    for _, d in minhas.iterrows():
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 1.4, 1, 1.2])
            comp = d.get("competencia")
            comp_txt = f"  \n🗓️ {dp.rotulo_mes(comp)}" if comp and len(str(comp)) == 7 else ""
            c1.markdown(f"**{d['id']}**  \n{d['data_criacao']}{comp_txt}")
            c2.markdown(dp.STATUS_LABEL.get(d["status"], d["status"])
                        + (f"  \n🚚 {d.get('placa')}" if d.get("placa") else ""))
            c3.markdown(f"Total: **{_fmt(d['total_declarado'])}**")
            with c4:
                itens = dp.itens_da_devolucao(d["id"])
                itens_l = [{"tipo": r["tipo"], "qtd_declarada": r["qtd_declarada"]}
                           for _, r in itens.iterrows()]
                dev_h = d.to_dict()
                st.download_button(
                    "📄 Romaneio",
                    romaneio.gerar_romaneio_pdf(dev_h, itens_l, dp.base_url()),
                    file_name=f"{d['id']}.pdf", mime="application/pdf",
                    key=f"rom_{d['id']}",
                )
                if d["status"] == dp.STATUS_TRANSITO:
                    if st.button("Cancelar", key=f"can_{d['id']}"):
                        dados.atualizar_devolucao(d["id"], {"status": dp.STATUS_CANCELADO})
                        st.rerun()
