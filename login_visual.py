"""
login_visual.py — visual da tela de login (só aparência; a lógica fica no app.py).

Tela dividida: à esquerda o painel da marca (degradê oficial Loggi, Azul Claro →
Azul Médio, com a logo branca); à direita o formulário em fundo branco, limpo,
em Montserrat — mesma linguagem dos módulos do portal.
"""

from __future__ import annotations

import base64
import functools
import json
import os

import streamlit as st

_RAIZ = os.path.dirname(os.path.abspath(__file__))

CSS = """
<style>
:root{--azul:#006aff;--azul-claro:#00baff;--azul-bg:#eaf3ff;--texto:#14213d;--texto-2:#66728a;--linha:#e3e9f2}
[data-testid="stApp"] *:not([data-testid="stIconMaterial"]):not(.material-symbols-rounded){font-family:Montserrat,sans-serif!important}
[data-testid="stApp"],[data-testid="stMain"],[data-testid="stAppViewContainer"]{background:#ffffff!important}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"]{display:none!important}
[data-testid="stMainBlockContainer"]{max-width:100%!important;padding:0!important}
.st-key-lg-tela > [data-testid="stHorizontalBlock"]{gap:0!important;min-height:100vh;align-items:stretch!important}
/* ---- painel da marca ---- */
.lg-marca{position:relative;overflow:hidden;height:100%;min-height:100vh;box-sizing:border-box;padding:56px 64px;
  background:linear-gradient(135deg,#00baff 25%,#006aff 75%);color:#fff;display:flex;flex-direction:column}
.lg-marca:before{content:"";position:absolute;width:520px;height:520px;border-radius:50%;right:-180px;bottom:-200px;background:rgba(255,255,255,.10)}
.lg-marca:after{content:"";position:absolute;width:300px;height:300px;border-radius:0 0 0 300px;right:-40px;top:-40px;background:rgba(255,255,255,.08)}
.lg-marca img{height:46px;position:absolute;top:56px;left:64px;z-index:1}
.lg-meio{margin:auto 0;position:relative;z-index:1;max-width:460px;min-height:min(562px,calc(100vh - 160px));box-sizing:border-box}  /* mesma altura do formulário: o topo de 'Portal Leves' fica na linha de 'Acesse sua conta' */
.lg-tag{display:inline-block;background:rgba(255,255,255,.18);border-radius:999px;padding:6px 14px;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}
.lg-meio h1{color:#fff!important;font-size:46px!important;font-weight:800!important;line-height:1.08!important;margin:18px 0 12px!important;padding:0!important;letter-spacing:-1px}
.lg-meio p{color:rgba(255,255,255,.92)!important;font-size:16px;font-weight:500;line-height:1.6;margin:0 0 28px}
.lg-item{display:flex;align-items:center;gap:14px;margin:0 0 14px;font-size:15px;font-weight:600}
.lg-item span{width:38px;height:38px;flex:0 0 38px;border-radius:12px;background:rgba(255,255,255,.18);display:flex;align-items:center;justify-content:center}
.lg-item svg{width:20px;height:20px}
.lg-rodape{position:absolute;left:64px;bottom:40px;z-index:1;font-size:12px;color:rgba(255,255,255,.8);font-weight:500}
/* ---- lado do formulário ---- */
.st-key-lg-form{max-width:420px;margin:0 auto;min-height:100vh;box-sizing:border-box;justify-content:center!important;padding:40px 24px!important}
.lg-ola{font-size:30px;font-weight:800;color:var(--texto);margin:0 0 6px;letter-spacing:-.5px}
.lg-sub{font-size:14.5px;color:var(--texto-2);margin:0 0 26px;line-height:1.5}
.st-key-lg-form [data-testid="stForm"]{border:0!important;padding:0!important;background:transparent!important}
.st-key-lg-form label p{font-size:13px!important;font-weight:700!important;color:var(--texto)!important}
.st-key-lg-form [data-baseweb="input"]{border-radius:12px!important;border:1px solid var(--linha)!important;background:#f7f9fc!important;min-height:48px}
.st-key-lg-form [data-baseweb="input"]:focus-within{border-color:var(--azul)!important;box-shadow:0 0 0 3px rgba(0,106,255,.12)!important;background:#fff!important}
.st-key-lg-form input{font-size:15px!important;background:transparent!important}
.st-key-lg-form [data-testid="stFormSubmitButton"] button{background:var(--azul)!important;border:0!important;color:#fff!important;border-radius:12px!important;
  min-height:50px!important;font-weight:700!important;font-size:15px!important;box-shadow:0 8px 20px rgba(0,106,255,.22)!important;margin-top:6px}
.st-key-lg-form [data-testid="stFormSubmitButton"] button *{color:#fff!important;font-weight:700!important}
.st-key-lg-form [data-testid="stFormSubmitButton"] button:hover{background:#0057d1!important}
.st-key-btn_esqueci_senha,.st-key-btn_voltar_login{display:flex;justify-content:flex-end}
.st-key-btn_esqueci_senha button,.st-key-btn_voltar_login button{border:0!important;background:transparent!important;color:var(--azul)!important;
  font-weight:700!important;font-size:13.5px!important;padding:0!important;min-height:28px!important;box-shadow:none!important;width:auto!important}
.st-key-btn_esqueci_senha button *,.st-key-btn_voltar_login button *{color:var(--azul)!important;font-weight:700!important}
.st-key-btn_esqueci_senha button:hover,.st-key-btn_voltar_login button:hover{text-decoration:underline}
.lg-rec{font-size:18px;font-weight:800;color:var(--texto);margin:18px 0 4px}
.lg-sep{display:flex;align-items:center;gap:12px;color:#97a2b4;font-size:12px;font-weight:600;margin:26px 0 12px}
.lg-sep:before,.lg-sep:after{content:"";flex:1;height:1px;background:var(--linha)}
.st-key-lg-form [data-testid="stExpander"]{border:1px solid var(--linha)!important;border-radius:12px!important;background:#fff!important}
.st-key-lg-form [data-testid="stExpander"] summary{font-weight:700!important;color:var(--texto)!important}
.st-key-lg-form [data-testid="stExpander"] summary p{font-weight:700!important}
.st-key-lg-btn-suporte button{background:#e6f0ff!important;border:1px solid #cfe0ff!important;border-radius:12px!important;min-height:50px!important;
  color:#0050c8!important;font-weight:700!important;font-size:15px!important;box-shadow:none!important;transition:all .15s}
.st-key-lg-btn-suporte button *{color:#0050c8!important;font-weight:700!important;font-size:15px!important}
.st-key-lg-btn-suporte button [data-testid="stIconMaterial"]{font-size:21px!important}
.st-key-lg-btn-suporte button:hover{background:#d6e7ff!important;border-color:var(--azul)!important;transform:translateY(-1px);box-shadow:0 6px 16px rgba(0,106,255,.15)!important}
[class*='st-key-ct_anexo_'] [data-testid='stFileUploaderDropzoneInstructions'] span{display:none!important}
[class*='st-key-ct_anexo_'] [data-testid='stFileUploaderDropzoneInstructions']::after{content:'PNG ou JPG · até 3 imagens de 5 MB';font-size:12.5px;color:#6b7a90;font-weight:600}
/* ---- janela de suporte: centralizada, título azul em selo ---- */
[data-testid="stDialog"]{background:rgba(10,30,70,.38)!important;backdrop-filter:blur(3px)}
[data-testid="stDialog"] > div{margin:auto 16px!important}
[data-testid="stDialog"] [role="dialog"]{border-radius:22px!important;border:0!important;box-shadow:0 24px 60px rgba(0,39,102,.25)!important}
[data-testid="stDialog"] [role="dialog"]:before{content:"";position:absolute;left:0;right:0;top:0;height:5px;background:linear-gradient(90deg,#00baff,#006aff);border-radius:22px 22px 0 0}
[data-testid="stDialog"] h2{padding-bottom:4px!important}
[data-testid="stDialog"] h2 p{display:inline-flex;align-items:center;gap:10px;background:#eaf3ff;color:#006aff!important;font-size:18px!important;font-weight:800!important;
  padding:9px 18px 9px 14px;border-radius:999px;margin:0!important}
[data-testid="stDialog"] h2 p:before{content:"";width:22px;height:22px;flex:0 0 22px;background:no-repeat center/contain url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23006aff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 14v-2a8 8 0 0 1 16 0v2'/%3E%3Crect x='3' y='14' width='4' height='6' rx='1.5'/%3E%3Crect x='17' y='14' width='4' height='6' rx='1.5'/%3E%3Cpath d='M19 20a3 3 0 0 1-3 2h-3'/%3E%3C/svg%3E")}
.lg-dlg-sub{font-size:14px;color:var(--texto-2);margin:2px 0 6px;line-height:1.6}
.lg-dlg-sla{display:inline-block;background:#f1f5fb;color:#4a5a75;border-radius:999px;padding:2px 10px;font-size:12px;font-weight:700;margin-left:4px;white-space:nowrap}
[data-testid="stDialog"] label p{font-size:13px!important;font-weight:700!important;color:var(--texto)!important}
[data-testid="stDialog"] [data-baseweb="input"],[data-testid="stDialog"] [data-baseweb="textarea"]{border-radius:12px!important;border:1px solid var(--linha)!important;background:#f7f9fc!important}
[data-testid="stDialog"] [data-baseweb="input"]:focus-within,[data-testid="stDialog"] [data-baseweb="textarea"]:focus-within{border-color:var(--azul)!important;background:#fff!important;box-shadow:0 0 0 3px rgba(0,106,255,.12)!important}
[data-testid="stDialog"] input,[data-testid="stDialog"] textarea{background:transparent!important}
[data-testid="stDialog"] [data-testid="stFileUploaderDropzone"]{background:#f5f9ff!important;border:1.5px dashed #b9d3ff!important;border-radius:14px!important}
[data-testid="stDialog"] [data-testid="stFileUploaderDropzone"] button{border-radius:10px!important;border-color:#cfe0ff!important;color:#0050c8!important;font-weight:700!important}
[data-testid="stDialog"] [data-testid="stFormSubmitButton"] button{background:var(--azul)!important;border:0!important;border-radius:12px!important;min-height:48px!important;
  box-shadow:0 8px 20px rgba(0,106,255,.22)!important;margin-top:6px}
[data-testid="stDialog"] [data-testid="stFormSubmitButton"] button:hover{background:#0057d1!important}
[data-testid="stDialog"] [data-testid="stFormSubmitButton"] button *{color:#fff!important;font-weight:700!important}
.lg-foot{text-align:center;font-size:12px;color:#97a2b4;margin-top:28px}
.st-key-lg-form [data-testid="stAlert"]{border-radius:12px!important}
@media (max-width:900px){
  .lg-marca img{position:relative;top:auto;left:auto;align-self:flex-start}.lg-meio{min-height:0}.st-key-lg-form{min-height:auto}
  .lg-marca{min-height:auto;padding:28px 24px}.lg-meio{margin:22px 0 0}.lg-meio h1{font-size:30px!important}
  .lg-item,.lg-rodape{display:none}.st-key-lg-form{padding:28px 20px 40px!important}
}
</style>
"""

