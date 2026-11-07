"""
streamlit_sidebar.py — identidade visual da navegação do Portal LEVES.
Mantém a navegação e as regras do app.py sem alterações.
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
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,500,0,0');
[data-testid="stHeader"], [data-testid="stToolbar"] {display:none !important;}
[data-testid="stSidebar"] {width:300px !important;min-width:300px !important;max-width:300px !important;transform:none !important;visibility:visible !important;display:block !important;}
[data-testid="stSidebar"] > div {width:300px !important;min-width:300px !important;max-width:300px !important;}
[data-testid="stSidebar"] > div:first-child {background:linear-gradient(180deg,#075FEA 0%,#064FC5 100%) !important;padding:18px 16px 18px !important;}
[data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] {display:none !important;}
[data-testid="stSidebar"] button[aria-label*="Close"], [data-testid="stSidebar"] button[aria-label*="Fechar"], [data-testid="stSidebar"] button[title*="Close"], [data-testid="stSidebar"] button[title*="Fechar"] {display:none !important;}
section[data-testid="stSidebar"] + div {margin-left:0 !important;}
.leves-sb-logo {text-align:center;margin:4px auto 2px;line-height:0;}
.leves-sb-logo img {width:116px;max-width:72%;height:auto;object-fit:contain;}
.leves-sb-title {color:#fff !important;text-align:center;font-family:Montserrat,sans-serif !important;font-size:22px !important;font-weight:800 !important;letter-spacing:-.5px;margin:5px 0 2px !important;}
.leves-sb-subtitle {color:rgba(255,255,255,.82);text-align:center;font-family:Montserrat,sans-serif;font-size:10px;font-weight:700;letter-spacing:2.1px;margin:0 0 20px;}
.sb-sep {border:0;border-top:1px solid rgba(255,255,255,.25);margin:14px 0 !important;}
.sb-section-label {color:#C8DDFF !important;font-family:Montserrat,sans-serif !important;font-size:10px !important;font-weight:800 !important;letter-spacing:1.6px;text-transform:uppercase;margin:8px 4px 8px;}
.sb-card {position:relative;background:rgba(255,255,255,.13) !important;border:1px solid rgba(255,255,255,.25) !important;border-radius:16px !important;padding:13px 12px 13px 66px !important;margin:0 0 20px 0 !important;min-height:68px;box-shadow:0 6px 18px rgba(0,0,0,.07);}
.sb-card:before {content:"person";position:absolute;left:14px;top:13px;width:42px;height:42px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:rgba(35,157,255,.72);color:#fff;font-family:"Material Symbols Rounded";font-size:25px;font-weight:500;}
.sb-card .nome {color:#fff !important;font-family:Montserrat,sans-serif !important;font-size:13px !important;line-height:1.3 !important;font-weight:800 !important;margin-top:4px;}
.sb-card .papel {color:#DCEAFF !important;font-family:Montserrat,sans-serif !important;font-size:11px !important;font-weight:600 !important;margin-top:3px;}
/* Navegação real por botões — separação e estados visuais */
[data-testid="stSidebar"] .st-key-leves-nav-menu {
    display:flex !important;
    flex-direction:column !important;
    gap:2px !important;
}
[data-testid="stSidebar"] .st-key-leves-nav-menu .leves-nav-section {
    color:#C8DDFF !important;
    font-family:Montserrat,sans-serif !important;
    font-size:10px !important;
    line-height:1.2 !important;
    font-weight:800 !important;
    letter-spacing:1.6px !important;
    margin:2px 4px 8px !important;
}
[data-testid="stSidebar"] .st-key-leves-nav-menu .leves-nav-admin {
    margin-top:12px !important;
}
[data-testid="stSidebar"] .st-key-leves-nav-menu .leves-nav-divider {
    height:1px !important;
    width:100% !important;
    background:rgba(255,255,255,.55) !important;
    margin:0 0 10px !important;
}
[data-testid="stSidebar"] .st-key-leves-nav-menu [data-testid="stButton"] {
    margin:0 !important;
    padding:0 !important;
}
[data-testid="stSidebar"] .st-key-leves-nav-menu [data-testid="stButton"] > button {
    min-height:34px !important;
    height:34px !important;
    padding:0 11px !important;
    border-radius:9px !important;
    border:1px solid transparent !important;
    box-shadow:none !important;
    display:flex !important;
    align-items:center !important;
    justify-content:flex-start !important;
    gap:10px !important;
    font-family:Montserrat,sans-serif !important;
    font-size:12px !important;
    line-height:1 !important;
    font-weight:700 !important;
    text-align:left !important;
    transition:background .15s ease,color .15s ease !important;
}
[data-testid="stSidebar"] .st-key-leves-nav-menu [data-testid="stButton"] > button[kind="secondary"] {
    color:#FFFFFF !important;
    background:transparent !important;
}
[data-testid="stSidebar"] .st-key-leves-nav-menu [data-testid="stButton"] > button[kind="secondary"]:hover {
    color:#FFFFFF !important;
    background:rgba(255,255,255,.13) !important;
    border-color:transparent !important;
}
[data-testid="stSidebar"] .st-key-leves-nav-menu [data-testid="stButton"] > button[kind="primary"] {
    color:#075BEA !important;
    background:#FFFFFF !important;
    border-color:#FFFFFF !important;
    box-shadow:0 2px 8px rgba(0,0,0,.10) !important;
}
[data-testid="stSidebar"] .st-key-leves-nav-menu [data-testid="stButton"] > button [data-testid="stIconMaterial"] {
    color:currentColor !important;
    font-size:19px !important;
}
[data-testid="stSidebar"] .st-key-leves-nav-menu [data-testid="stButton"] > button[kind="primary"]:after {
    content:"";
    width:7px;
    height:7px;
    margin-left:auto;
    border-top:2px solid #075BEA;
    border-right:2px solid #075BEA;
    transform:rotate(45deg);
}
[data-testid="stSidebar"] .st-key-leves-nav-menu [data-testid="stButton"] > button:focus {
    box-shadow:none !important;
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
                f'<div class="leves-sb-logo"><img src="data:image/png;base64,{logo_base64}" alt="Loggi"></div>',
                unsafe_allow_html=True,
            )
        st.markdown('<div class="leves-sb-title">Portal LEVES</div>', unsafe_allow_html=True)
        st.markdown('<div class="leves-sb-subtitle">GESTÃO DE INSUMOS</div>', unsafe_allow_html=True)
