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

# ---------------------------------------------------------------------------
# Sessão / login
# ---------------------------------------------------------------------------
def _init_state():
    st.session_state.setdefault("usuario", None)
    st.session_state.setdefault("tentativas", 0)
    st.session_state.setdefault("recuperacao", False)


def logout():
    st.session_state["usuario"] = None
    st.session_state["tentativas"] = 0
    st.session_state["recuperacao"] = False



def tela_primeiro_acesso():
    """Tela obrigatória para criação da senha definitiva no primeiro acesso."""
    user = st.session_state.get("usuario")

    if not user:
        return

    st.markdown(
        """
        <style>
        .first-access-title {
            text-align: center;
            color: #172033;
            font-family: Montserrat, sans-serif;
            font-size: 24px;
            font-weight: 800;
            margin: 8px 0 8px 0;
        }

        .first-access-description {
            text-align: center;
            color: #788292;
            font-family: Montserrat, sans-serif;
            font-size: 13px;
            line-height: 1.5;
            max-width: 390px;
            margin: 0 auto 20px auto;
        }

        .first-access-info {
            background: #eef6ff;
            border: 1px solid #dcecff;
            border-radius: 12px;
            padding: 13px 15px;
            color: #566172;
            font-family: Montserrat, sans-serif;
            font-size: 12px;
            line-height: 1.55;
            margin-bottom: 18px;
        }

        .first-access-user {
            text-align: center;
            color: #0067fc;
            font-family: Montserrat, sans-serif;
            font-size: 12px;
            font-weight: 700;
            margin-bottom: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns(
        [1.05, 0.95],
        gap="large",
        vertical_alignment="center",
    )

    with col_left:
        st.markdown(
            '<div class="login-panel">'
            '<div class="login-panel-badge">📦 PORTAL LEVES</div>'
            '<div class="login-panel-title">Primeiro <span>acesso</span></div>'
            '<div class="login-panel-text">'
            'Para proteger sua conta, crie uma senha pessoal antes de acessar o portal.'
            '</div>'
            '<div class="login-feature"><div class="login-feature-icon">🔐</div>'
            '<div>Senha pessoal e exclusiva</div></div>'
            '<div class="login-feature"><div class="login-feature-icon">🛡️</div>'
            '<div>Mais segurança para sua conta</div></div>'
            '<div class="login-feature"><div class="login-feature-icon">📦</div>'
            '<div>Acesso aos seus insumos</div></div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with col_right:
        st.markdown('<div class="login-right">', unsafe_allow_html=True)

        base = os.path.dirname(os.path.abspath(__file__))
        caminho_logo = os.path.join(base, LOGO_LOGIN_PATH)

        logo_base64 = (
            get_base64_image(caminho_logo)
            if os.path.exists(caminho_logo)
            else ""
        )

        if logo_base64:
            st.markdown(
                f'<div class="login-floating-logo">'
                f'<img src="data:image/png;base64,{logo_base64}">'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="login-floating-logo">'
                '<div style="color:#0067fc;font-size:32px;font-weight:800;'
                'font-family:Montserrat,sans-serif;">loggi</div>'
                '</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div class="login-title">Portal LEVES</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="first-access-title">Crie sua nova senha</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="first-access-description">'
            'A senha temporária usada no primeiro acesso deixará de funcionar '
            'depois que você cadastrar sua nova senha.'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="first-access-user">'
            f'Usuário: {user.get("usuario", "")}'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="first-access-info">'
            '<strong>Requisitos:</strong><br>'
            '• Mínimo de 6 caracteres<br>'
            '• A confirmação precisa ser igual à nova senha'
            '</div>',
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
                placeholder="Digite novamente sua nova senha",
            )

            salvar = st.form_submit_button(
                "Criar nova senha",
                type="primary",
                width="stretch",
            )

        if salvar:
            if not nova_senha:
                st.error("Digite uma nova senha.")
                return

            if len(nova_senha) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres.")
                return

            if nova_senha != confirmar_senha:
                st.error("As senhas não são iguais.")
                return

            try:
                ok, mensagem = auth.alterar_senha(
                    user["usuario"],
                    nova_senha,
                )
            except Exception as e:  # noqa: BLE001
                st.error(f"Erro ao alterar a senha: {e}")
                return

            if ok:
                novo_usuario = auth.buscar_usuario(user["usuario"])

                if not novo_usuario:
                    st.error(
                        "A senha foi alterada, mas não foi possível "
                        "atualizar sua sessão. Faça o login novamente."
                    )
                    logout()
                    return

                st.session_state["usuario"] = novo_usuario
                st.session_state["tentativas"] = 0

                st.success(
                    "Senha criada com sucesso! Seu acesso foi liberado."
                )
                st.rerun()
            else:
                st.error(mensagem)

        st.markdown(
            '<div class="login-footer">Portal LEVES · Loggi</div>',
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)


def tela_recuperacao_senha():
    """Fluxo de recuperação de senha por código enviado ao e-mail cadastrado."""
    st.markdown(
        """
        <style>
        .recovery-title {
            text-align: center;
            color: #172033;
            font-family: Montserrat, sans-serif;
            font-size: 24px;
            font-weight: 800;
            margin: 8px 0 8px 0;
        }
        .recovery-description {
            text-align: center;
            color: #788292;
            font-family: Montserrat, sans-serif;
            font-size: 13px;
            line-height: 1.5;
            max-width: 390px;
            margin: 0 auto 20px auto;
        }
        .recovery-info {
            background: #eef6ff;
            border: 1px solid #dcecff;
            border-radius: 12px;
            padding: 13px 15px;
            color: #566172;
            font-family: Montserrat, sans-serif;
            font-size: 12px;
            line-height: 1.55;
            margin-bottom: 18px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns(
        [1.05, 0.95],
        gap="large",
        vertical_alignment="center",
    )

    with col_left:
        st.markdown(
            '<div class="login-panel">'
            '<div class="login-panel-badge">📦 PORTAL LEVES</div>'
            '<div class="login-panel-title">Recuperar <span>senha</span></div>'
            '<div class="login-panel-text">'
            'Recupere o acesso à sua conta usando o e-mail cadastrado no portal.'
            '</div>'
            '<div class="login-feature"><div class="login-feature-icon">📧</div>'
            '<div>Código enviado por e-mail</div></div>'
            '<div class="login-feature"><div class="login-feature-icon">⏱️</div>'
            '<div>Código válido por 15 minutos</div></div>'
            '<div class="login-feature"><div class="login-feature-icon">🔐</div>'
            '<div>Crie uma nova senha pessoal</div></div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with col_right:
        st.markdown('<div class="login-right">', unsafe_allow_html=True)

        base = os.path.dirname(os.path.abspath(__file__))
        caminho_logo = os.path.join(base, LOGO_LOGIN_PATH)
        logo_base64 = (
            get_base64_image(caminho_logo)
            if os.path.exists(caminho_logo)
            else ""
        )
        if logo_base64:
            st.markdown(
                f'<div class="login-floating-logo"><img src="data:image/png;base64,{logo_base64}"></div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="recovery-title">Esqueci minha senha</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="recovery-description">Informe seu usuário para receber um código de recuperação no e-mail cadastrado.</div>',
            unsafe_allow_html=True,
        )

        etapa = st.session_state.get("recuperacao_etapa", "solicitar")
        usuario_rec = st.session_state.get("recuperacao_usuario", "")

        if etapa == "solicitar":
            with st.form("recuperar_senha_form"):
                usuario = st.text_input("Usuário", placeholder="Digite seu usuário")
                enviar = st.form_submit_button(
                    "Enviar código por e-mail",
                    type="primary",
                    width="stretch",
                )

            if enviar:
                usuario = (usuario or "").strip().lower()
                if not usuario:
                    st.error("Informe seu usuário.")
                else:
                    try:
                        _, mensagem = auth.solicitar_recuperacao(usuario)
                        st.session_state["recuperacao_usuario"] = usuario
                        st.session_state["recuperacao_etapa"] = "codigo"
                        st.success(mensagem)
                        st.rerun()
                    except Exception as e:  # noqa: BLE001
                        st.error(f"Não foi possível enviar o código de recuperação: {e}")

        else:
            st.markdown(
                '<div class="recovery-info">'
                'Digite o código de 6 dígitos enviado para o e-mail cadastrado e escolha sua nova senha.'
                '</div>',
                unsafe_allow_html=True,
            )

            with st.form("redefinir_senha_form"):
                codigo = st.text_input("Código de recuperação", max_chars=6, placeholder="000000")
                nova_senha = st.text_input("Nova senha", type="password", placeholder="Mínimo de 6 caracteres")
                confirmar = st.text_input("Confirmar nova senha", type="password", placeholder="Repita a nova senha")
                redefinir = st.form_submit_button(
                    "Redefinir senha",
                    type="primary",
                    width="stretch",
                )

            if redefinir:
                if nova_senha != confirmar:
                    st.error("As senhas não coincidem.")
                else:
                    try:
                        ok, mensagem = auth.redefinir_senha_com_codigo(
                            usuario_rec,
                            codigo,
                            nova_senha,
                        )
                        if ok:
                            st.success(mensagem)
                            st.session_state["recuperacao"] = False
                            st.session_state["recuperacao_etapa"] = "solicitar"
                            st.session_state["recuperacao_usuario"] = ""
                            st.session_state["tentativas"] = 0
                            st.session_state["mensagem_login"] = "Senha redefinida com sucesso. Faça login com sua nova senha."
                            st.rerun()
                        else:
                            st.error(mensagem)
                    except Exception as e:  # noqa: BLE001
                        st.error(f"Não foi possível redefinir a senha: {e}")

            if st.button("← Voltar para o login", width="stretch"):
                st.session_state["recuperacao"] = False
                st.session_state["recuperacao_etapa"] = "solicitar"
                st.session_state["recuperacao_usuario"] = ""
                st.rerun()

        st.markdown('<div class="login-footer">Portal LEVES · Loggi</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

def tela_login():
    if st.session_state.get("recuperacao", False):
        tela_recuperacao_senha()
        return

    # -----------------------------------------------------------------------
    # CSS exclusivo da tela de login.
    # O restante do portal continua usando o PageStyler normalmente.
    # -----------------------------------------------------------------------
    st.markdown(
        """
<style>
/* ============================================================
   PORTAL LEVES — LOGIN
   ============================================================ */

/* ============================================================
   FUNDO + TOPO DO STREAMLIT
   ============================================================ */

html,
body,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
section.main {
    background: #f7f9fc !important;
}

header[data-testid="stHeader"],
[data-testid="stHeader"] {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    visibility: hidden !important;
}

[data-testid="stDecoration"] {
    display: none !important;
    height: 0 !important;
}

#MainMenu,
footer {
    display: none !important;
    visibility: hidden !important;
}

[data-testid="stAppViewContainer"] {
    background: #f7f9fc !important;
    top: 0 !important;
    margin-top: 0 !important;
}

section.main {
    background: #f7f9fc !important;
    margin-top: 0 !important;
    padding-top: 0 !important;
}

section.main > div {
    padding-top: 0 !important;
}

[data-testid="stAppViewBlockContainer"],
[data-testid="stMainBlockContainer"] {
    max-width: 1220px !important;
    padding-top: 8px !important;
    padding-bottom: 20px !important;
}

[data-testid="stToolbar"] {
    display: none !important;
}

/* Não limitar a coluna que contém o formulário */
.login-layout {
    width: 100%;
}

/* O vertical_alignment="center" do st.columns faz o alinhamento principal.
   Esta regra só garante que o conteúdo do lado direito não herde altura extra. */
div[data-testid="column"]:nth-child(2) > div {
    min-height: auto !important;
}

/* ============================================================
   PAINEL ESQUERDO
   ============================================================ */

.login-panel {
    box-sizing: border-box;
    width: 100%;
    min-height: 480px;
    padding: 38px 46px;
    border-radius: 30px;
    background: #eef6ff;
    display: flex;
    flex-direction: column;
    justify-content: center;
    font-family: Montserrat, sans-serif;
}

.login-panel-badge {
    color: #0067fc;
    font-size: 14px;
    font-weight: 800;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 20px;
}

.login-panel-title {
    color: #172033;
    font-size: 43px;
    line-height: 1.08;
    font-weight: 800;
    letter-spacing: -1.7px;
    margin: 0 0 20px 0;
    max-width: 540px;
}

.login-panel-title span {
    color: #0067fc;
}

.login-panel-text {
    color: #5d6675;
    font-size: 16px;
    line-height: 1.65;
    max-width: 610px;
    margin-bottom: 28px;
}

.login-feature {
    display: flex;
    align-items: center;
    gap: 12px;
    color: #303847;
    font-size: 15px;
    font-weight: 600;
    margin: 9px 0;
}

.login-feature-icon {
    width: 34px;
    height: 34px;
    border-radius: 10px;
    background: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 17px;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
}

.login-panel-bottom {
    color: #8993a2;
    font-size: 13px;
    line-height: 1.55;
    margin-top: 30px;
}

/* Ilustração discreta, para aproximar do mockup */
.login-visual {
    position: relative;
    height: 105px;
    margin-top: 32px;
    max-width: 460px;
}

.login-box {
    position: absolute;
    bottom: 0;
    width: 105px;
    height: 72px;
    border-radius: 9px;
    background: #ffffff;
    border: 1px solid #dce8f5;
    box-shadow: 0 12px 22px rgba(0, 75, 150, 0.08);
}

.login-box:before {
    content: "";
    position: absolute;
    left: 17px;
    right: 17px;
    top: 16px;
    height: 7px;
    border-radius: 10px;
    background: #dcecff;
}

.login-box:after {
    content: "";
    position: absolute;
    left: 17px;
    width: 48px;
    top: 31px;
    height: 7px;
    border-radius: 10px;
    background: #eef4fb;
}

.login-box.one {
    left: 0;
    transform: rotate(-4deg);
}

.login-box.two {
    left: 85px;
    bottom: 8px;
    transform: rotate(4deg);
}

.login-visual-label {
    position: absolute;
    left: 245px;
    bottom: 23px;
    color: #9aa5b5;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.2px;
}

/* ============================================================
   ÁREA DIREITA
   ============================================================ */

.login-right {
    width: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    font-family: Montserrat, sans-serif;
}

.login-brand-block {
    width: 100%;
    text-align: center;
    margin: 10px auto 5px auto;
}

.login-floating-logo {
    position: fixed;
    top: 28px !important;
    right: 38px !important;
    z-index: 1000;
    width: 128px;
    text-align: center;
}

.login-floating-logo img {
    display: block;
    width: 128px;
    max-width: 100%;
    height: auto;
    margin: 0;
}

.login-logo {
    margin-bottom: 7px;
}

.login-brand-block .login-title {
    margin-top: 0;
    margin-bottom: 8px;
}

.login-logo {
    text-align: center;
    margin: 0 auto 5px auto;
}

.login-logo img {
    display: block;
    width: 128px;
    max-width: 70%;
    height: auto;
    margin: 0 auto;
}

.login-title {
    text-align: center;
    color: #0067fc;
    font-family: Montserrat, sans-serif;
    font-size: 22px;
    font-weight: 800;
    letter-spacing: 1.8px;
    line-height: 1.2;
    margin: 3px 0 6px 0;
    text-transform: uppercase;
}

.login-description {
    text-align: center;
    color: #788292;
    font-family: Montserrat, sans-serif;
    font-size: 13px;
    line-height: 1.45;
    max-width: 370px;
    margin: 6px auto 22px auto;
}

/* Card do login */
[data-testid="stForm"] {
    background: #ffffff !important;
    border: 1px solid #e0e5ec !important;
    border-radius: 18px !important;
    padding: 28px 28px 24px 28px !important;
    box-shadow: 0 14px 38px rgba(15, 23, 42, 0.08) !important;
}

[data-testid="stForm"] label {
    color: #3d4654 !important;
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
    box-shadow: 0 0 0 2px rgba(0, 103, 252, 0.10) !important;
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
}

[data-testid="stFormSubmitButton"] button:hover {
    background: #0056d6 !important;
    box-shadow: 0 7px 18px rgba(0, 103, 252, 0.20) !important;
}

[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-family: Montserrat, sans-serif !important;
    font-size: 13px !important;
}

/* Manual */
.login-manual {
    margin-top: 12px;
}

[data-testid="stDownloadButton"] button {
    border: 1px solid #e0e5ec !important;
    border-radius: 12px !important;
    background: #ffffff !important;
    color: #566172 !important;
    min-height: 47px !important;
    font-family: Montserrat, sans-serif !important;
    font-weight: 600 !important;
    width: 100% !important;
}

[data-testid="stDownloadButton"] button:hover {
    border-color: #0067fc !important;
    color: #0067fc !important;
}

/* Suporte */
.login-help-title {
    text-align: center;
    color: #a0a8b5;
    font-family: Montserrat, sans-serif;
    font-size: 12px;
    margin: 16px 0 7px 0;
}

[data-testid="stExpander"] {
    border: 1px solid #e0e5ec !important;
    border-radius: 12px !important;
    background: #ffffff !important;
    overflow: hidden !important;
}

[data-testid="stExpander"] summary {
    font-family: Montserrat, sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #566172 !important;
}

.login-footer {
    text-align: center;
    color: #a5adba;
    font-family: Montserrat, sans-serif;
    font-size: 11px;
    margin-top: 16px;
}

/* ============================================================
   RESPONSIVO
   ============================================================ */

@media (max-width: 900px) {
    [data-testid="stAppViewBlockContainer"] {
        padding: 4px 18px 16px 18px !important;
    }

    .login-panel {
        min-height: 500px;
        padding: 40px;
    }

    .login-panel-title {
        font-size: 36px;
    }


}

@media (max-width: 700px) {
    .login-panel {
        display: none;
    }

    .login-right {
        min-height: auto;
        padding: 20px 0;
    }

    [data-testid="stForm"] {
        padding: 22px 18px 20px 18px !important;
    }
}
</style>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------------------------
    # Layout: painel de apresentação + login
    # -----------------------------------------------------------------------
    col_left, col_right = st.columns(
        [1.05, 0.95],
        gap="large",
        vertical_alignment="center",
    )

    # =======================================================================
    # ESQUERDA
    # =======================================================================
    with col_left:
        st.markdown(
            '<div class="login-panel">'
            '<div class="login-panel-badge">📦 PORTAL LEVES</div>'
            '<div class="login-panel-title">Gestão de <span>Insumos</span></div>'
            '<div class="login-panel-text">Consulte, acompanhe e gerencie os insumos enviados para sua operação em um único lugar.</div>'
            '<div class="login-feature"><div class="login-feature-icon">📦</div><div>Controle de insumos</div></div>'
            '<div class="login-feature"><div class="login-feature-icon">↩️</div><div>Acompanhamento de devoluções</div></div>'
            '<div class="login-feature"><div class="login-feature-icon">📊</div><div>Informações de valores</div></div>'
            '<div class="login-panel-bottom">Tenha as informações de forma rápida, organizada e centralizada.</div>'
            '<div class="login-visual">'
            '<div class="login-box one"></div>'
            '<div class="login-box two"></div>'
            '<div class="login-visual-label">LOGGI · LEVES</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # =======================================================================
    # DIREITA — login original preservado
    # =======================================================================
    with col_right:
        st.markdown('<div class="login-right">', unsafe_allow_html=True)

        base = os.path.dirname(os.path.abspath(__file__))
        caminho_logo = os.path.join(base, LOGO_LOGIN_PATH)

        logo_base64 = (
            get_base64_image(caminho_logo)
            if os.path.exists(caminho_logo)
            else ""
        )

        # Logo institucional fixado no canto superior direito.
        # O título Portal LEVES permanece centralizado sobre o login.
        if logo_base64:
            st.markdown(
                f'<div class="login-floating-logo">'
                f'<img src="data:image/png;base64,{logo_base64}">'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="login-floating-logo">'
                '<div style="color:#0067fc;font-size:32px;font-weight:800;'
                'font-family:Montserrat,sans-serif;">loggi</div>'
                '</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div class="login-title">Portal LEVES</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="login-description">'
            "Acesse sua conta para consultar os insumos da sua operação."
            "</div>",
            unsafe_allow_html=True,
        )

        if st.session_state["tentativas"] >= 5:
            st.error(
                "Muitas tentativas. Recarregue a página e tente novamente."
            )

        # Login — autenticação original preservada.
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

        mensagem_login = st.session_state.pop("mensagem_login", None)
        if mensagem_login:
            st.success(mensagem_login)

        if st.button("Esqueci minha senha", width="stretch"):
            st.session_state["recuperacao"] = True
            st.session_state["recuperacao_etapa"] = "solicitar"
            st.session_state["recuperacao_usuario"] = ""
            st.rerun()

        if manual.disponivel():
            st.markdown(
                '<div class="login-manual">',
                unsafe_allow_html=True,
            )
            manual.botao_manual(key="manual_login")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            '<div class="login-help-title">Precisa de ajuda?</div>',
            unsafe_allow_html=True,
        )

        with st.expander("💬 Falar com o suporte"):
            contato.form_contato(key="login")

        st.markdown(
            '<div class="login-footer">Portal LEVES · Loggi</div>',
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)


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

    # Primeiro acesso: o usuário deve criar sua senha pessoal
    # antes de acessar qualquer funcionalidade do portal.
    if user.get("primeiro_acesso", False):
        tela_primeiro_acesso()
        return

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
