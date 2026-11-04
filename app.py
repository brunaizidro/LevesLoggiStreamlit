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
    st.session_state["tentativas"] = 0


def tela_login():
    # -----------------------------------------------------------------------
    # Primeiro acesso: criação da nova senha
    # -----------------------------------------------------------------------
    usuario_primeiro_acesso = st.session_state.get(
        "usuario_primeiro_acesso"
    )

    if usuario_primeiro_acesso:
        st.markdown(
            """
            <div style="
                max-width: 520px;
                margin: 80px auto 20px auto;
                text-align: center;
                font-family: Montserrat, sans-serif;
            ">
                <h2 style="color:#172033;margin-bottom:8px;">
                    Crie sua nova senha
                </h2>
                <p style="color:#788292;font-size:14px;line-height:1.5;">
                    Este é seu primeiro acesso ao Portal LEVES.
                    Defina uma nova senha para continuar.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
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

    # -----------------------------------------------------------------------
    # CSS exclusivo da tela de login.
    # O restante do portal continua usando o PageStyler normalmente.
    # -----------------------------------------------------------------------
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"], [data-testid="stApp"] {
            font-family: 'Montserrat', sans-serif !important;
        }
        [data-testid="stAppViewContainer"] {
            background: #F4F7FC !important;
            min-height: 100vh;
            position: relative;
            isolation: isolate;
        }
        [data-testid="stAppViewContainer"]::before {
            content: "";
            position: fixed;
            z-index: -1;
            pointer-events: none;
            top: 0; left: -5%; width: 110%; height: 64vh;
            background: linear-gradient(112deg, #0759EF 0%, #0878F8 58%, #08A8EE 100%);
            clip-path: ellipse(105% 100% at 50% 0%);
        }
        [data-testid="stAppViewContainer"]::after {
            content: "";
            position: fixed;
            z-index: -1;
            pointer-events: none;
            inset: 0;
            background:
                radial-gradient(ellipse 24% 23% at 103% 0%, rgba(0,195,238,.92) 0%, rgba(0,195,238,0) 100%),
                radial-gradient(ellipse 19% 20% at -2% 104%, rgba(56,174,255,.78) 0%, rgba(56,174,255,0) 100%);
        }
        [data-testid="stAppViewBlockContainer"] {
            position: relative;
            z-index: 1;
            max-width: 100% !important;
            padding: 2.2rem 18px 2rem !important;
        }
        [data-testid="stHeader"], [data-testid="stToolbar"] {
            background: transparent !important;
            display: none !important;
        }
        [data-testid="column"]:has(.login-title) {
            position: relative !important;
            max-width: 720px !important;
            min-width: min(100%, 320px) !important;
            margin: 112px auto 0 !important;
            padding: 34px 42px 32px !important;
            background: #FFFFFF !important;
            border: 1px solid rgba(222,232,246,.95) !important;
            border-radius: 28px !important;
            box-shadow: 0 22px 58px rgba(15,55,115,.18) !important;
            overflow: visible !important;
        }
        [data-testid="column"]:has(.login-title) [data-testid="stVerticalBlock"] {
            background: transparent !important;
            padding: 0 !important;
            box-shadow: none !important;
        }
        .login-logo {
            position: absolute !important;
            top: -116px !important;
            left: 0 !important;
            right: 0 !important;
            text-align: center !important;
            margin: 0 auto !important;
            height: 78px !important;
        }
        .login-logo img {
            display: block !important;
            width: 210px !important;
            max-width: 72% !important;
            height: auto !important;
            margin: 0 auto !important;
            filter: brightness(0) invert(1) !important;
        }
        .login-title {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 16px;
            text-align: center;
            color: #075BEA !important;
            font-family: 'Montserrat', sans-serif !important;
            font-size: clamp(30px, 4vw, 48px) !important;
            font-weight: 800 !important;
            letter-spacing: -1.8px !important;
            line-height: 1.15 !important;
            margin: 2px 0 20px !important;
        }
        .login-cube {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            flex: 0 0 64px;
            width: 64px;
            height: 64px;
            border-radius: 17px;
            background: #DDF5FF;
        }
        .login-cube svg { width: 38px; height: 38px; }
        .login-description {
            text-align: center;
            color: #63738D !important;
            font-family: 'Montserrat', sans-serif !important;
            font-size: 16px !important;
            font-weight: 500 !important;
            line-height: 1.65 !important;
            max-width: 570px;
            margin: 0 auto 34px !important;
        }
        [data-testid="stForm"] {
            background: transparent !important;
            border: 0 !important;
            border-radius: 0 !important;
            padding: 0 !important;
            box-shadow: none !important;
        }
        [data-testid="stForm"] label {
            color: #253B5B !important;
            font-family: 'Montserrat', sans-serif !important;
            font-size: 14px !important;
            font-weight: 700 !important;
        }
        [data-testid="stForm"] input {
            border-radius: 12px !important;
            border: 1px solid #DCE5F0 !important;
            min-height: 50px !important;
            font-family: 'Montserrat', sans-serif !important;
            background: #FFFFFF !important;
        }
        [data-testid="stForm"] input:focus {
            border-color: #0875F5 !important;
            box-shadow: 0 0 0 3px rgba(0,103,252,.11) !important;
        }
        [data-testid="stFormSubmitButton"] button {
            width: 100% !important;
            min-height: 56px !important;
            margin-top: 12px !important;
            border-radius: 12px !important;
            border: 0 !important;
            background: linear-gradient(90deg,#0759EE,#087BFA) !important;
            color: #FFFFFF !important;
            font-family: 'Montserrat', sans-serif !important;
            font-size: 17px !important;
            font-weight: 800 !important;
            box-shadow: 0 9px 22px rgba(0,103,252,.20) !important;
        }
        [data-testid="stFormSubmitButton"] button:hover {
            background: #064FD0 !important;
            transform: translateY(-1px);
        }
        [data-testid="stAppViewContainer"] .stButton > button,
        [data-testid="stAppViewContainer"] .stDownloadButton > button {
            border-radius: 12px !important;
            min-height: 50px !important;
            font-family: 'Montserrat', sans-serif !important;
            font-weight: 700 !important;
        }
        [data-testid="stAppViewContainer"] .stButton > button {
            border: 1px solid #DCE5F0 !important;
            background: #FFFFFF !important;
            color: #243B5B !important;
        }
        [data-testid="stAppViewContainer"] .stButton > button:hover {
            border-color: #0875F5 !important;
            color: #075BEA !important;
        }
        [data-testid="stDownloadButton"] button {
            background: #F0F7FF !important;
            border: 1px solid #DCEBFF !important;
            color: #174A91 !important;
            width: 100% !important;
        }
        [data-testid="stAlert"] {
            border-radius: 12px !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        .login-manual { margin-top: 18px !important; }
        .login-help-title {
            text-align: center;
            color: #7D8DA4;
            font-family: 'Montserrat', sans-serif;
            font-size: 12px;
            font-weight: 600;
            margin: 22px 0 8px;
        }
        [data-testid="stExpander"] {
            border: 1px solid #E1E8F2 !important;
            border-radius: 12px !important;
            background: #FFFFFF !important;
            overflow: hidden !important;
        }
        [data-testid="stExpander"] summary {
            font-family: 'Montserrat', sans-serif !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            color: #29415F !important;
        }
        .login-footer {
            text-align: center;
            color: #9AA8BA;
            font-family: 'Montserrat', sans-serif;
            font-size: 11px;
            margin-top: 20px;
        }
        @media (max-width: 700px) {
            [data-testid="stAppViewBlockContainer"] { padding: 1.5rem 12px 2rem !important; }
            [data-testid="column"]:has(.login-title) {
                padding: 28px 20px 24px !important;
                margin-top: 96px !important;
                border-radius: 22px !important;
            }
            .login-logo { top: -100px !important; }
            .login-logo img { width: 178px !important; }
            .login-title { gap: 10px; font-size: 30px !important; letter-spacing: -1px !important; }
            .login-cube { flex-basis: 48px; width: 48px; height: 48px; border-radius: 13px; }
            .login-cube svg { width: 30px; height: 30px; }
            .login-description { font-size: 13px !important; margin-bottom: 26px !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, col, _ = st.columns([1, 1.7, 1])

    with col:
        base = os.path.dirname(os.path.abspath(__file__))
        caminho_logo = os.path.join(base, LOGO_LOGIN_PATH)
        logo_base64 = (
            get_base64_image(caminho_logo)
            if os.path.exists(caminho_logo)
            else ""
        )

        # Logo + título
        if logo_base64:
            st.markdown(
                f"""
                <div class="login-logo">
                    <img src="data:image/png;base64,{logo_base64}">
                </div>
                <div class="login-title"><span class="login-cube"><svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M24 4L43 14.5V34L24 44L5 34V14.5L24 4Z" stroke="#0786F7" stroke-width="2.8" stroke-linejoin="round"/><path d="M5.5 14.5L24 25L42.5 14.5M24 25V43.5M14.5 9.5L33.5 20" stroke="#0786F7" stroke-width="2.8" stroke-linejoin="round"/></svg></span>Portal Leves</div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="login-logo">
                    <div style="
                        color:#0067fc;
                        font-size:36px;
                        font-weight:800;
                        font-family:Montserrat,sans-serif;
                    ">loggi</div>
                </div>
                <div class="login-title">Portal LEVES</div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            """
            <div class="login-description">
                Acesse o portal para consultar os insumos
                enviados para sua operação.
            </div>
            """,
            unsafe_allow_html=True,
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
            st.markdown("### Redefinir senha")

            if not st.session_state.get("recuperacao_codigo_enviado"):
                with st.form("solicitar_recuperacao"):
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
                    if not (email_rec or "").strip() or "@" not in email_rec:
                        st.error("Digite um endereço de e-mail válido.")
                    else:
                        try:
                            ok, mensagem, usuario_encontrado = auth.solicitar_recuperacao_por_email(email_rec)
                            if ok and usuario_encontrado:
                                st.session_state["recuperacao_usuario"] = usuario_encontrado
                                st.session_state["recuperacao_codigo_enviado"] = True
                                st.success("Código solicitado. Confira sua caixa de entrada e o spam.")
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

        # Manual
        if manual.disponivel():
            st.markdown(
                '<div class="login-manual">',
                unsafe_allow_html=True,
            )
            manual.botao_manual(key="manual_login")
            st.markdown("</div>", unsafe_allow_html=True)

        # Suporte
        st.markdown(
            '<div class="login-help-title">Precisa de ajuda?</div>',
            unsafe_allow_html=True,
        )

        with st.expander("💬 Falar com o suporte"):
            contato.form_contato(key="login")

        st.markdown(
            """
            <div class="login-footer">
                Portal LEVES · Loggi
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    _init_state()
    estilizador = PageStyler()
    estilizador.apply_general_css()

    if not st.session_state["usuario"]:
        tela_login()
        return

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
            opcoes = ["📥 Recebimento"]
        elif eh_admin:
            opcoes = [
                "📦 Envios",
                "📥 Recebimento",
                "🧾 Conciliação",
                "💰 Cobranças",
                "↩️ Devoluções",
                "🔔 Pendências",
                "👥 Usuários",
                "📊 Relatórios",
                "⚙️ Configurações",
            ]
        elif user.get("perfil") == "gdl":
            opcoes = [
                "📦 Envios",
                "🧾 Conciliação",
                "↩️ Devoluções",
                "👥 Usuários",
            ]
        else:
            opcoes = ["📦 Envios", "↩️ Devoluções", "💰 Cobranças"]

        # Se veio de um QR, já abre o Recebimento.
        idx = 0
        if scan_id and (eh_admin or eh_receb):
            idx = next(
                (i for i, o in enumerate(opcoes) if "Recebimento" in o),
                0,
            )

        if len(opcoes) > 1:
            pagina = st.radio(
                "Navegação",
                opcoes,
                index=idx,
                label_visibility="collapsed",
            )
        else:
            pagina = opcoes[0]

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
        if "Usuários" in pagina:
            page_2()
        elif "Conciliação" in pagina:
            page_6()
        elif "Pendências" in pagina:
            page_8()
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
    except Exception as e:  # noqa: BLE001
        st.error(
            "Erro ao acessar a planilha: "
            f"{e}. Verifique a chave da service account (veja o README)."
        )


if __name__ == "__main__":
    main()