_ICONES = {
    "envio": "<svg viewBox='0 0 24 24' fill='none' stroke='#fff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M3 7h11v10H3zM14 11h4l3 3v3h-7z'/><circle cx='7' cy='18' r='1.8'/><circle cx='17' cy='18' r='1.8'/></svg>",
    "devolucao": "<svg viewBox='0 0 24 24' fill='none' stroke='#fff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M9 14 4 9l5-5'/><path d='M4 9h10a6 6 0 0 1 0 12h-2'/></svg>",
    "pendencia": "<svg viewBox='0 0 24 24' fill='none' stroke='#fff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='4' y='4' width='16' height='16' rx='3'/><path d='M8 12l3 3 5-6'/></svg>",
}


@functools.lru_cache(maxsize=2)
def _b64(nome: str) -> str:
    caminho = os.path.join(_RAIZ, nome)
    if not os.path.exists(caminho):
        return ""
    with open(caminho, "rb") as f:
        return base64.b64encode(f.read()).decode()


def aplicar_css() -> None:
    st.html(CSS)


def tela_carregando() -> None:
    """Tela branca com a lebre da Loggi no meio enquanto o app processa.

    Usa o atributo que o Streamlit põe no app durante a execução
    (data-test-script-state="running"). Só aparece se demorar mais de ~0,4 s,
    para não piscar em cliques rápidos. Chamar no início de cada execução.
    """
    # O estilo é instalado UMA vez no <head> da página (via script num iframe
    # invisível). Se ficasse num st.html, o Streamlit reescreveria o bloco a cada
    # atualização e a animação recomeçaria do zero — a tela nunca apareceria.
    lebre = _b64("image_simbolo_lebre_azul.png")
    css = (
        "@keyframes lgCarregaIn{from{opacity:0}to{opacity:1}}"
        "@keyframes lgPulsa{0%,100%{transform:translate(-50%,-50%) scale(1)}50%{transform:translate(-50%,-50%) scale(1.07)}}"
        "[data-testid='stApp'][data-test-script-state='running']::after{content:'';position:fixed;inset:0;z-index:2147483000;"
        "background:#fff;opacity:0;pointer-events:none;animation:lgCarregaIn .25s ease .4s forwards}"
        "[data-testid='stApp'][data-test-script-state='running']::before{content:'';position:fixed;left:50%;top:50%;z-index:2147483001;"
        "width:68px;height:68px;border-radius:18px;background:#fff "
        f"url(data:image/png;base64,{lebre}) no-repeat center/36px;"
        "box-shadow:0 10px 34px rgba(0,39,102,.12);opacity:0;pointer-events:none;transform:translate(-50%,-50%);"
        "animation:lgCarregaIn .25s ease .4s forwards,lgPulsa 1.4s ease-in-out .65s infinite}"
        ".st-key-lg-carregando,[data-testid='stLayoutWrapper']:has(> .st-key-lg-carregando){display:none!important}"
    )
    js = (
        "<script>(function(){var d=window.parent.document;"
        "if(d.getElementById('lg-carregando'))return;"
        "var s=d.createElement('style');s.id='lg-carregando';"
        f"s.textContent={json.dumps(css)};d.head.appendChild(s);}})();</script>"
    )
    with st.container(key="lg-carregando"):
        st.html("<style>.st-key-lg-carregando,[data-testid='stLayoutWrapper']:has(> .st-key-lg-carregando),[data-testid='stElementContainer']:has(.st-key-lg-carregando){display:none!important}</style>")
        st.iframe(js, height=1)  # fica escondido; só roda o script


def painel_marca() -> None:
    logo = _b64("image_loggi_branco.png")
    img = f'<img src="data:image/png;base64,{logo}" alt="Loggi">' if logo else "<b style='font-size:30px'>loggi</b>"
    itens = [
        ("envio", "Envios de insumos para a sua base, dia a dia"),
        ("devolucao", "Devoluções com romaneio e QR Code"),
        ("pendencia", "Pendências e cobranças em um só lugar"),
    ]
    st.markdown(
        f"<div class='lg-marca'>{img}<div class='lg-meio'><span class='lg-tag'>Gestão de insumos</span>"
        "<h1>Portal Leves</h1>"
        "<p>O canal entre a Loggi e as bases Leve para acompanhar sacas, gaylords e pallets.</p>"
        + "".join(f"<div class='lg-item'><span>{_ICONES[i]}</span>{t}</div>" for i, t in itens)
        + "</div><div class='lg-rodape'>Portal LEVES · Loggi</div></div>",
        unsafe_allow_html=True,
    )


def cabecalho(titulo: str, sub: str) -> None:
    st.markdown(f"<div class='lg-ola'>{titulo}</div><div class='lg-sub'>{sub}</div>", unsafe_allow_html=True)
