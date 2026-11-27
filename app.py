"""
app.py — Portal LEVES (Loggi) — camada de apresentação (padrão DLE).

Configura a página, aplica o estilo, trata o login próprio (multi-tenant) e
roteia entre as páginas via st.sidebar.radio.

Fluxo: data_extraction -> data_processing -> page_N() -> app.main()
Executar:  streamlit run app.py
"""

from __future__ import annotations

import os
import streamlit as st
import auth
import contato
import manual
from streamlit_estilizador import PageStyler
from streamlit_sidebar import get_base64_image, sidebar

LOGO_LOGIN_PATH = "image_simbolo_lebre.png"

st.set_page_config(page_title="Portal LEVES — Loggi", page_icon="📦", layout="wide")
from page_1 import page_1  # noqa: E402
from page_2 import page_2  # noqa: E402
from page_3 import page_3  # noqa: E402
from page_4 import page_4  # noqa: E402
from page_5 import page_5  # noqa: E402
from page_6 import page_6  # noqa: E402
from page_7 import page_7  # noqa: E402
from page_8 import page_8  # noqa: E402
from page_9 import page_9  # noqa: E402
from page_10 import page_10  # noqa: E402
from page_inicio import page_inicio  # noqa: E402
import portal_leve  # noqa: E402
import login_visual  # noqa: E402
import portal_admin  # noqa: E402
from page_pendencias_leve import page_pendencias_leve  # noqa: E402

# ---------------------------------------------------------------------------
# Sessão / login
# ---------------------------------------------------------------------------
def _init_state():
    st.session_state.setdefault("usuario", None)
    st.session_state.setdefault("tentativas", 0)
    st.session_state.setdefault("usuario_primeiro_acesso", None)
    st.session_state.setdefault("recuperacao_senha", False)
    st.session_state.setdefault("recuperacao_codigo_enviado", False)
    st.session_state.setdefault("recuperacao_usuario", "")


def logout():
    st.session_state["usuario"] = None
    # Próximo login começa na tela inicial.
    st.session_state.pop("pagina_navegacao_leves", None)
    st.session_state["tentativas"] = 0


@st.dialog("Falar com o suporte", width="large")
def _janela_suporte():
    st.markdown(
        "<div class='lg-dlg-sub'>Conte o que aconteceu e, se puder, anexe um print da tela."
        " <span class='lg-dlg-sla'>Resposta em até 24h úteis</span></div>",
        unsafe_allow_html=True,
    )
    contato.form_contato(key="login", horizontal=True)


def tela_login():
    """Tela de login: painel da marca à esquerda e formulário à direita."""
    login_visual.aplicar_css()
    with st.container(key="lg-tela"):
        marca, formulario = st.columns([1.05, 1], gap=None)
        with marca:
            login_visual.painel_marca()
        with formulario, st.container(key="lg-form"):
            _tela_login_conteudo()


