"""
streamlit_sidebar.py — Sidebar V6 do Portal LEVES.

Mantém a mesma função pública sidebar() e get_base64_image(), mas melhora a
hierarquia visual sem alterar a navegação ou as regras do app.py.
"""

import base64
import os

import streamlit as st

from streamlit_estilizador import PageStyler

LOGO_PATH = "image_simbolo_lebre_1.png"


def get_base64_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _estilos_extra():
    st.markdown(
        """
<style>
/* ============================================================
   PORTAL LEVES — SIDEBAR V6
   ============================================================ */


/* Largura da navegação */
[data-testid="stSidebar"] {
    width: 280px !important;
    min-width: 280px !important;
}

[data-testid="stSidebar"] > div {
    width: 280px !important;
}

[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(180deg, #0067fc 0%, #0058dc 100%) !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 14px !important;
}

/* Logo */
.leves-sb-logo {
    text-align: center;
    margin: 4px auto 7px auto;
}

.leves-sb-logo img {
    width: 118px;
    max-width: 72%;
    height: auto;
}

.leves-sb-title {
    color: #ffffff;
    font-family: Montserrat, sans-serif;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -.2px;
    text-align: center;
    margin-bottom: 16px;
}

/* Card da operação */
.sb-card {
    background: rgba(255,255,255,.13) !important;
    border: 1px solid rgba(255,255,255,.24) !important;
    border-radius: 14px !important;
    padding: 13px 14px !important;
    margin: 0 0 15px 0 !important;
    box-shadow: 0 7px 18px rgba(0,0,0,.06);
}

.sb-card .nome {
    color: #ffffff !important;
    font-family: Montserrat, sans-serif !important;
    font-size: 14px !important;
    line-height: 1.35 !important;
    font-weight: 700 !important;
}

.sb-card .papel {
    color: rgba(255,255,255,.78) !important;
    font-family: Montserrat, sans-serif !important;
    font-size: 11px !important;
    margin-top: 4px !important;
}

.sb-section-label {
    color: rgba(255,255,255,.62);
    font-family: Montserrat, sans-serif;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin: 8px 3px 8px 3px;
}

.sb-sep {
    border: none !important;
    border-top: 1px solid rgba(255,255,255,.18) !important;
    margin: 13px 0 !important;
}

/* Radio: esconde as bolinhas do Streamlit */
[data-testid="stSidebar"] [role="radiogroup"] {
    gap: 4px !important;
}

[data-testid="stSidebar"] [role="radiogroup"] label {
    color: #ffffff !important;
    background: transparent !important;
    border-radius: 10px !important;
    padding: 8px 10px !important;
    margin: 0 !important;
    transition: background .15s ease, color .15s ease;
}

[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(255,255,255,.10) !important;
}

/* Texto dos itens não selecionados: sempre branco */
[data-testid="stSidebar"] [role="radiogroup"] label,
[data-testid="stSidebar"] [role="radiogroup"] label p,
[data-testid="stSidebar"] [role="radiogroup"] label span,
[data-testid="stSidebar"] [role="radiogroup"] label div {
    color: #ffffff !important;
}

/* Item selecionado: fundo branco + texto azul */
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: #ffffff !important;
    color: #0067fc !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 12px rgba(0,0,0,.08);
}

[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {
    display: none !important;
}

[data-testid="stSidebar"] [role="radiogroup"] label p {
    color: #ffffff !important;
    font-family: Montserrat, sans-serif !important;
    font-size: 13px !important;
}

[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p,
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) span,
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) div {
    color: #0067fc !important;
}

[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
    display: none !important;
}

/* Botões secundários */
[data-testid="stSidebar"] .stButton > button,
[data-testid="stSidebar"] .stDownloadButton > button {
    min-height: 42px !important;
    background: rgba(255,255,255,.09) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,.25) !important;
    border-radius: 10px !important;
    font-family: Montserrat, sans-serif !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    box-shadow: none !important;
}

[data-testid="stSidebar"] .stButton > button:hover,
[data-testid="stSidebar"] .stDownloadButton > button:hover {
    background: #ffffff !important;
    color: #0067fc !important;
    border-color: #ffffff !important;
}

[data-testid="stSidebar"] .stButton > button *,
[data-testid="stSidebar"] .stDownloadButton > button * {
    color: inherit !important;
}

/* Suporte */
[data-testid="stSidebar"] [data-testid="stExpander"] {
    border: 1px solid rgba(255,255,255,.18) !important;
    border-radius: 10px !important;
    background: rgba(0,0,0,.04) !important;
}

[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    color: #ffffff !important;
    font-family: Montserrat, sans-serif !important;
    font-size: 12px !important;
    font-weight: 600 !important;
}

</style>
        """,
        unsafe_allow_html=True,
    )


def sidebar():
    estilizador = PageStyler()
    base = os.path.dirname(os.path.abspath(__file__))
    caminho = os.path.join(base, LOGO_PATH)
    logo_base64 = get_base64_image(caminho) if os.path.exists(caminho) else ""

    estilizador.apply_sidebar_css(logo_base64)
    _estilos_extra()

    with st.sidebar:
        if logo_base64:
            st.markdown(
                f'<div class="leves-sb-logo">'
                f'<img src="data:image/png;base64,{logo_base64}">'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="leves-sb-title">Portal LEVES</div>', unsafe_allow_html=True)
        st.markdown('<div class="sb-section-label">Operação</div>', unsafe_allow_html=True)
        st.markdown("<hr class='sb-sep'>", unsafe_allow_html=True)
