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
        .dev-section-title { color:#12345d; background:#eaf3ff; border:1px solid #d4e6ff; border-radius:12px; padding:12px 16px; font-size:19px; font-weight:750; margin:16px 0 12px; }
        .dev-balance-card { position:relative; overflow:hidden; background:#ffffff; border:1px solid #d9e4f2; border-radius:14px; padding:18px 20px 17px; min-height:146px; box-shadow:0 3px 10px rgba(23,52,95,.045); transition:transform .18s ease, box-shadow .18s ease, border-color .18s ease; }
        .dev-balance-card:before { content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background:#2874df; }
        .dev-balance-card:hover { transform:translateY(-2px); border-color:#b8d2f5; box-shadow:0 7px 18px rgba(23,75,136,.09); }
        .dev-balance-label { color:#607895; font-family:'Montserrat',sans-serif; font-size:12px; font-weight:800; letter-spacing:.45px; text-transform:uppercase; margin-bottom:9px; }
        .dev-balance-qty { color:#142f55; font-family:'Montserrat',sans-serif; font-size:34px; line-height:1.05; font-weight:800; letter-spacing:-1px; margin-bottom:15px; }
        .dev-balance-caption { color:#8192a8; font-family:'Montserrat',sans-serif; font-size:11px; font-weight:700; margin-bottom:3px; padding-top:10px; border-top:1px solid #edf1f6; }
        .dev-balance-value { color:#174b88; font-family:'Montserrat',sans-serif; font-size:17px; font-weight:800; }
        .dev-total-banner { display:flex; align-items:center; gap:13px; background:#eaf3ff; border:1px solid #cfe0ff; border-radius:13px; padding:16px 20px; margin:14px 0 20px; color:#1155cc; font-family:'Montserrat',sans-serif; font-size:14px; font-weight:700; box-shadow:0 3px 10px rgba(17,85,204,.06); }
        .dev-total-banner strong { color:#17345f; font-size:19px; font-weight:800; margin-left:4px; }
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

    if manual.disponivel():
        with st.container(border=True):
            mc1, mc2, mc3 = st.columns([0.65, 4.8, 1.8], vertical_alignment="center")
            with mc1:
                st.markdown(
                    "<div style='width:48px;height:48px;border-radius:12px;background:#eaf3ff;"
                    "display:flex;align-items:center;justify-content:center;color:#1155cc;"
                    "font-size:25px;'>▤</div>",
                    unsafe_allow_html=True,
                )
            with mc2:
                st.markdown(
                    "<div style='color:#172b4d;font-size:18px;font-weight:800;'>Manual de devolução</div>"
                    "<div style='color:#627895;font-size:14px;font-weight:500;'>"
                    "Consulte o procedimento para realizar devoluções.</div>"
                    "<div style='margin-top:5px;display:inline-block;background:#e5f2ff;color:#1155cc;"
                    "border-radius:20px;padding:3px 10px;font-size:11px;font-weight:700;'>Treinamento</div>",
                    unsafe_allow_html=True,
                )
            with mc3:
                manual.botao_manual(key="manual_page3", label="Baixar manual em PDF")

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
