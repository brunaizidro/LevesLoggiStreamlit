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
        /* ===== LOGIN PORTAL LEVES — IDENTIDADE LOGGI ===== */
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"], [data-testid="stApp"] {
            font-family: 'Montserrat', sans-serif !important;
        }
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(180deg, #0067FC 0%, #087EF5 42%, #F4F8FF 42%, #F4F8FF 100%) !important;
            min-height: 100vh;
        }
        [data-testid="stAppViewBlockContainer"] {
            max-width: 100% !important;
            padding: 3.2rem 20px 2rem !important;
        }
        [data-testid="stHeader"], [data-testid="stToolbar"] {
            background: transparent !important;
            display: none !important;
        }
        [data-testid="column"]:has([data-testid="stForm"]) {
            max-width: 560px !important;
            margin: 0 auto !important;
        }
        .login-logo { text-align:center; margin: 0 auto 18px; }
        .login-logo img {
            display:block; width:180px; max-width:72%; height:auto; margin:0 auto;
            filter: brightness(0) invert(1);
        }
        .login-title {
            text-align:center; color:#0067FC; font-family:'Montserrat',sans-serif;
            font-size:42px; font-weight:800; letter-spacing:-1.5px;
            line-height:1.12; margin: 12px 0 12px; text-transform:none;
        }
        .login-description {
            text-align:center; color:#65748B; font-family:'Montserrat',sans-serif;
            font-size:15px; font-weight:500; line-height:1.65;
            max-width:450px; margin:0 auto 26px;
        }
        [data-testid="stForm"] {
            background:#fff !important; border:1px solid #E4EAF3 !important;
            border-radius:22px !important; padding:30px 30px 26px !important;
            box-shadow:0 18px 48px rgba(12,48,100,.13) !important;
        }
        [data-testid="stForm"] label {
            color:#23344D !important; font-family:'Montserrat',sans-serif !important;
            font-size:13px !important; font-weight:700 !important;
        }
        [data-testid="stForm"] input {
            border-radius:11px !important; border:1px solid #D9E2EF !important;
            min-height:48px !important; font-family:'Montserrat',sans-serif !important;
            background:#fff !important;
        }
        [data-testid="stForm"] input:focus {
            border-color:#0067FC !important;
            box-shadow:0 0 0 3px rgba(0,103,252,.11) !important;
        }
        [data-testid="stFormSubmitButton"] button {
            width:100% !important; min-height:50px !important; margin-top:10px !important;
            border-radius:11px !important; border:0 !important;
            background:linear-gradient(90deg,#005BEE,#087BFF) !important;
            color:#fff !important; font-family:'Montserrat',sans-serif !important;
            font-size:15px !important; font-weight:800 !important;
            box-shadow:0 7px 18px rgba(0,103,252,.20) !important;
        }
        [data-testid="stFormSubmitButton"] button:hover {
            background:#004FD1 !important; transform:translateY(-1px);
        }
        [data-testid="stAppViewContainer"] .stButton > button,
        [data-testid="stAppViewContainer"] .stDownloadButton > button {
            border-radius:11px !important; min-height:46px !important;
            font-family:'Montserrat',sans-serif !important; font-weight:700 !important;
        }
        [data-testid="stAppViewContainer"] .stButton > button {
            border:1px solid #D7E1EF !important; background:#fff !important;
            color:#18345A !important;
        }
        [data-testid="stAppViewContainer"] .stButton > button:hover {
            border-color:#0067FC !important; color:#0067FC !important;
        }
        [data-testid="stDownloadButton"] button {
            background:#EFF6FF !important; border:1px solid #D6E7FF !important;
            color:#174A91 !important; width:100% !important;
        }
        [data-testid="stAlert"] {
            border-radius:11px !important; font-family:'Montserrat',sans-serif !important;
        }
        .login-manual { margin-top:14px; }
        .login-help-title {
            text-align:center; color:#7D8DA4; font-family:'Montserrat',sans-serif;
            font-size:12px; font-weight:600; margin:22px 0 8px;
        }
        [data-testid="stExpander"] {
            border:1px solid #E1E8F2 !important; border-radius:12px !important;
            background:#fff !important; overflow:hidden !important;
        }
        [data-testid="stExpander"] summary {
            font-family:'Montserrat',sans-serif !important; font-size:13px !important;
            font-weight:600 !important; color:#29415F !important;
        }
        .login-footer {
            text-align:center; color:#9AA8BA; font-family:'Montserrat',sans-serif;
            font-size:11px; margin-top:20px;
        }
        @media (max-width: 700px) {
            [data-testid="stAppViewBlockContainer"] { padding:2rem 14px !important; }
            [data-testid="stForm"] { padding:23px 18px 20px !important; }
            .login-title { font-size:34px; }
            .login-description { font-size:13px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, col, _ = st.columns([1, 1.1, 1])

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
