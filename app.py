"""
app.py — Portal LEVES (Loggi) — camada de apresentação (padrão DLE).
Configura a página, aplica o estilo, trata o login próprio (multi-tenant) e
roteia entre as páginas via st.sidebar.radio.

Fluxo: data_extraction -> data_processing -> page_N() -> app.main()
Executar: streamlit run app.py
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

st.set_page_config(
    page_title="Portal LEVES — Loggi",
    page_icon="📦",
    layout="wide",
)

from page_1 import page_1  # noqa: E402
from page_2 import page_2  # noqa: E402
from page_3 import page_3  # noqa: E402
from page_4 import page_4  # noqa: E402
from page_5 import page_5  # noqa: E402
from page_6 import page_6  # noqa: E402
from page_7 import page_7  # noqa: E402
from page_8 import page_8  # noqa: E402
from page_9 import page_9  # noqa: E402


# ---------------------------------------------------------------------------
# Sessão / login
# ---------------------------------------------------------------------------

def _init_state():
    st.session_state.setdefault("usuario", None)
    st.session_state.setdefault("tentativas", 0)


def logout():
    st.session_state["usuario"] = None
    st.session_state["tentativas"] = 0


def tela_login():
    # CSS exclusivo da tela de login.
    # O restante do portal continua usando o PageStyler normalmente.
    st.markdown(
        """
        <style>
        /* ============================================================
           LOGIN — PORTAL LEVES
           ============================================================ */

        [data-testid="stAppViewContainer"] {
            background: #f7f9fc;
        }

        [data-testid="stAppViewBlockContainer"] {
            max-width: 1180px !important;
            padding: 2.5rem 30px 2rem 30px !important;
        }

        [data-testid="stToolbar"] {
            display: none !important;
        }

        /* Colunas principais */
        .login-left {
            min-height: 650px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 35px 45px 35px 20px;
        }

        .login-left-badge {
            display: inline-block;
            width: fit-content;
            padding: 7px 13px;
            border-radius: 999px;
            background: #e8f3ff;
            color: #0067fc;
            font-family: Montserrat, sans-serif;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: .5px;
            margin-bottom: 20px;
        }

        .login-left-title {
            color: #172033;
            font-family: Montserrat, sans-serif;
            font-size: 42px;
            line-height: 1.08;
            font-weight: 800;
            letter-spacing: -1.5px;
            margin: 0 0 18px 0;
            max-width: 500px;
        }

        .login-left-title span {
            color: #0067fc;
        }

        .login-left-text {
            color: #667085;
            font-family: Montserrat, sans-serif;
            font-size: 16px;
            line-height: 1.65;
            max-width: 500px;
            margin-bottom: 30px;
        }

        .login-feature {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 11px 0;
            color: #344054;
            font-family: Montserrat, sans-serif;
            font-size: 14px;
            font-weight: 600;
        }

        .login-feature-icon {
            width: 34px;
            height: 34px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #ffffff;
            border: 1px solid #e4e7ec;
            box-shadow: 0 4px 12px rgba(16, 24, 40, .05);
            font-size: 17px;
        }

        .login-visual {
            position: relative;
            margin-top: 35px;
            width: 390px;
            max-width: 90%;
            height: 120px;
        }

        .login-visual-box {
            position: absolute;
            border-radius: 18px;
            border: 1px solid #dce8f8;
            background: linear-gradient(135deg, #ffffff, #eef6ff);
            box-shadow: 0 14px 35px rgba(16, 24, 40, .07);
        }

        .login-visual-box.one {
            width: 210px;
            height: 82px;
            left: 0;
            top: 28px;
            transform: rotate(-4deg);
        }

        .login-visual-box.two {
            width: 210px;
            height: 82px;
            left: 120px;
            top: 4px;
            transform: rotate(4deg);
        }

        .login-visual-label {
            position: absolute;
            left: 55px;
            top: 48px;
            color: #0067fc;
            font-family: Montserrat, sans-serif;
            font-size: 14px;
            font-weight: 800;
            letter-spacing: .8px;
        }

        /* Lado direito */
        .login-right {
            min-height: 650px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 25px 20px 25px 30px;
        }

        .login-card-wrap {
            max-width: 440px;
            width: 100%;
            margin: 0 auto;
        }

        .login-logo {
            text-align: center;
            margin: 0 auto 6px auto;
        }

        .login-logo img {
            display: block;
            width: 150px;
            max-width: 70%;
            height: auto;
            margin: 0 auto;
        }

        .login-title {
            text-align: center;
            color: #0067fc;
            font-family: Montserrat, sans-serif;
            font-size: 23px;
            font-weight: 800;
            letter-spacing: 2px;
            line-height: 1.2;
            margin: 4px 0 8px 0;
            text-transform: uppercase;
        }

        .login-description {
            text-align: center;
            color: #667085;
            font-family: Montserrat, sans-serif;
            font-size: 13px;
            line-height: 1.5;
            max-width: 350px;
            margin: 0 auto 20px auto;
        }

        [data-testid="stForm"] {
            background: #ffffff !important;
            border: 1px solid #e1e5eb !important;
            border-radius: 16px !important;
            padding: 24px 25px 21px 25px !important;
            box-shadow: 0 14px 35px rgba(15, 23, 42, .07) !important;
        }

        [data-testid="stForm"] label {
            color: #344054 !important;
            font-family: Montserrat, sans-serif !important;
            font-size: 13px !important;
            font-weight: 600 !important;
        }

        [data-testid="stForm"] input {
            border-radius: 10px !important;
            border: 1px solid #d8dee8 !important;
            min-height: 44px !important;
            font-family: Montserrat, sans-serif !important;
            background: #ffffff !important;
        }

        [data-testid="stForm"] input:focus {
            border-color: #0067fc !important;
            box-shadow: 0 0 0 2px rgba(0, 103, 252, .10) !important;
        }

        [data-testid="stForm"] [data-testid="stTextInput"] {
            margin-bottom: 5px !important;
        }

        [data-testid="stFormSubmitButton"] button {
            width: 100% !important;
            min-height: 46px !important;
            margin-top: 8px !important;
            border-radius: 10px !important;
            border: 0 !important;
            background: #0067fc !important;
            color: #ffffff !important;
            font-family: Montserrat, sans-serif !important;
            font-size: 15px !important;
            font-weight: 700 !important;
            transition: all .2s ease !important;
        }

        [data-testid="stFormSubmitButton"] button:hover {
            background: #0056d6 !important;
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(0, 103, 252, .20) !important;
        }

        [data-testid="stAlert"] {
            border-radius: 10px !important;
            font-family: Montserrat, sans-serif !important;
            font-size: 13px !important;
        }

        .login-manual {
            margin-top: 13px;
        }

        [data-testid="stDownloadButton"] button {
            border: 1px solid #e1e5eb !important;
            border-radius: 11px !important;
            background: #ffffff !important;
            color: #344054 !important;
            min-height: 44px !important;
            font-family: Montserrat, sans-serif !important;
            font-weight: 600 !important;
            width: 100% !important;
        }

        [data-testid="stDownloadButton"] button:hover {
            border-color: #0067fc !important;
            color: #0067fc !important;
        }

        .login-help-title {
            text-align: center;
            color: #98a2b3;
            font-family: Montserrat, sans-serif;
            font-size: 12px;
            margin: 15px 0 7px 0;
        }

        [data-testid="stExpander"] {
            border: 1px solid #e1e5eb !important;
            border-radius: 11px !important;
            background: #ffffff !important;
            overflow: hidden !important;
        }

        [data-testid="stExpander"] summary {
            font-family: Montserrat, sans-serif !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            color: #344054 !important;
        }

        .login-footer {
            text-align: center;
            color: #a1a8b3;
            font-family: Montserrat, sans-serif;
            font-size: 11px;
            margin-top: 16px;
        }

        /* Responsivo */
        @media (max-width: 850px) {
            .login-left {
                display: none !important;
            }

            .login-right {
                min-height: auto;
                padding: 30px 10px;
            }

            [data-testid="stAppViewBlockContainer"] {
                max-width: 560px !important;
                padding: 1.5rem 16px 2rem 16px !important;
            }
        }

        @media (max-width: 600px) {
            .login-right {
                padding: 15px 0;
            }

            [data-testid="stForm"] {
                padding: 22px 18px 20px 18px !important;
            }

            .login-title {
                font-size: 21px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ================================================================
    # LAYOUT: ESQUERDA + DIREITA
    # ================================================================
    col_left, col_right = st.columns([1.15, 0.85], gap="large")

    with col_left:
        st.markdown(
            """
            <div class="login-left">
                <div class="login-left-badge">📦 PORTAL LEVES</div>

                <h1 class="login-left-title">
                    Gestão de <span>insumos</span><br>
                    mais simples.
                </h1>

                <div class="login-left-text">
                    Consulte, acompanhe e gerencie os insumos enviados
                    para sua operação em um único lugar.
                </div>

                <div class="login-feature">
                    <div class="login-feature-icon">📦</div>
                    Controle de insumos
                </div>

                <div class="login-feature">
                    <div class="login-feature-icon">↩️</div>
                    Acompanhamento de devoluções
                </div>

                <div class="login-feature">
                    <div class="login-feature-icon">📊</div>
                    Informações da operação
                </div>

                <div class="login-visual">
                    <div class="login-visual-box one"></div>
                    <div class="login-visual-box two"></div>
                    <div class="login-visual-label">LOGGI · LEVES</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        st.markdown('<div class="login-right"><div class="login-card-wrap">', unsafe_allow_html=True)

        base = os.path.dirname(os.path.abspath(__file__))
        caminho_logo = os.path.join(base, LOGO_LOGIN_PATH)
        logo_base64 = (
            get_base64_image(caminho_logo)
            if os.path.exists(caminho_logo)
            else ""
        )

        if logo_base64:
            st.markdown(
                f"""
                <div class="login-logo">
                    <img src="data:image/png;base64,{logo_base64}">
                </div>
                <div class="login-title">Portal LEVES</div>
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
                Acesse sua conta para consultar os insumos
                da sua operação.
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state["tentativas"] >= 5:
            st.error("Muitas tentativas. Recarregue a página e tente novamente.")

        # Login — lógica de autenticação preservada.
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
            try:
                u = auth.autenticar(usuario, senha)
            except Exception as e:  # noqa: BLE001
                st.error(f"Erro ao acessar a planilha: {e}")
                return

            if u:
                st.session_state["usuario"] = u
                st.session_state["tentativas"] = 0
                st.rerun()
            else:
                st.session_state["tentativas"] += 1
                st.error("Usuário ou senha inválidos.")

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

        st.markdown("</div></div>", unsafe_allow_html=True)


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
        papel = {
            "admin": "Administrador",
            "recebimento": "Recebimento",
        }.get(
            perfil,
            f"Destino: {user['destino']}",
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
                "🔔 Pendências",
                "👥 Usuários",
                "📊 Relatórios",
                "⚙️ Configurações",
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
            page_9()
        else:
            page_1()
    except Exception as e:  # noqa: BLE001
        st.error(
            "Erro ao acessar a planilha: "
            f"{e}. Verifique a chave da service account (veja o README)."
        )


if __name__ == "__main__":
    main()
