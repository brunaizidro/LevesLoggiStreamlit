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


def logout():
    st.session_state["usuario"] = None
    st.session_state["tentativas"] = 0


def tela_login():
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

/* Ilustração: pacote Loggi */
.login-visual {
    position: relative;
    height: 115px;
    margin-top: 30px;
    max-width: 460px;
}

.login-package {
    position: absolute;
    left: 8px;
    bottom: 2px;
    width: 145px;
    height: 88px;
    border-radius: 10px;
    background: linear-gradient(135deg, #d8a66d 0%, #c98e50 100%);
    border: 1px solid #bd8147;
    box-shadow: 0 14px 24px rgba(95, 63, 30, 0.14);
    transform: rotate(-3deg);
    overflow: hidden;
}

.login-package:before {
    content: "";
    position: absolute;
    top: 0;
    bottom: 0;
    left: 50%;
    width: 22px;
    transform: translateX(-50%);
    background: rgba(255, 224, 176, 0.42);
}

.login-package:after {
    content: "";
    position: absolute;
    left: 15px;
    right: 15px;
    top: 13px;
    height: 3px;
    border-radius: 10px;
    background: rgba(112, 70, 31, 0.22);
}

.login-package-label {
    position: absolute;
    z-index: 2;
    left: 22px;
    top: 29px;
    width: 82px;
    height: 38px;
    border-radius: 6px;
    background: #ffffff;
    border: 1px solid #e3e8ef;
    box-shadow: 0 5px 10px rgba(15, 23, 42, 0.08);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 3px;
}

.login-package-label .brand {
    color: #00a9e8;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: -0.4px;
}

.login-package-label .code {
    width: 47px;
    height: 5px;
    border-radius: 5px;
    background: #dcecff;
}

.login-visual-label {
    position: absolute;
    left: 190px;
    bottom: 27px;
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
            '<div class="login-panel-title">Gestão de <span>insumos</span></div>'
            '<div class="login-panel-text">Consulte, acompanhe e gerencie os insumos enviados para sua operação em um único lugar.</div>'
            '<div class="login-feature"><div class="login-feature-icon">📦</div><div>Controle de insumos</div></div>'
            '<div class="login-feature"><div class="login-feature-icon">↩️</div><div>Acompanhamento de devoluções</div></div>'
            '<div class="login-feature"><div class="login-feature-icon">📊</div><div>Informações de valores</div></div>'
            '<div class="login-panel-bottom">Tenha as informações de forma rápida, organizada e centralizada.</div>'
            '<div class="login-visual">'
            '<div class="login-package">'
            '<div class="login-package-label">'
            '<div class="brand">loggi</div>'
            '<div class="code"></div>'
            '</div>'
            '</div>'
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