def _tela_login_conteudo():
    # -----------------------------------------------------------------------
    # Primeiro acesso: criação da nova senha
    # -----------------------------------------------------------------------
    usuario_primeiro_acesso = st.session_state.get(
        "usuario_primeiro_acesso"
    )

    if usuario_primeiro_acesso:
        login_visual.cabecalho(
            "Crie sua nova senha",
            "Este é seu primeiro acesso ao Portal Leves. Defina uma nova senha para continuar.",
        )

        with st.form("primeiro_acesso"):
            nova_senha = st.text_input(
                "Nova senha",
                type="password",
                placeholder="Digite sua nova senha",
            )
            confirmar_senha = st.text_input(
                "Confirmar nova senha",
                type="password",
                placeholder="Digite novamente sua senha",
            )
            salvar = st.form_submit_button(
                "Salvar nova senha",
                type="primary",
                width="stretch",
            )

        if salvar:
            if nova_senha != confirmar_senha:
                st.error("As senhas não são iguais.")
            elif not hasattr(auth, "alterar_senha"):
                st.error(
                    "A função de alteração de senha não está disponível no auth.py."
                )
            else:
                try:
                    ok, mensagem = auth.alterar_senha(
                        usuario_primeiro_acesso["usuario"],
                        nova_senha,
                    )
                except Exception as e:
                    st.error(f"Não foi possível alterar a senha: {e}")
                    return

                if ok:
                    try:
                        u = auth.autenticar(
                            usuario_primeiro_acesso["usuario"],
                            nova_senha,
                        )
                    except Exception as e:
                        st.error(
                            "Senha criada, mas não foi possível concluir "
                            f"o login: {e}"
                        )
                        return

                    if u:
                        st.session_state["usuario_primeiro_acesso"] = None
                        st.session_state["usuario"] = u
                        st.rerun()
                    else:
                        st.error(
                            "A senha foi alterada, mas não foi possível "
                            "validar o acesso. Tente entrar novamente."
                        )
                else:
                    st.error(mensagem)

        return

    if True:
        with st.container(key="login_card"):
            login_visual.cabecalho(
                "Acesse sua conta",
                "Entre com seu usuário e senha para acompanhar os insumos da sua operação.",
            )

            if st.session_state["tentativas"] >= 5:
                st.error("Muitas tentativas. Recarregue a página e tente novamente.")

            # Login — a lógica de autenticação permanece exatamente igual.
            with st.form("login"):
                usuario = st.text_input(
                    "Usuário",
                    placeholder="Digite seu usuário",
                )
                senha = st.text_input(
                    "Senha",
                    type="password",
                    placeholder="Digite sua senha",
                )
                entrar = st.form_submit_button(
                    "Entrar",
                    type="primary",
                    width="stretch",
                )

            if entrar and st.session_state["tentativas"] < 5:
                usuario = (usuario or "").strip()
                senha = senha or ""

                try:
                    if hasattr(auth, "diagnosticar_login"):
                        valido, mensagem, u = auth.diagnosticar_login(
                            usuario,
                            senha,
                        )
                    else:
                        u = auth.autenticar(usuario, senha)
                        valido = bool(u)
                        mensagem = (
                            "Login validado com sucesso."
                            if valido
                            else "Usuário ou senha inválidos."
                        )
                except Exception as e:
                    st.error(
                        "Não foi possível validar o login. "
                        f"Detalhes: {e}"
                    )
                    return

                if not valido:
                    st.session_state["tentativas"] += 1
                    st.error(mensagem)
                else:
                    st.session_state["tentativas"] = 0

                    if u.get("primeiro_acesso"):
                        st.session_state["usuario_primeiro_acesso"] = u
                        st.rerun()
                    else:
                        st.session_state["usuario"] = u
                        st.rerun()

            if st.button("Esqueci minha senha", width="stretch", key="btn_esqueci_senha"):
                st.session_state["recuperacao_senha"] = True
                st.session_state["recuperacao_codigo_enviado"] = False
                st.rerun()

            if st.session_state.get("recuperacao_senha"):
                st.markdown("<div class='lg-rec'>Redefinir senha</div>", unsafe_allow_html=True)

                if not st.session_state.get("recuperacao_codigo_enviado"):
                    with st.form("solicitar_recuperacao"):
                        usuario_rec = st.text_input(
                            "Usuário",
                            placeholder="Digite seu login (ex.: TF3)",
                        )
                        email_rec = st.text_input(
                            "E-mail cadastrado",
                            placeholder="Digite seu e-mail",
                        )
                        enviar_codigo = st.form_submit_button(
                            "Enviar código de recuperação",
                            type="primary",
                            width="stretch",
                        )

                    if enviar_codigo:
                        if not (usuario_rec or "").strip():
                            st.error("Digite seu usuário.")
                        elif not (email_rec or "").strip() or "@" not in email_rec:
                            st.error("Digite um endereço de e-mail válido.")
                        else:
                            try:
                                ok, mensagem, usuario_encontrado = auth.solicitar_recuperacao_por_email(
                                    email_rec, usuario_rec
                                )
                                if ok and usuario_encontrado:
                                    st.session_state["recuperacao_usuario"] = usuario_encontrado
                                    st.session_state["recuperacao_codigo_enviado"] = True
                                    st.success("Código enviado. Confira sua caixa de entrada e o spam.")
                                    st.rerun()
                                elif ok:
                                    st.info(mensagem)
                                else:
                                    st.error(mensagem)
                            except Exception as e:
                                st.error(f"Não foi possível enviar o código: {e}")
                else:
                    st.info("Digite o código de 6 dígitos recebido por e-mail.")
                    with st.form("redefinir_senha"):
                        codigo = st.text_input("Código de recuperação", max_chars=6)
                        nova_senha = st.text_input("Nova senha", type="password")
                        confirmar = st.text_input("Confirmar nova senha", type="password")
                        redefinir = st.form_submit_button("Redefinir senha", type="primary", width="stretch")

                    if redefinir:
                        if nova_senha != confirmar:
                            st.error("As senhas não são iguais.")
                        else:
                            try:
                                ok, mensagem = auth.redefinir_senha_com_codigo(
                                    st.session_state["recuperacao_usuario"], codigo, nova_senha
                                )
                                if ok:
                                    st.success("Senha redefinida com sucesso. Você já pode entrar com a nova senha.")
                                    st.session_state["recuperacao_senha"] = False
                                    st.session_state["recuperacao_codigo_enviado"] = False
                                    st.session_state["recuperacao_usuario"] = ""
                                    st.rerun()
                                else:
                                    st.error(mensagem)
                            except Exception as e:
                                st.error(f"Não foi possível redefinir a senha: {e}")

                if st.button("← Voltar para o login", width="stretch", key="btn_voltar_login"):
                    st.session_state["recuperacao_senha"] = False
                    st.session_state["recuperacao_codigo_enviado"] = False
                    st.session_state["recuperacao_usuario"] = ""
                    st.rerun()

            # Suporte (o manual saiu da tela de login).
            st.markdown("<div class='lg-sep'>Precisa de ajuda?</div>", unsafe_allow_html=True)
            if st.button("Falar com o suporte", key="lg-btn-suporte", width="stretch",
                         icon=":material/support_agent:"):
                _janela_suporte()

        st.markdown("<div class='lg-foot'>Portal LEVES · Loggi</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    _init_state()
    # Tela branca com a lebre enquanto carrega (login e troca de módulo).
    login_visual.tela_carregando()

    # Portal da Leve (perfil operação): portal próprio, leve e sem o CSS
    # global antigo. Admin, GDL e Recebimento seguem no app abaixo.
    _u = st.session_state.get("usuario") or {}
    _perfil = str(_u.get("perfil", "")).lower() if _u else ""
    if _u and _perfil not in ("admin", "gdl", "recebimento"):
        portal_leve.render(_u, logout)
        return
    # Admin: portal novo (Gestão de Materiais).
    if _u and _perfil == "admin":
        portal_admin.render(_u, logout)
        return

    if not st.session_state["usuario"]:
        tela_login()
        return

    estilizador = PageStyler()
    estilizador.apply_general_css()

    user = st.session_state["usuario"]
    perfil = user.get("perfil")
    eh_admin = perfil == "admin"
    eh_receb = perfil == "recebimento"

    # Devolução aberta pelo QR (id + token na URL).
    scan_id = st.query_params.get("dev")
    scan_token = st.query_params.get("t")

    sidebar()

    with st.sidebar:
        papel = {"admin": "Administrador", "recebimento": "Recebimento"}.get(
            perfil, f"Destino: {user['destino']}"
        )

        st.markdown(
            f"<div class='sb-card'><div class='nome'>{user['nome']}</div>"
            f"<div class='papel'>{papel}</div></div>",
            unsafe_allow_html=True,
        )

        if eh_receb:
            opcoes = ["Recebimentos"]
        elif eh_admin:
            opcoes = [
                "Início",
                "Envios",
                "Recebimentos",
                "Conciliação",
                "Cobranças",
                "Devoluções",
                "Pendências",
                "Usuários",
                "Relatórios",
                "Configurações",
            ]
        elif user.get("perfil") == "gdl":
            opcoes = ["Início", "Envios", "Conciliação", "Devoluções", "Pendências", "Usuários"]
        else:
            opcoes = ["Início", "Envios", "Devoluções", "Pendências", "Cobranças"]

        # Mantém a abertura de Recebimentos quando o usuário chega por QR Code.
        chave_pagina = "pagina_navegacao_leves"
        if scan_id and (eh_admin or eh_receb) and "Recebimentos" in opcoes:
            st.session_state[chave_pagina] = "Recebimentos"

        pagina = st.session_state.get(chave_pagina)
        if pagina not in opcoes:
            pagina = opcoes[0]
            st.session_state[chave_pagina] = pagina

        icones_menu = {
            "Início": ":material/home:",
            "Envios": ":material/inventory_2:",
            "Recebimentos": ":material/inbox:",
            "Conciliação": ":material/receipt_long:",
            "Cobranças": ":material/paid:",
            "Devoluções": ":material/undo:",
            "Pendências": ":material/notifications:",
            "Usuários": ":material/groups:",
            "Relatórios": ":material/bar_chart:",
            "Configurações": ":material/settings:",
        }
        slugs_menu = {
            "Início": "inicio",
            "Envios": "envios",
            "Recebimentos": "recebimentos",
            "Conciliação": "conciliacao",
            "Cobranças": "cobrancas",
            "Devoluções": "devolucoes",
            "Pendências": "pendencias",
            "Usuários": "usuarios",
            "Relatórios": "relatorios",
            "Configurações": "configuracoes",
        }
        modulos_operacao = [
            nome for nome in opcoes
            if nome in ["Início", "Envios", "Recebimentos", "Conciliação", "Cobranças", "Devoluções", "Pendências"]
        ]
        modulos_admin = [
            nome for nome in opcoes
            if nome in ["Usuários", "Relatórios", "Configurações"]
        ]

        with st.container(key="leves-nav-menu"):
            if modulos_operacao:
                st.markdown('<div class="leves-nav-section">OPERAÇÃO</div>', unsafe_allow_html=True)
                for nome in modulos_operacao:
                    if st.button(
                        nome,
                        key=f"nav_leves_{slugs_menu[nome]}",
                        type="primary" if pagina == nome else "secondary",
                        width="stretch",
                    ):
                        st.session_state[chave_pagina] = nome
                        st.rerun()

            if modulos_admin:
                st.markdown(
                    '<div class="leves-nav-admin"><div class="leves-nav-divider"></div>'
                    '<div class="leves-nav-section">ADMINISTRAÇÃO</div></div>',
                    unsafe_allow_html=True,
                )
                for nome in modulos_admin:
                    if st.button(
                        nome,
                        key=f"nav_leves_{slugs_menu[nome]}",
                        type="primary" if pagina == nome else "secondary",
                        width="stretch",
                    ):
                        st.session_state[chave_pagina] = nome
                        st.rerun()

        st.markdown("<hr class='sb-sep'>", unsafe_allow_html=True)

        manual.botao_manual(key="manual_side")

        if st.button("↻ Atualizar dados", width="stretch"):
            import data_extraction
            data_extraction.limpar_cache()
            st.rerun()

        if st.button("Sair", width="stretch"):
            logout()
            st.rerun()

        with st.expander("💬 Dúvidas / suporte"):
            contato.form_contato(
                key="app",
                nome=user.get("nome", ""),
                email=user.get("email", ""),
            )

    try:
        if pagina == "Início":
            page_inicio(opcoes)
        elif "Usuários" in pagina:
            page_2()
        elif "Conciliação" in pagina:
            page_6()
        elif "Pendências" in pagina:
            page_8() if (eh_admin or perfil == "gdl") else page_pendencias_leve()
        elif "Relatórios" in pagina:
            page_5()
        elif "Configurações" in pagina:
            page_7()
        elif "Recebimento" in pagina:
            page_4(
                scan_id if (eh_admin or eh_receb) else None,
                scan_token,
            )
        elif "Devoluções" in pagina:
            page_3()
        elif "Cobranças" in pagina:
            page_10() if eh_admin else page_9()
        else:
            page_1()

        # Ajuste global de altura: mantém todos os módulos próximos ao topo.
        # Este CSS é injetado após a renderização da página para prevalecer
        # sobre estilos locais dos módulos.
        st.markdown(
            """
            <style>
            [data-testid="stAppViewContainer"] [data-testid="stMain"],
            [data-testid="stAppViewContainer"] [data-testid="stMainBlockContainer"],
            [data-testid="stAppViewContainer"] [data-testid="stAppViewBlockContainer"],
            [data-testid="stAppViewContainer"] section.main,
            [data-testid="stAppViewContainer"] section.main > div,
            [data-testid="stAppViewContainer"] .main .block-container {
                padding-top: 8px !important;
                margin-top: 0 !important;
                scroll-padding-top: 8px !important;
            }
            [data-testid="stAppViewContainer"] [data-testid="stMain"] {
                align-items: flex-start !important;
            }
            [data-testid="stAppViewContainer"] [data-testid="stVerticalBlock"] {
                row-gap: 0.7rem !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    except Exception as e:  # noqa: BLE001
        st.error(
            "Erro ao acessar a planilha: "
            f"{e}. Verifique a chave da service account (veja o README)."
        )


if __name__ == "__main__":
    main()
