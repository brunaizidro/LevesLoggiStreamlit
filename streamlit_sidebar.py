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

/* Ícones SVG próprios, alinhados ao texto dos botões */
[data-testid="stSidebar"] .st-key-leves-nav-menu [data-testid="stButton"] > button::before {content:"";display:inline-block;flex:0 0 19px;width:19px;height:19px;background-color:currentColor;-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;-webkit-mask-position:center;mask-position:center;-webkit-mask-size:contain;mask-size:contain;}
.st-key-nav_leves_envios button::before{-webkit-mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D'm12%203%208%204.5v9L12%2021l-8-4.5v-9L12%203Z'%2F%3E%3Cpath%20d%3D'm4.3%207.5%207.7%204.4%207.7-4.4M12%2021v-9.1'%2F%3E%3C%2Fsvg%3E");mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D'm12%203%208%204.5v9L12%2021l-8-4.5v-9L12%203Z'%2F%3E%3Cpath%20d%3D'm4.3%207.5%207.7%204.4%207.7-4.4M12%2021v-9.1'%2F%3E%3C%2Fsvg%3E");}
.st-key-nav_leves_recebimentos button::before{-webkit-mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D'M4%2013h4l2%203h4l2-3h4v7H4zM12%203v9m-4-4%204%204%204-4'%2F%3E%3C%2Fsvg%3E");mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D'M4%2013h4l2%203h4l2-3h4v7H4zM12%203v9m-4-4%204%204%204-4'%2F%3E%3C%2Fsvg%3E");}
.st-key-nav_leves_conciliacao button::before{-webkit-mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Crect%20x%3D'5'%20y%3D'3'%20width%3D'14'%20height%3D'18'%20rx%3D'1'%2F%3E%3Cpath%20d%3D'M9%208h6M9%2012h6M9%2016h6'%2F%3E%3C%2Fsvg%3E");mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Crect%20x%3D'5'%20y%3D'3'%20width%3D'14'%20height%3D'18'%20rx%3D'1'%2F%3E%3Cpath%20d%3D'M9%208h6M9%2012h6M9%2016h6'%2F%3E%3C%2Fsvg%3E");}
.st-key-nav_leves_cobrancas button::before{-webkit-mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Ccircle%20cx%3D'12'%20cy%3D'12'%20r%3D'9'%2F%3E%3Cpath%20d%3D'M15%208.5c-.7-.8-1.7-1.2-3-1.2-1.5%200-2.5.8-2.5%201.9%200%203%205.5%201.2%205.5%204.3%200%201.2-1.1%202.2-2.8%202.2-1.3%200-2.5-.5-3.3-1.4M12%205.5v13'%2F%3E%3C%2Fsvg%3E");mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Ccircle%20cx%3D'12'%20cy%3D'12'%20r%3D'9'%2F%3E%3Cpath%20d%3D'M15%208.5c-.7-.8-1.7-1.2-3-1.2-1.5%200-2.5.8-2.5%201.9%200%203%205.5%201.2%205.5%204.3%200%201.2-1.1%202.2-2.8%202.2-1.3%200-2.5-.5-3.3-1.4M12%205.5v13'%2F%3E%3C%2Fsvg%3E");}
.st-key-nav_leves_devolucoes button::before{-webkit-mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D'M9%2014%204%209l5-5M4%209h10a6%206%200%200%201%200%2012h-2'%2F%3E%3C%2Fsvg%3E");mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D'M9%2014%204%209l5-5M4%209h10a6%206%200%200%201%200%2012h-2'%2F%3E%3C%2Fsvg%3E");}
.st-key-nav_leves_pendencias button::before{-webkit-mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D'M18%209a6%206%200%200%200-12%200c0%207-3%207-3%209h18c0-2-3-2-3-9M10%2021h4'%2F%3E%3C%2Fsvg%3E");mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D'M18%209a6%206%200%200%200-12%200c0%207-3%207-3%209h18c0-2-3-2-3-9M10%2021h4'%2F%3E%3C%2Fsvg%3E");}
.st-key-nav_leves_usuarios button::before{-webkit-mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D'M16%2021v-2a4%204%200%200%200-4-4H6a4%204%200%200%200-4%204v2M9%2011a4%204%200%201%200%200-8%204%204%200%200%200%200%208ZM20%208v6M23%2011h-6'%2F%3E%3C%2Fsvg%3E");mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D'M16%2021v-2a4%204%200%200%200-4-4H6a4%204%200%200%200-4%204v2M9%2011a4%204%200%201%200%200-8%204%204%200%200%200%200%208ZM20%208v6M23%2011h-6'%2F%3E%3C%2Fsvg%3E");}
.st-key-nav_leves_relatorios button::before{-webkit-mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D'M4%2020V10M10%2020V4M16%2020v-7M22%2020H2'%2F%3E%3C%2Fsvg%3E");mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D'M4%2020V10M10%2020V4M16%2020v-7M22%2020H2'%2F%3E%3C%2Fsvg%3E");}
.st-key-nav_leves_configuracoes button::before{-webkit-mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Ccircle%20cx%3D'12'%20cy%3D'12'%20r%3D'3'%2F%3E%3Cpath%20d%3D'm19.4%2015%20.1.1%201.4%201.1-1.4%202.4-1.7-.6a8%208%200%200%201-1.4.8l-.3%201.8h-2.8l-.3-1.8a8%208%200%200%201-1.4-.8l-1.7.6-1.4-2.4%201.4-1.1a8%208%200%200%201%200-1.7l-1.4-1.1%201.4-2.4%201.7.6a8%208%200%200%201%201.4-.8l.3-1.8h2.8l.3%201.8a8%208%200%200%201%201.4.8l1.7-.6%201.4%202.4-1.4%201.1a8%208%200%200%201%200%201.7Z'%2F%3E%3C%2Fsvg%3E");mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Ccircle%20cx%3D'12'%20cy%3D'12'%20r%3D'3'%2F%3E%3Cpath%20d%3D'm19.4%2015%20.1.1%201.4%201.1-1.4%202.4-1.7-.6a8%208%200%200%201-1.4.8l-.3%201.8h-2.8l-.3-1.8a8%208%200%200%201-1.4-.8l-1.7.6-1.4-2.4%201.4-1.1a8%208%200%200%201%200-1.7l-1.4-1.1%201.4-2.4%201.7.6a8%208%200%200%201%201.4-.8l.3-1.8h2.8l.3%201.8a8%208%200%200%201%201.4.8l1.7-.6%201.4%202.4-1.4%201.1a8%208%200%200%201%200%201.7Z'%2F%3E%3C%2Fsvg%3E");}
 
