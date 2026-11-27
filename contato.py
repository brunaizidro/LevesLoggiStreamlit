"""
contato.py — formulário "Fale conosco / Dúvidas".

Reutilizável na tela de login (não autenticado) e dentro do app (pré-preenchido
com o e-mail do usuário logado). Envia para o e-mail de suporte definido pelo
admin em Configurações, com Reply-To do remetente.
"""

from __future__ import annotations

import time

import streamlit as st

import emailer

# Intervalo mínimo entre envios (por sessão) para evitar spam.
COOLDOWN_SEG = 60
# Anexos do chamado: só imagens, até 3 arquivos de até 5 MB cada.
TIPOS_IMAGEM = ["png", "jpg", "jpeg"]
MAX_ANEXOS = 3
MAX_MB = 5
SLA_TEXTO = "Respondemos em até 24 horas, somente em dias úteis."


def form_contato(key: str, nome: str = "", email: str = "", horizontal: bool = False):
    """Renderiza o formulário de dúvidas. `key` deve ser único por local de uso.

    `horizontal=True`: duas colunas (dados e mensagem | anexo e envio), mais baixo —
    usado na janela de suporte da tela de login.
    """
    if not emailer.email_suporte() or not emailer.smtp_configurado():
        st.caption("Canal de dúvidas indisponível no momento.")
        return

    ts_key = f"_duvida_ts_{key}"

    with st.form(f"contato_{key}", clear_on_submit=True, border=not horizontal):
        if horizontal:
            esq, dir_ = st.columns([1.25, 1], gap="medium")
        else:
            esq = dir_ = st.container()
        with esq:
            c1, c2 = st.columns(2)
            nome_in = c1.text_input("Seu nome", value=nome, key=f"ct_nome_{key}")
            email_in = c2.text_input("Seu e-mail", value=email, key=f"ct_mail_{key}",
                                     placeholder="para retornarmos")
            msg_in = st.text_area("Sua dúvida", key=f"ct_msg_{key}",
                                  placeholder="Descreva sua dúvida...", height=120 if horizontal else None)
        with dir_:
            arquivos = st.file_uploader(
                "Anexar imagens (opcional)", type=TIPOS_IMAGEM, accept_multiple_files=True,
                key=f"ct_anexo_{key}", help=f"Prints da tela ajudam a resolver mais rápido. Até {MAX_ANEXOS} imagens de {MAX_MB} MB.")
            if not horizontal:
                st.caption(f"⏱ {SLA_TEXTO}")
            enviar = st.form_submit_button("Enviar dúvida", type="primary", width="stretch")

    if enviar:
        restante = COOLDOWN_SEG - (time.time() - st.session_state.get(ts_key, 0))
        if restante > 0:
            st.warning(f"Aguarde {int(restante)}s antes de enviar outra mensagem.")
            return
        arquivos = list(arquivos or [])
        if len(arquivos) > MAX_ANEXOS:
            st.error(f"Envie no máximo {MAX_ANEXOS} imagens.")
            return
        grandes = [a.name for a in arquivos if a.size > MAX_MB * 1024 * 1024]
        if grandes:
            st.error(f"Imagem acima de {MAX_MB} MB: " + ", ".join(grandes))
            return
        anexos = [(a.name, a.getvalue(), a.type or "image/png") for a in arquivos]
        ok, resp = emailer.enviar_duvida(nome_in, email_in, msg_in, anexos=anexos or None)
        if ok:
            st.session_state[ts_key] = time.time()
            st.success(f"Sua mensagem foi enviada. {SLA_TEXTO} Retornaremos por e-mail.")
        else:
            st.error(resp)
