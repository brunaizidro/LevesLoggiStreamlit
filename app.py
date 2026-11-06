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
        /* Logo separado; o cartão começa no título Portal Leves. */
        .login-logo {
            position: relative !important;
            top: auto !important;
            left: auto !important;
            right: auto !important;
            text-align: center !important;
            margin: 0 auto 34px !important;
            height: auto !important;
        }
        .login-logo-fallback {
            color: #FFFFFF !important;
            font-size: 42px !important;
            font-weight: 800 !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        /* Streamlit adiciona esta classe ao container com key=login_card. */
        .st-key-login_card {
            box-sizing: border-box !important;
            width: 100% !important;
            max-width: 720px !important;
            margin: 0 auto !important;
            padding: 32px 42px 30px !important;
            background: #FFFFFF !important;
            border: 1px solid rgba(222,232,246,.98) !important;
            border-radius: 28px !important;
            box-shadow: 0 22px 58px rgba(15,55,115,.18) !important;
            overflow: visible !important;
        }
        .st-key-login_card > [data-testid="stVerticalBlock"] {
            gap: 0.8rem !important;
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
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,500,0,0');

        /* Rótulos dos campos em negrito */
        [data-testid="stForm"] label,
        [data-testid="stTextInput"] label,
        [data-testid="stTextInput"] label p {
            color: #253B5B !important;
            font-family: 'Montserrat', sans-serif !important;
            font-size: 14px !important;
            font-weight: 800 !important;
        }

        /* Ícone de usuário dentro do campo Usuário */
        [data-testid="stTextInput"]:has(input[placeholder="Digite seu usuário"]) {
            position: relative !important;
        }
        [data-testid="stTextInput"]:has(input[placeholder="Digite seu usuário"])::after {
            content: "person";
            font-family: "Material Symbols Rounded";
            font-size: 21px;
            font-weight: 500;
            color: #71829A;
            position: absolute;
            left: 14px;
            bottom: 13px;
            z-index: 2;
            pointer-events: none;
        }
        [data-testid="stTextInput"]:has(input[placeholder="Digite seu usuário"]) input {
            padding-left: 44px !important;
        }

        /* Cadeado dentro do campo Senha */
        [data-testid="stTextInput"]:has(input[placeholder="Digite sua senha"]) {
            position: relative !important;
        }
        [data-testid="stTextInput"]:has(input[placeholder="Digite sua senha"])::after {
            content: "lock";
            font-family: "Material Symbols Rounded";
            font-size: 21px;
            font-weight: 500;
            color: #71829A;
            position: absolute;
            left: 14px;
            bottom: 13px;
            z-index: 2;
            pointer-events: none;
        }
        [data-testid="stTextInput"]:has(input[placeholder="Digite sua senha"]) input {
            padding-left: 44px !important;
        }

        /* Botão de recuperação em negrito */
        .st-key-btn_esqueci_senha button {
            font-weight: 800 !important;
            font-family: 'Montserrat', sans-serif !important;
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

        /* Login em uma única tela: dimensões compactas e sem rolagem vertical. */
        html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"] {
            height: 100% !important;
            min-height: 100% !important;
            overflow: hidden !important;
        }
        [data-testid="stAppViewContainer"] {
            height: 100vh !important;
            height: 100dvh !important;
            overflow: hidden !important;
        }
        [data-testid="stAppViewMain"] {
            height: 100vh !important;
            height: 100dvh !important;
            overflow: hidden !important;
        }
        [data-testid="stAppViewBlockContainer"] {
            box-sizing: border-box !important;
            height: 100vh !important;
            height: 100dvh !important;
            min-height: 0 !important;
            overflow: hidden !important;
            padding: clamp(8px, 1.4vh, 14px) 14px 6px !important;
        }
        .login-logo {
            margin: 0 auto clamp(8px, 1.3vh, 14px) !important;
        }
        .login-logo img {
            width: clamp(112px, 17vh, 158px) !important;
            max-height: 8vh !important;
            object-fit: contain !important;
        }
        .st-key-login_card {
            max-width: 650px !important;
            padding: clamp(12px, 1.8vh, 20px) clamp(18px, 3vw, 32px) clamp(10px, 1.5vh, 16px) !important;
            border-radius: 22px !important;
        }
        .st-key-login_card > [data-testid="stVerticalBlock"] {
            gap: clamp(5px, .8vh, 9px) !important;
        }
        .login-title {
            font-size: clamp(25px, 4vh, 38px) !important;
            gap: 11px !important;
            margin: 0 0 clamp(7px, 1.1vh, 12px) !important;
            letter-spacing: -1px !important;
        }
        .login-cube {
            flex-basis: clamp(42px, 5.5vh, 52px) !important;
            width: clamp(42px, 5.5vh, 52px) !important;
            height: clamp(42px, 5.5vh, 52px) !important;
            border-radius: 13px !important;
        }
        .login-cube svg { width: 30px !important; height: 30px !important; }
        .login-description {
            font-size: clamp(11px, 1.6vh, 14px) !important;
            line-height: 1.4 !important;
            margin: 0 auto clamp(8px, 1.2vh, 13px) !important;
        }
        [data-testid="stForm"] {
            padding: 0 !important;
        }
        [data-testid="stForm"] label,
        [data-testid="stTextInput"] label,
        [data-testid="stTextInput"] label p {
            font-size: 12px !important;
            margin-bottom: 2px !important;
        }
        [data-testid="stForm"] input {
            min-height: 40px !important;
            height: 40px !important;
        }
        [data-testid="stFormSubmitButton"] button {
            min-height: 44px !important;
            height: 44px !important;
            margin-top: 5px !important;
            font-size: 15px !important;
        }
        .st-key-btn_esqueci_senha button,
        [data-testid="stAppViewContainer"] .stButton > button {
            min-height: 40px !important;
            height: 40px !important;
            font-size: 13px !important;
        }
        .login-manual { margin-top: 5px !important; }
        [data-testid="stDownloadButton"] button {
            min-height: 40px !important;
            height: 40px !important;
            font-size: 12px !important;
        }
        .login-help-title {
            font-size: 11px !important;
            margin: clamp(6px, 1vh, 10px) 0 3px !important;
        }
        [data-testid="stExpander"] summary {
            font-size: 11px !important;
        }
        [data-testid="stExpander"] {
            margin-top: 0 !important;
        }
        @media (max-width: 700px) {
            [data-testid="stAppViewBlockContainer"] { padding: 1.5rem 12px 2rem !important; }
            .st-key-login_card {
                padding: 25px 20px 23px !important;
                border-radius: 22px !important;
            }
            .login-logo { margin-bottom: 24px !important; }
            .login-logo img { width: 178px !important; }
            .login-title { gap: 10px; font-size: 30px !important; letter-spacing: -1px !important; }
            .login-cube { flex-basis: 48px; width: 48px; height: 48px; border-radius: 13px; }
            .login-cube svg { width: 30px; height: 30px; }
            .login-description { font-size: 13px !important; margin-bottom: 26px !important; }
        }


        /* Ajustes solicitados: sem brilho inferior, título maior e logo mais alta. */
        [data-testid="stAppViewContainer"]::after {
            background:
                radial-gradient(ellipse 24% 23% at 103% 0%, rgba(0,195,238,.92) 0%, rgba(0,195,238,0) 100%) !important;
        }
        .login-title {
            font-size: clamp(30px, 4vw, 48px) !important;
            letter-spacing: -1.8px !important;
        }
        .login-logo {
            transform: translateY(-4vh) !important;
        }
        @media (max-width: 700px) {
            .login-title {
                font-size: clamp(30px, 4vw, 40px) !important;
            }
            .login-logo {
                transform: translateY(-3vh) !important;
            }
        }

        /* Ajustes finais para aproximar o login da referência visual */
        [data-testid="stAppViewBlockContainer"] > div [data-testid="stHorizontalBlock"] {
            transform: translateY(-5vh) !important;
        }
        .login-logo {
            transform: translateY(-1.5vh) !important;
            margin-bottom: clamp(5px, .8vh, 9px) !important;
        }
        .login-logo img {
            width: clamp(118px, 15vh, 145px) !important;
            max-height: 7vh !important;
        }
        .st-key-login_card {
            max-width: 610px !important;
            padding: clamp(10px, 1.3vh, 15px) clamp(18px, 2.2vw, 26px) clamp(9px, 1.1vh, 13px) !important;
            border-radius: 22px !important;
        }
        .st-key-login_card > [data-testid="stVerticalBlock"] {
            gap: clamp(4px, .55vh, 6px) !important;
        }
        .login-title {
            font-size: clamp(24px, 3.4vh, 34px) !important;
            margin-bottom: clamp(4px, .7vh, 8px) !important;
        }
        .login-cube {
            align-items: center !important;
            justify-content: center !important;
        }
        .login-description {
            margin-bottom: clamp(6px, .9vh, 10px) !important;
            line-height: 1.35 !important;
        }
        /* Centraliza verticalmente os ícones de usuário e cadeado nos inputs. */
        [data-testid="stTextInput"]:has(input[placeholder="Digite seu usuário"])::after,
        [data-testid="stTextInput"]:has(input[placeholder="Digite sua senha"])::after {
            top: 47px !important;
            bottom: auto !important;
            transform: translateY(-50%) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            height: 22px !important;
        }
        [data-testid="stFormSubmitButton"] button {
            font-weight: 800 !important;
        }
        .st-key-btn_esqueci_senha button {
            font-weight: 800 !important;
        }
        /* Manual com azul claro e tipografia em negrito. */
        [data-testid="stDownloadButton"] button {
            color: #36B9F5 !important;
            background: #EFF9FF !important;
            border: 1px solid #D7F0FF !important;
            font-family: 'Montserrat', sans-serif !important;
            font-weight: 800 !important;
            min-height: 38px !important;
            height: 38px !important;
            font-size: 12px !important;
        }
        .login-manual {
            margin-top: 3px !important;
        }
        @media (max-width: 700px) {
            [data-testid="stAppViewBlockContainer"] > div [data-testid="stHorizontalBlock"] {
                transform: translateY(-2vh) !important;
            }
            .st-key-login_card {
                max-width: 100% !important;
                padding: 12px 16px 10px !important;
            }
            .login-logo img { width: 118px !important; }
        }

        /* Aumento final do título e da marca Loggi — sobrescreve regras anteriores. */
        .login-title {
            font-size: clamp(38px, 5.2vh, 52px) !important;
            letter-spacing: -2px !important;
            line-height: 1.08 !important;
        }
        .login-logo {
            transform: translateY(-5vh) !important;
            margin-bottom: clamp(5px, .8vh, 10px) !important;
        }
        .login-logo img {
            width: clamp(155px, 20vh, 190px) !important;
            max-height: 10vh !important;
            height: auto !important;
            object-fit: contain !important;
        }
        @media (max-width: 700px) {
            .login-title {
                font-size: clamp(34px, 8vw, 43px) !important;
                letter-spacing: -1.4px !important;
            }
            .login-logo {
                transform: translateY(-3.5vh) !important;
            }
            .login-logo img {
                width: clamp(140px, 28vw, 170px) !important;
                max-height: 9vh !important;
            }
        }

        /* Refinamento do cartão de login: compacto, simples e com respiro interno. */
        .st-key-login_card {
            box-sizing: border-box !important;
            width: 100% !important;
            max-width: 590px !important;
            padding: 22px 30px 34px !important;
            border-radius: 22px !important;
        }
        .st-key-login_card > [data-testid="stVerticalBlock"] {
            gap: 10px !important;
        }
        .login-title {
            font-size: clamp(36px, 4.6vh, 46px) !important;
            gap: 12px !important;
            line-height: 1.12 !important;
            margin: 2px 0 10px !important;
            letter-spacing: -1.5px !important;
        }
        .login-cube {
            flex: 0 0 52px !important;
            width: 52px !important;
            height: 52px !important;
            border-radius: 14px !important;
        }
        .login-cube svg {
            width: 31px !important;
            height: 31px !important;
        }
        .login-description {
            max-width: 500px !important;
            font-size: 13px !important;
            line-height: 1.55 !important;
            margin: 0 auto 14px !important;
        }
        [data-testid="stForm"] input {
            min-height: 44px !important;
            height: 44px !important;
        }
        [data-testid="stFormSubmitButton"] button {
            min-height: 48px !important;
            height: 48px !important;
            margin-top: 8px !important;
        }
        .st-key-btn_esqueci_senha button,
        [data-testid="stAppViewContainer"] .stButton > button {
            min-height: 42px !important;
            height: 42px !important;
        }
        .login-manual {
            margin-top: 10px !important;
        }
        [data-testid="stDownloadButton"] button {
            min-height: 44px !important;
            height: 44px !important;
        }
        @media (max-width: 700px) {
            .st-key-login_card {
                max-width: 100% !important;
                padding: 20px 20px 28px !important;
            }
            .login-title {
                font-size: clamp(32px, 8vw, 40px) !important;
                gap: 9px !important;
            }
            .login-cube {
                flex-basis: 46px !important;
                width: 46px !important;
                height: 46px !important;
            }
            .login-description {
                font-size: 12px !important;
                margin-bottom: 12px !important;
            }
        }

        /* Layout final conforme referência: cartão menor e conteúdo inteiro visível. */
        .st-key-login_card {
            box-sizing: border-box !important;
            width: 100% !important;
            max-width: 540px !important;
            padding: 20px 30px 24px !important;
            border-radius: 22px !important;
        }
        .st-key-login_card > [data-testid="stVerticalBlock"] {
            gap: 7px !important;
        }
        .login-title {
            font-size: clamp(36px, 4.8vh, 44px) !important;
            line-height: 1.08 !important;
            gap: 11px !important;
            margin: 0 0 7px !important;
            letter-spacing: -1.5px !important;
        }
        .login-cube {
            flex: 0 0 50px !important;
            width: 50px !important;
            height: 50px !important;
            border-radius: 14px !important;
        }
        .login-cube svg {
            width: 30px !important;
            height: 30px !important;
        }
        .login-description {
            max-width: 470px !important;
            font-size: 13px !important;
            line-height: 1.45 !important;
            margin: 0 auto 9px !important;
        }
        [data-testid="stForm"] label,
        [data-testid="stTextInput"] label,
        [data-testid="stTextInput"] label p {
            font-size: 12px !important;
            margin-bottom: 2px !important;
        }
        [data-testid="stForm"] input {
            min-height: 42px !important;
            height: 42px !important;
        }
        [data-testid="stFormSubmitButton"] button {
            min-height: 44px !important;
            height: 44px !important;
            margin-top: 5px !important;
            font-size: 15px !important;
        }
        .st-key-btn_esqueci_senha button,
        [data-testid="stAppViewContainer"] .stButton > button {
            min-height: 42px !important;
            height: 42px !important;
            font-size: 13px !important;
        }
        .login-manual {
            margin-top: 3px !important;
        }
        [data-testid="stDownloadButton"] button {
            min-height: 42px !important;
            height: 42px !important;
            font-size: 12px !important;
        }
        @media (max-width: 700px) {
            .st-key-login_card {
                max-width: 100% !important;
                padding: 18px 18px 22px !important;
            }
            .login-title {
                font-size: clamp(31px, 8vw, 39px) !important;
                gap: 9px !important;
            }
            .login-description {
                font-size: 12px !important;
                margin-bottom: 8px !important;
            }
        }
        /* Suporte integrado ao cartão, próximo ao manual e sem tipografia em negrito. */
        .login-support-divider {
            height: 1px !important;
            background: #E2EAF5 !important;
            margin: 10px 0 9px !important;
        }
        .st-key-login_card [data-testid="stExpander"] {
            margin: 0 !important;
            border: 1.5px solid #0875F5 !important;
            border-radius: 13px !important;
            background: linear-gradient(90deg, #F0F8FF, #EAF4FF) !important;
            overflow: hidden !important;
        }
        .st-key-login_card [data-testid="stExpander"] summary {
            min-height: 44px !important;
            padding: 8px 14px !important;
            color: #075BEA !important;
            font-family: 'Montserrat', sans-serif !important;
            font-size: 14px !important;
            font-weight: 500 !important;
        }
        .st-key-login_card [data-testid="stExpander"] summary p {
            font-weight: 500 !important;
        }
        .st-key-login_card [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
            padding: 12px 14px 14px !important;
            background: #FFFFFF !important;
        }
        /* Recuperação e manual em negrito, com pouco espaço entre eles. */
        .st-key-btn_esqueci_senha button {
            font-weight: 800 !important;
            margin-bottom: 0 !important;
        }
        .login-manual {
            margin-top: 2px !important;
        }
        [data-testid="stDownloadButton"] button {
            font-weight: 800 !important;
        }
        @media (max-width: 700px) {
            .st-key-login_card [data-testid="stExpander"] summary {
                min-height: 40px !important;
                font-size: 13px !important;
            }
            .login-support-divider {
                margin: 7px 0 !important;
            }
        }

        /* Acabamento compacto: reduzir espaços e destacar os três acessos. */
        .st-key-login_card [data-testid="stVerticalBlock"] {
            gap: 3px !important;
            row-gap: 3px !important;
        }
        .st-key-login_card [data-testid="stElementContainer"] {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }
        .st-key-btn_esqueci_senha {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }
        .st-key-btn_esqueci_senha button {
            font-weight: 800 !important;
            margin: 0 !important;
        }
        .login-manual {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        .st-key-login_card [data-testid="stDownloadButton"] {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }
        .st-key-login_card [data-testid="stDownloadButton"] button {
            font-weight: 800 !important;
            margin: 0 !important;
        }
        .login-support-divider {
            margin: 5px 0 5px !important;
        }
        .st-key-login_card [data-testid="stExpander"] {
            margin: 0 !important;
        }
        .st-key-login_card [data-testid="stExpander"] summary,
        .st-key-login_card [data-testid="stExpander"] summary p {
            font-weight: 800 !important;
        }
        .st-key-login_card [data-testid="stExpander"] summary {
            min-height: 40px !important;
            padding: 6px 12px !important;
        }
        .st-key-login_card [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
            padding: 9px 12px 11px !important;
        }

        /* Aproxima especificamente o Manual do botão "Esqueci minha senha".
           O recuo compensa o espaçamento automático entre elementos do Streamlit. */
        .st-key-login_card [data-testid="stElementContainer"]:has(.st-key-btn_esqueci_senha) {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }
        .st-key-login_card [data-testid="stElementContainer"]:has([data-testid="stDownloadButton"]) {
            margin-top: -20px !important;
            padding-top: 0 !important;
        }
        .st-key-login_card [data-testid="stDownloadButton"] {
            margin-top: 0 !important;
        }
        .st-key-login_card [data-testid="stDownloadButton"] button {
            margin-top: 0 !important;
        }

        /* Força o negrito no texto interno dos botões, inclusive elementos filhos do Streamlit. */
        .st-key-login_card .st-key-btn_esqueci_senha button,
        .st-key-login_card .st-key-btn_esqueci_senha button *,
        .st-key-login_card [data-testid="stDownloadButton"] button,
        .st-key-login_card [data-testid="stDownloadButton"] button * {
            font-weight: 800 !important;
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

        # Logo Loggi — fica acima do cartão branco.
        if logo_base64:
            st.markdown(
                f'<div class="login-logo"><img src="data:image/png;base64,{logo_base64}"></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="login-logo"><div class="login-logo-fallback">loggi</div></div>',
                unsafe_allow_html=True,
            )

        # O cartão envolve o título, a orientação, o login e o manual.
        with st.container(key="login_card"):
            st.markdown(
                '<div class="login-title"><span class="login-cube"><svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M24 4L43 14.5V34L24 44L5 34V14.5L24 4Z" stroke="#0786F7" stroke-width="2.8" stroke-linejoin="round"/><path d="M5.5 14.5L24 25L42.5 14.5M24 25V43.5M14.5 9.5L33.5 20" stroke="#0786F7" stroke-width="2.8" stroke-linejoin="round"/></svg></span>Portal Leves</div>',
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

            # Suporte integrado ao cartão, logo abaixo do manual.
            st.markdown('<div class="login-support-divider"></div>', unsafe_allow_html=True)
            with st.expander("🎧  Falar com o suporte"):
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
# Tela inicial — seleção visual dos módulos
# ---------------------------------------------------------------------------
def tela_modulos(user, opcoes):
    """Exibe os módulos em cards, seguindo a identidade visual Loggi."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
        html, body, [data-testid="stApp"], [data-testid="stApp"] * {
            font-family: 'Montserrat', sans-serif !important;
        }
        [data-testid="stAppViewContainer"] {
            background: #F7FAFF !important;
        }
        [data-testid="stHeader"], [data-testid="stToolbar"] {
            background: transparent !important;
        }
        [data-testid="stAppViewBlockContainer"] {
            max-width: 1320px !important;
            padding: 0 28px 48px !important;
        }
        .leves-home-hero {
            position: relative;
            margin: 0 -28px 0;
            padding: 26px 34px 100px;
            min-height: 180px;
            background: linear-gradient(112deg,#0759EF 0%,#0878F8 58%,#08A8EE 100%);
            color: #fff;
            overflow: hidden;
        }
        .leves-home-brand {
            display:flex; align-items:center; justify-content:space-between;
            max-width:1260px; margin:0 auto; gap:20px;
        }
        .leves-home-brand img { width:132px; height:auto; object-fit:contain; filter:brightness(0) invert(1); }
        .leves-home-user {
            color:#075BEA; background:#fff; border-radius:12px;
            padding:12px 18px; font-size:13px; font-weight:700;
        }
        .leves-home-panel {
            position:relative; z-index:2; max-width:1180px;
            margin:-62px auto 0; background:#fff;
            border:1px solid #DCE8F8; border-radius:28px;
            overflow:hidden; box-shadow:0 18px 48px rgba(20,61,120,.12);
        }
        .leves-home-panel-head {
            padding:27px 34px 25px;
            color:#fff; background:linear-gradient(105deg,#073B83 0%,#0759D9 55%,#087BFA 100%);
        }
        .leves-home-panel-head h1 {
            margin:0 0 7px; color:#fff; font-size:32px;
            line-height:1.2; font-weight:800; text-align:left;
        }
        .leves-home-panel-head p { margin:0; color:#EAF4FF; font-size:14px; font-weight:600; }
        .leves-home-grid {
            padding:28px; display:grid;
            grid-template-columns:repeat(4,minmax(0,1fr)); gap:16px;
        }
        .leves-home-card {
            min-height:190px; padding:21px 20px 18px;
            border:1px solid #DCE8F8; border-radius:22px;
            background:#fff; box-shadow:0 8px 22px rgba(20,61,120,.07);
        }
        .leves-home-card:hover { border-color:#83B9FF; }
        .leves-home-icon {
            width:48px;height:48px;display:flex;align-items:center;justify-content:center;
            border-radius:15px;background:#EAF4FF;color:#0875F5;
            border:1px solid #D2E6FF;font-size:24px;margin-bottom:15px;
        }
        .leves-home-card h3 {
            margin:0 0 9px;color:#06458F;font-size:15px;
            font-weight:800;line-height:1.25;
        }
        .leves-home-card p {
            margin:0;color:#64748B;font-size:12px;
            font-weight:600;line-height:1.5;
        }
        [data-testid="stVerticalBlock"] [data-testid="stButton"] button {
            border-radius:11px !important; min-height:42px !important;
            border:1px solid #D7E7FA !important; background:#F5F9FF !important;
            color:#075BEA !important; font-weight:800 !important;
        }
        [data-testid="stVerticalBlock"] [data-testid="stButton"] button:hover {
            background:#EAF4FF !important; border-color:#0875F5 !important;
        }
        @media(max-width:1000px) {
            .leves-home-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
        }
        @media(max-width:600px) {
            [data-testid="stAppViewBlockContainer"] { padding:0 12px 28px !important; }
            .leves-home-hero { margin:0 -12px; padding:20px 18px 86px; }
            .leves-home-brand img { width:105px; }
            .leves-home-user { font-size:10px; padding:9px 11px; }
            .leves-home-panel { margin:-54px auto 0; border-radius:20px; }
            .leves-home-panel-head { padding:22px 20px; }
            .leves-home-panel-head h1 { font-size:25px; }
            .leves-home-grid { padding:16px; grid-template-columns:1fr; gap:12px; }
            .leves-home-card { min-height:155px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    base = os.path.dirname(os.path.abspath(__file__))
    caminho_logo = os.path.join(base, LOGO_LOGIN_PATH)
    logo_base64 = get_base64_image(caminho_logo) if os.path.exists(caminho_logo) else ""
    logo_html = (
        f'<img src="data:image/png;base64,{logo_base64}" alt="Loggi">'
        if logo_base64 else '<div style="color:white;font-size:30px;font-weight:800">Loggi</div>'
    )
    st.markdown(
        f"""
        <div class="leves-home-hero">
          <div class="leves-home-brand">
            {logo_html}
            <div class="leves-home-user">Olá, {user.get('nome','usuário')} · {user.get('email','')}</div>
          </div>
        </div>
        <div class="leves-home-panel">
          <div class="leves-home-panel-head">
            <h1>Portal LEVES</h1>
            <p>Escolha o módulo que deseja acessar.</p>
          </div>
          <div class="leves-home-grid">
        """,
        unsafe_allow_html=True,
    )

    descricoes = {
        "Envios": ("📦", "Consulte e acompanhe os envios de insumos para as operações."),
        "Recebimento": ("📥", "Registre e acompanhe os recebimentos de materiais."),
        "Conciliação": ("🧾", "Confira movimentações, saldos e possíveis divergências."),
        "Cobranças": ("💰", "Consulte valores e acompanhe as cobranças."),
        "Devoluções": ("↩️", "Registre devoluções e acompanhe os saldos a devolver."),
        "Pendências": ("🔔", "Acompanhe itens e tratativas que precisam de atenção."),
        "Usuários": ("👥", "Gerencie os usuários e seus acessos ao portal."),
        "Relatórios": ("📊", "Acesse os indicadores e relatórios do portal."),
        "Configurações": ("⚙️", "Consulte e ajuste as configurações disponíveis."),
    }
    cols = st.columns(4)
    for i, opcao in enumerate(opcoes):
        nome = opcao.split(" ", 1)[-1]
        icone, descricao = descricoes.get(nome, ("📁", "Acesse este módulo do portal."))
        with cols[i % 4]:
            st.markdown(
                f"""
                <div class="leves-home-card">
                  <div class="leves-home-icon">{icone}</div>
                  <h3>{nome.upper()}</h3>
                  <p>{descricao}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Acessar módulo →", key=f"home_mod_{i}", width="stretch"):
                st.session_state["pagina_ativa"] = opcao
                st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)
    a, b, c = st.columns([1, 1, 1])
    with a:
        if st.button("↻ Atualizar dados", width="stretch", key="home_refresh"):
            import data_extraction
            data_extraction.limpar_cache()
            st.rerun()
    with b:
        if st.button("📘 Manual de devolução", width="stretch", key="home_manual"):
            manual.botao_manual(key="manual_home")
    with c:
        if st.button("Sair", width="stretch", key="home_logout"):
            logout()
            st.session_state.pop("pagina_ativa", None)
            st.rerun()



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

    if scan_id and (eh_admin or eh_receb):
        pagina = "📥 Recebimento"
        st.session_state["pagina_ativa"] = pagina
    else:
        if eh_receb:
            opcoes = ["📥 Recebimento"]
        elif eh_admin:
            opcoes = [
                "📦 Envios", "📥 Recebimento", "🧾 Conciliação", "💰 Cobranças",
                "↩️ Devoluções", "🔔 Pendências", "👥 Usuários",
                "📊 Relatórios", "⚙️ Configurações",
            ]
        elif perfil == "gdl":
            opcoes = ["📦 Envios", "🧾 Conciliação", "↩️ Devoluções", "👥 Usuários"]
        else:
            opcoes = ["📦 Envios", "↩️ Devoluções", "💰 Cobranças"]

        pagina = st.session_state.get("pagina_ativa")
        if pagina not in opcoes:
            st.session_state.pop("pagina_ativa", None)
            tela_modulos(user, opcoes)
            return

    topo_voltar, topo_usuario = st.columns([1, 5])
    with topo_voltar:
        if st.button("← Módulos", key="voltar_modulos"):
            st.session_state.pop("pagina_ativa", None)
            st.rerun()
    with topo_usuario:
        st.markdown(
            f"<div style='text-align:right;color:#64748B;font-size:13px;font-weight:700;padding-top:10px'>{user.get('nome','')} · {pagina}</div>",
            unsafe_allow_html=True,
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