/* Ajuste fino da navegação: ícone e texto próximos, alinhados à esquerda */
[data-testid="stSidebar"] .st-key-leves-nav-menu [data-testid="stButton"] > button {
    justify-content:flex-start !important;
    gap:8px !important;
    padding-left:12px !important;
    padding-right:12px !important;
    text-align:left !important;
    color:#FFFFFF !important;
    background-color:transparent !important;
}
[data-testid="stSidebar"] .st-key-leves-nav-menu [data-testid="stButton"] > button > div,
[data-testid="stSidebar"] .st-key-leves-nav-menu [data-testid="stButton"] > button [data-testid="stMarkdownContainer"] {
    display:flex !important;
    flex:0 1 auto !important;
    width:auto !important;
    min-width:0 !important;
    margin:0 !important;
    padding:0 !important;
    justify-content:flex-start !important;
    align-items:center !important;
    text-align:left !important;
}
[data-testid="stSidebar"] .st-key-leves-nav-menu [data-testid="stButton"] > button p,
[data-testid="stSidebar"] .st-key-leves-nav-menu [data-testid="stButton"] > button span {
    color:inherit !important;
    text-align:left !important;
    margin:0 !important;
    line-height:1.2 !important;
}
[data-testid="stSidebar"] .st-key-leves-nav-menu [data-testid="stButton"] > button[kind="secondary"] {
    color:#FFFFFF !important;
    background:#075BEA !important;
    border-color:transparent !important;
}
[data-testid="stSidebar"] .st-key-leves-nav-menu [data-testid="stButton"] > button[kind="secondary"]:hover {
    color:#FFFFFF !important;
    background:#176CF5 !important;
}
[data-testid="stSidebar"] .st-key-leves-nav-menu [data-testid="stButton"] > button[kind="primary"] {
    color:#075BEA !important;
    background:#FFFFFF !important;
    border-color:#FFFFFF !important;
}
[data-testid="stSidebar"] .st-key-leves-nav-menu [data-testid="stButton"] > button[kind="primary"] p,
[data-testid="stSidebar"] .st-key-leves-nav-menu [data-testid="stButton"] > button[kind="primary"] span {
    color:#075BEA !important;
}
[data-testid="stSidebar"] .st-key-leves-nav-menu [data-testid="stButton"] > button::before {
    background-color:currentColor !important;
    margin:0 !important;
}

