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
/* Menu lateral — ícones individuais em traço, alinhamento e estados */
[data-testid="stSidebar"] [role="radiogroup"] {
    display:flex !important;
    flex-direction:column !important;
    gap:2px !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label {
    position:relative !important;
    display:flex !important;
    align-items:center !important;
    box-sizing:border-box !important;
    min-height:34px !important;
    padding:5px 10px !important;
    margin:0 0 0 0 !important;
    border-radius:9px !important;
    background:transparent !important;
    color:#fff !important;
    transition:background .15s ease,color .15s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background:rgba(255,255,255,.12) !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {
    display:none !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label p {
    display:flex !important;
    align-items:center !important;
    gap:10px !important;
    width:100% !important;
    color:#fff !important;
    font-family:Montserrat,sans-serif !important;
    font-size:12px !important;
    line-height:1.2 !important;
    font-weight:700 !important;
    margin:0 !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label p:before {
    content:"";
    display:inline-block !important;
    flex:0 0 19px !important;
    width:19px !important;
    height:19px !important;
    background-color:#fff !important;
    -webkit-mask-repeat:no-repeat !important;
    mask-repeat:no-repeat !important;
    -webkit-mask-position:center !important;
    mask-position:center !important;
    -webkit-mask-size:contain !important;
    mask-size:contain !important;
}
/* Envios — caixa */
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(1) p:before {
    -webkit-mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z'/%3E%3Cpath d='m4.3 7.5 7.7 4.4 7.7-4.4M12 21v-9.1'/%3E%3C/svg%3E");
    mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z'/%3E%3Cpath d='m4.3 7.5 7.7 4.4 7.7-4.4M12 21v-9.1'/%3E%3C/svg%3E");
}
/* Recebimentos — bandeja com seta */
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(2) p:before {
    -webkit-mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 13h4l2 3h4l2-3h4v7H4zM12 3v9m-4-4 4 4 4-4'/%3E%3C/svg%3E");
    mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 13h4l2 3h4l2-3h4v7H4zM12 3v9m-4-4 4 4 4-4'/%3E%3C/svg%3E");
}
/* Conciliação — lista */
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(3) p:before {
    -webkit-mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='5' y='3' width='14' height='18' rx='1'/%3E%3Cpath d='M9 8h6M9 12h6M9 16h6'/%3E%3C/svg%3E");
    mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='5' y='3' width='14' height='18' rx='1'/%3E%3Cpath d='M9 8h6M9 12h6M9 16h6'/%3E%3C/svg%3E");
}
/* Cobranças — dinheiro */
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(4) p:before {
    -webkit-mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='9'/%3E%3Cpath d='M15 8.5c-.7-.8-1.7-1.2-3-1.2-1.5 0-2.5.8-2.5 1.9 0 3 5.5 1.2 5.5 4.3 0 1.2-1.1 2.2-2.8 2.2-1.3 0-2.5-.5-3.3-1.4M12 5.5v13'/%3E%3C/svg%3E");
    mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='9'/%3E%3Cpath d='M15 8.5c-.7-.8-1.7-1.2-3-1.2-1.5 0-2.5.8-2.5 1.9 0 3 5.5 1.2 5.5 4.3 0 1.2-1.1 2.2-2.8 2.2-1.3 0-2.5-.5-3.3-1.4M12 5.5v13'/%3E%3C/svg%3E");
}
/* Devoluções — seta de retorno */
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(5) p:before {
    -webkit-mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9 14 4 9l5-5M4 9h10a6 6 0 0 1 0 12h-2'/%3E%3C/svg%3E");
    mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9 14 4 9l5-5M4 9h10a6 6 0 0 1 0 12h-2'/%3E%3C/svg%3E");
}
/* Pendências — sino */
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(6) p:before {
    -webkit-mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4'/%3E%3C/svg%3E");
    mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4'/%3E%3C/svg%3E");
}
/* Separador e título de Administração */
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(7) {
    margin-top:25px !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(7):before {
    content:"";
    position:absolute;
    left:-1px;right:-1px;top:-15px;
    height:1px;
    background:rgba(255,255,255,.55);
}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(7):after {
    content:"ADMINISTRAÇÃO";
    position:absolute;
    left:0;right:0;top:-34px;
    color:#C8DDFF;
    font-family:Montserrat,sans-serif;
    font-size:10px;font-weight:800;letter-spacing:1.6px;
    pointer-events:none;
}
/* Usuários — grupo */
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(7) p:before {
    -webkit-mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM20 8v6M23 11h-6'/%3E%3C/svg%3E");
    mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM20 8v6M23 11h-6'/%3E%3C/svg%3E");
}
/* Relatórios — barras */
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(8) p:before {
    -webkit-mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 20V10M10 20V4M16 20v-7M22 20H2'/%3E%3C/svg%3E");
    mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 20V10M10 20V4M16 20v-7M22 20H2'/%3E%3C/svg%3E");
}
/* Configurações — engrenagem */
[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(9) p:before {
    -webkit-mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z'/%3E%3Cpath d='m19.4 15 .1.1 1.4 1.1-1.4 2.4-1.7-.6a8 8 0 0 1-1.4.8l-.3 1.8h-2.8l-.3-1.8a8 8 0 0 1-1.4-.8l-1.7.6-1.4-2.4 1.4-1.1a8 8 0 0 1 0-1.7l-1.4-1.1 1.4-2.4 1.7.6a8 8 0 0 1 1.4-.8l.3-1.8h2.8l.3 1.8a8 8 0 0 1 1.4.8l1.7-.6 1.4 2.4-1.4 1.1a8 8 0 0 1 0 1.7Z'/%3E%3C/svg%3E");
    mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z'/%3E%3Cpath d='m19.4 15 .1.1 1.4 1.1-1.4 2.4-1.7-.6a8 8 0 0 1-1.4.8l-.3 1.8h-2.8l-.3-1.8a8 8 0 0 1-1.4-.8l-1.7.6-1.4-2.4 1.4-1.1a8 8 0 0 1 0-1.7l-1.4-1.1 1.4-2.4 1.7.6a8 8 0 0 1 1.4-.8l.3-1.8h2.8l.3 1.8a8 8 0 0 1 1.4.8l1.7-.6 1.4 2.4-1.4 1.1a8 8 0 0 1 0 1.7Z'/%3E%3C/svg%3E");
}
/* Item selecionado — fundo branco, texto/ícone azul e seta lateral */
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background:#fff !important;
    color:#075BEA !important;
    box-shadow:0 2px 8px rgba(0,0,0,.10) !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {
    color:#075BEA !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p:before {
    background-color:#075BEA !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p:after {
    content:"";
    margin-left:auto;
    width:7px;height:7px;
    border-top:2px solid #075BEA;
    border-right:2px solid #075BEA;
    transform:rotate(45deg);
}
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
