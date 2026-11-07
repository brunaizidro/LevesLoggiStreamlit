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
[data-testid="stSidebar"] [role="radiogroup"] {display:flex !important;flex-direction:column !important;gap:4px !important;}
[data-testid="stSidebar"] [role="radiogroup"] label {position:relative !important;display:flex !important;align-items:center !important;min-height:42px !important;box-sizing:border-box !important;padding:8px 12px !important;margin:0 !important;border-radius:11px !important;background:transparent !important;color:#fff !important;transition:background .16s ease,color .16s ease;}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {background:rgba(255,255,255,.12) !important;}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {display:none !important;}
[data-testid="stSidebar"] [role="radiogroup"] label p {display:flex !important;align-items:center !important;gap:9px !important;color:#fff !important;font-family:Montserrat,sans-serif !important;font-size:13px !important;font-weight:700 !important;margin:0 !important;}
[data-testid="stSidebar"] [role="radiogroup"] label p:before {font-family:"Material Symbols Rounded" !important;font-size:19px !important;font-weight:500 !important;line-height:1 !important;display:inline-block !important;width:21px !important;text-align:center !important;color:rgba(255,255,255,.96) !important;font-feature-settings:"liga";}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(1) p:before {content:"inventory_2";}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(2) p:before {content:"move_to_inbox";}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(3) p:before {content:"receipt_long";}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(4) p:before {content:"payments";}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(5) p:before {content:"undo";}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(6) p:before {content:"notifications";}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(7) p:before {content:"groups";}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(8) p:before {content:"bar_chart";}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(9) p:before {content:"settings";}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(7) {margin-top:25px !important;}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(7):after {content:"ADMINISTRAÇÃO";position:absolute;left:0;right:0;top:-24px;padding:0 12px;color:#C8DDFF;font-family:Montserrat,sans-serif;font-size:10px;font-weight:800;letter-spacing:1.6px;pointer-events:none;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {background:#fff !important;color:#075BEA !important;box-shadow:0 4px 13px rgba(0,0,0,.10) !important;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {color:#075BEA !important;}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {display:none !important;}
[data-testid="stSidebar"] .stButton > button, [data-testid="stSidebar"] .stDownloadButton > button {width:100% !important;min-height:44px !important;border-radius:11px !important;font-family:Montserrat,sans-serif !important;font-size:12px !important;font-weight:700 !important;color:#fff !important;background:rgba(255,255,255,.10) !important;border:1px solid rgba(255,255,255,.25) !important;box-shadow:none !important;}
[data-testid="stSidebar"] .stButton > button:hover, [data-testid="stSidebar"] .stDownloadButton > button:hover {background:#fff !important;color:#075BEA !important;border-color:#fff !important;}
[data-testid="stSidebar"] .stButton > button *, [data-testid="stSidebar"] .stDownloadButton > button * {color:inherit !important;}
[data-testid="stSidebar"] [data-testid="stExpander"] {border:1px solid rgba(255,255,255,.20) !important;border-radius:11px !important;background:rgba(0,0,0,.04) !important;}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {color:#fff !important;font-family:Montserrat,sans-serif !important;font-size:12px !important;font-weight:700 !important;}
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
        st.markdown('<div class="sb-section-label">OPERAÇÃO</div>', unsafe_allow_html=True)