/* Rodapé e suporte: contraste consistente com o fundo azul do portal */
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background:rgba(0,48,150,.18) !important;
    border:1px solid rgba(255,255,255,.22) !important;
    border-radius:12px !important;
    overflow:hidden !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] details,
[data-testid="stSidebar"] [data-testid="stExpander"] details > div {
    background:transparent !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary,
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
    background:#075BEA !important;
    color:#FFFFFF !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary *,
[data-testid="stSidebar"] [data-testid="stExpander"] summary p,
[data-testid="stSidebar"] [data-testid="stExpander"] summary span {
    color:#FFFFFF !important;
    fill:#FFFFFF !important;
    font-family:Montserrat,sans-serif !important;
    font-weight:700 !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stVerticalBlock"],
[data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stHorizontalBlock"] {
    background:transparent !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] label,
[data-testid="stSidebar"] [data-testid="stExpander"] label p,
[data-testid="stSidebar"] [data-testid="stExpander"] .stMarkdown,
[data-testid="stSidebar"] [data-testid="stExpander"] .stMarkdown p {
    color:#FFFFFF !important;
    font-family:Montserrat,sans-serif !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] input,
[data-testid="stSidebar"] [data-testid="stExpander"] textarea,
[data-testid="stSidebar"] [data-testid="stExpander"] select {
    background:#FFFFFF !important;
    color:#17345F !important;
    -webkit-text-fill-color:#17345F !important;
    border:1px solid #B8D0F2 !important;
    border-radius:9px !important;
    caret-color:#075BEA !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] input::placeholder,
[data-testid="stSidebar"] [data-testid="stExpander"] textarea::placeholder {
    color:#64748B !important;
    -webkit-text-fill-color:#64748B !important;
    opacity:1 !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stFormSubmitButton"] button,
[data-testid="stSidebar"] [data-testid="stExpander"] button[kind="primary"] {
    background:#0068F5 !important;
    color:#FFFFFF !important;
    border:1px solid #0068F5 !important;
    border-radius:10px !important;
    font-family:Montserrat,sans-serif !important;
    font-weight:800 !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stFormSubmitButton"] button *,
[data-testid="stSidebar"] [data-testid="stExpander"] button[kind="primary"] * {
    color:#FFFFFF !important;
}
/* Botões de rodapé (manual, atualizar e sair): azul com texto branco */
[data-testid="stSidebar"] .stButton:not(.st-key-leves-nav-menu .stButton) > button,
[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button {
    background:#0068F5 !important;
    color:#FFFFFF !important;
    border:1px solid #0068F5 !important;
    border-radius:10px !important;
    font-family:Montserrat,sans-serif !important;
    font-weight:800 !important;
}
[data-testid="stSidebar"] .stButton:not(.st-key-leves-nav-menu .stButton) > button *,
[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button * {
    color:#FFFFFF !important;
}

/* Mantém a fonte de ícones do Streamlit no chevron do expander.
   Sem isso, "arrow_drop_down" aparece como texto sobre o título. */
[data-testid="stSidebar"] [data-testid="stExpander"] summary [data-testid="stIconMaterial"],
[data-testid="stSidebar"] [data-testid="stExpander"] summary [data-testid="stIconMaterial"] * {
    font-family:"Material Symbols Rounded" !important;
    font-size:20px !important;
    font-weight:normal !important;
    line-height:1 !important;
    font-feature-settings:"liga" !important;
    letter-spacing:normal !important;
    color:#FFFFFF !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary p {
    font-family:Montserrat,sans-serif !important;
    color:#FFFFFF !important;
    font-weight:700 !important;
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
