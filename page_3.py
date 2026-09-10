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
    destino = user.get("destino", "")
    destino_fisico_fixo = ""

    st.subheader("Devoluções")
    if eh_admin:
        st.markdown(
            "<p class='custom-text'>Selecione a operação e registre uma devolução manual "
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
            help="Selecione a operação em nome da qual a devolução será registrada.",
        )

        chave_op = dp._normalizar(destino)
        destinos_fisicos = mapa_operacoes.get(chave_op, {}).get("destinos", [])
        if len(destinos_fisicos) == 1:
            destino_fisico_fixo = destinos_fisicos[0]
            st.caption(
                f"Devolução manual sendo registrada para **{destino}**. "
                f"Destino fixado pela aba Envios: **{destino_fisico_fixo}**."
            )
        elif len(destinos_fisicos) > 1:
            st.error(
                f"A operação **{destino}** possui mais de um destino na coluna E da aba Envios. "
                "A devolução não pode ser registrada até que exista apenas um destino para a operação."
            )
        else:
            st.error(
                f"Não foi encontrado destino na coluna E da aba Envios para a operação **{destino}**."
            )
    else:
        st.markdown(
            "<p class='custom-text'>Declare o que está devolvendo, gere o romaneio com "
            "QR e envie impresso junto com os itens.</p>",
            unsafe_allow_html=True,
        )

    if manual.disponivel():
        with st.expander("📘 Manual de devolução (treinamento)"):
            manual.botao_manual(key="manual_page3")

    # ---- Saldo a devolver ----
    saldo = dp.saldo_por_tipo(destino)
    if saldo.empty or saldo["enviado"].sum() == 0:
        if eh_admin:
            st.info(f"Nenhum ativo enviado para a operação **{destino}** até o momento.")
        else:
            st.info("Nenhum ativo enviado para a sua operação até o momento.")
        return

    st.markdown("#### Saldo a devolver")
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
            st.metric(tipo.title(), _fmt(qtd_saldo), help=ajuda)
            if valor_unitario > 0:
                st.markdown(
                    f"""
                    <div style="margin-top:-8px; padding-top:2px;">
                        <div style="font-size:0.78rem; color:#7a7f87; margin-bottom:2px;">Valor do saldo</div>
                        <div style="font-size:1.02rem; font-weight:600; color:#343840;">
                            {dp.fmt_brl(valor_total_insumo)}
                        </div>
                        <div style="font-size:0.76rem; color:#8b9098; margin-top:1px;">
                            {dp.fmt_brl(valor_unitario)} por unidade
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    if dp.tem_precos():
        total_val = sum(
            int(r["saldo"]) * pr.get(r["tipo"], 0)
            for _, r in saldo.iterrows()
        )
        st.markdown(f"**Valor total a devolver:** {dp.fmt_brl(total_val)}")

    st.markdown("<hr class='sb-sep' style='border-top-color:#e6e6e6;'>", unsafe_allow_html=True)

    # ---- Nova devolução ----
    st.markdown("#### Nova devolução")
    elegiveis = dp.competencias_elegiveis(destino)
    if not elegiveis:
        st.info("Nenhuma competência aberta para devolução (prazos encerrados).")
        _minhas_devolucoes(destino, eh_admin=eh_admin)
        return

    # Competência (mês) — fora do form para recalcular a pendência ao trocar.
    rot_mes = {m: dp.rotulo_mes(m) for m in elegiveis}
    escolha_mes = st.selectbox(
        "Mês de referência (competência)",
        [rot_mes[m] for m in elegiveis],
        help="Você pode devolver retroativo, dentro do prazo (até o dia 5 do mês seguinte).",
    )
    mes_ref = next(m for m, r in rot_mes.items() if r == escolha_mes)
    prazo_txt = dp.prazo_devolucao(mes_ref).strftime("%d/%m/%Y")
    st.caption(f"Devoluções de {escolha_mes} aceitas até **{prazo_txt}**.")

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

            if eh_admin:
                local = st.text_input(
                    "Devolvendo para (local/CD de destino)",
                    value=destino_fisico_fixo,
                    disabled=True,
                    help="Destino definido automaticamente pela coluna E da aba Envios para a operação selecionada.",
                )
            else:
                destinos_cfg = dp.destinos_devolucao()
                if destinos_cfg:
                    local = st.selectbox(
                        "Devolvendo para (local/CD de destino)",
                        [""] + destinos_cfg,
                    )
                else:
                    local = st.text_input(
                        "Devolvendo para (local/CD de destino)",
                        placeholder="ex.: CD Cajamar",
                    )

            obs = st.text_input("Observação (opcional)")
            enviar = st.form_submit_button("Gerar devolução", type="primary")

        if enviar:
            itens = [{"tipo": t, "qtd_declarada": int(q)} for t, q in qtds.items() if q > 0]
            placa_norm = "".join(str(placa or "").upper().split()).replace("-", "")
            local_norm = str(local or "").strip()
            if not itens:
                st.error("Informe ao menos uma quantidade.")
            elif not placa_norm:
                st.error("Informe a placa do veículo.")
            elif not local_norm:
                st.error("Informe para onde está devolvendo.")
            elif eh_admin and not destino_fisico_fixo:
                st.error("A operação selecionada não possui um destino fixado na coluna E da aba Envios.")
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
                    "placa": placa_norm, "local_devolucao": local_norm,
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


def _minhas_devolucoes(destino: str, eh_admin: bool = False):
    st.markdown("#### Devoluções da operação" if eh_admin else "#### Minhas devoluções")
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
