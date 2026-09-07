import textwrap
import streamlit as st

class PageStyler:
    def __init__(self):
        pass

    def apply_general_css(self):
        css = textwrap.dedent("""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
        :root{--leves-azul:#0067fc;--leves-fundo:#f7f9fc;--leves-borda:#e5eaf1;--leves-texto:#172033;--leves-cinza:#697587;--leves-cinza-claro:#8a95a5}
        html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"],section.main{background:var(--leves-fundo)!important}
        [data-testid="stHeader"],[data-testid="stToolbar"]{display:none!important}
        [data-testid="stAppViewBlockContainer"]{max-width:100%!important;padding:12px 50px 40px!important}
        body,p,li,input,textarea,label,small,button,select,[data-baseweb],[data-testid="stMarkdownContainer"]{font-family:Montserrat,sans-serif!important}
        p{font-size:14px;color:var(--leves-cinza)}
        h2,.stSubheader{color:var(--leves-texto)!important;font-family:Montserrat,sans-serif!important;font-size:32px!important;line-height:1.15!important;font-weight:800!important;letter-spacing:-1px!important;margin-top:0!important;margin-bottom:7px!important}
        h3{color:var(--leves-texto)!important;font-family:Montserrat,sans-serif!important;font-size:20px!important;font-weight:700!important}
        h4{color:#253044!important;font-family:Montserrat,sans-serif!important;font-size:15px!important;font-weight:700!important}
        .custom-text{color:var(--leves-cinza)!important;font-family:Montserrat,sans-serif!important;font-size:14px!important;line-height:1.6!important;text-align:left!important;margin-bottom:18px!important}
        .subtitle{color:#253044!important;font-family:Montserrat,sans-serif!important;font-size:15px!important;font-weight:700!important;margin:4px 0 10px!important}
        div[data-testid="stHorizontalBlock"]{gap:16px}
        [data-baseweb="input"]>div,[data-baseweb="textarea"]>div,[data-baseweb="select"]>div{border-color:#dfe5ed!important;border-radius:10px!important;background:#fff!important;box-shadow:none!important}
        [data-baseweb="input"]>div:focus-within,[data-baseweb="textarea"]>div:focus-within,[data-baseweb="select"]>div:focus-within{border-color:#b9c7d8!important;box-shadow:0 0 0 1px rgba(0,103,252,.08)!important}
        [data-testid="stWidgetLabel"] p,[data-testid="stTextInput"] label,[data-testid="stNumberInput"] label,[data-testid="stSelectbox"] label,[data-testid="stMultiSelect"] label,[data-testid="stTextArea"] label,[data-testid="stFileUploader"] label{color:#536074!important;font-size:12px!important;font-weight:600!important}
        [data-testid="stButton"] button,[data-testid="stDownloadButton"] button,[data-testid="stFormSubmitButton"] button{border-radius:10px!important;font-family:Montserrat,sans-serif!important;font-weight:700!important;min-height:40px!important}
        [data-testid="stButton"] button[kind="primary"],[data-testid="stFormSubmitButton"] button[kind="primary"]{background:var(--leves-azul)!important;border-color:var(--leves-azul)!important}
        [data-testid="stVerticalBlockBorderWrapper"]{background:#fff!important;border:1px solid var(--leves-borda)!important;border-radius:16px!important;box-shadow:0 5px 18px rgba(23,32,51,.035)!important}
        [data-testid="stForm"]{background:#fff!important;border:1px solid var(--leves-borda)!important;border-radius:16px!important;padding:20px!important;box-shadow:0 5px 18px rgba(23,32,51,.035)!important}
        [data-testid="stExpander"]{border:1px solid var(--leves-borda)!important;border-radius:14px!important;background:#fff!important;overflow:hidden!important}
        [data-testid="stExpander"] summary{color:#334056!important;font-family:Montserrat,sans-serif!important;font-weight:700!important}
        [data-testid="stMetric"]{background:#fff!important;border:1px solid var(--leves-borda)!important;border-radius:16px!important;padding:15px 17px 14px!important;min-height:96px!important;box-shadow:0 5px 18px rgba(23,32,51,.035)!important}
        [data-testid="stMetricLabel"]{color:#788497!important;font-size:11px!important;font-weight:700!important;text-transform:uppercase!important;letter-spacing:.45px!important}
        [data-testid="stMetricValue"]{color:var(--leves-texto)!important;font-size:28px!important;font-weight:700!important}
        [data-testid="stMetricDelta"]{font-size:10px!important}
        [data-testid="stDataFrame"]{border:1px solid var(--leves-borda)!important;border-radius:14px!important;overflow:hidden!important;background:#fff!important}
        [data-testid="stAlert"]{border-radius:12px!important;font-family:Montserrat,sans-serif!important}
        hr{border-color:var(--leves-borda)!important}
        [data-testid="stFileUploader"] section{border:1px dashed #cfd8e5!important;border-radius:12px!important;background:#fff!important}
        [data-testid="stCheckbox"] label p{color:#536074!important;font-size:13px!important;font-weight:500!important}
        [data-testid="stSidebar"]{background-color:var(--leves-azul)!important}
        [data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,[data-testid="stSidebar"] li,[data-testid="stSidebar"] p{color:#fff}
        @media(max-width:900px){[data-testid="stAppViewBlockContainer"]{padding-left:20px!important;padding-right:20px!important}h2,.stSubheader{font-size:29px!important}}
        </style>
        """)
        st.html(css)

    def apply_sidebar_css(self, image_base64):
        css = textwrap.dedent("""
        <style>
        [data-testid="stSidebar"]{background-color:#0067fc!important}
        [data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,[data-testid="stSidebar"] li,[data-testid="stSidebar"] p{color:#fff!important}
        </style>
        """)
        st.html(css)
