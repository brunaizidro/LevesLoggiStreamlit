"""
page_2.py — Administração de usuários (somente admin).

Cria novos usuários e ativa/desativa os existentes. Escreve na aba Usuarios
pela camada de extração; o login/hash é responsabilidade de auth.py.
"""

from __future__ import annotations

import io
import html

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import auth
import data_extraction as dados
import data_processing as dp

TEMPLATE_COLS = ["nome", "usuario", "senha", "destino", "perfil", "email"]


def _importar_massa(eh_gdl: bool = False):
    """Importação de usuários via CSV (com template, prévia e relatório)."""
    st.markdown("<p class='subtitle'>Importar em massa (CSV)</p>", unsafe_allow_html=True)
    st.caption(
        "Colunas: nome, usuario, senha, destino, perfil, email. "
        + (
            "Para GDL, o perfil deve ser Operação."
            if eh_gdl
            else "Perfil aceita: operacao, admin, recebimento ou gdl (padrão operacao)."
        )
    )

    modelo = pd.DataFrame([
        {"nome": "Base São Paulo", "usuario": "base_sp", "senha": "trocar123",
         "destino": "GJM", "perfil": "operacao", "email": "base_sp@empresa.com"},
    ], columns=TEMPLATE_COLS)
    st.download_button("Baixar modelo (CSV)", modelo.to_csv(index=False).encode("utf-8-sig"),
                       file_name="modelo_usuarios.csv", mime="text/csv", key="tpl_users")

    up = st.file_uploader("Arraste o CSV preenchido", type=["csv"], key="up_users")
    if not up:
        return

    try:
        raw = up.getvalue()
        df = None
        for sep in (",", ";", "\t"):
            try:
                cand = pd.read_csv(io.BytesIO(raw), sep=sep, dtype=str).fillna("")
                if cand.shape[1] >= 4:
                    df = cand
                    break
            except Exception:  # noqa: BLE001
                continue
        if df is None:
            st.error("Não consegui ler o CSV. Use o modelo como base.")
            return
    except Exception as e:  # noqa: BLE001
        st.error(f"Falha ao ler o arquivo: {e}")
        return

    df.columns = [str(c).strip().lower() for c in df.columns]
    faltando = [c for c in ("usuario", "senha", "destino") if c not in df.columns]
    if faltando:
        st.error("Faltam colunas obrigatórias: " + ", ".join(faltando))
        return

    st.markdown("**Prévia**")
    st.dataframe(df.head(20), width="stretch", hide_index=True)
    st.caption(f"{len(df)} linha(s) no arquivo.")

    if st.button("Importar usuários", type="primary", key="do_import"):
        ocupados = {u["usuario"] for u in dados.ler_usuarios()}
        rows, erros = [], []
        for i, r in df.iterrows():
            perfil = auth.normalizar_perfil(r.get("perfil", ""))
            if eh_gdl and perfil != auth.PERFIL_OP:
                erros.append({
                    "linha": int(i) + 2,
                    "usuario": r.get("usuario", ""),
                    "motivo": "GDL só pode cadastrar usuários com perfil Operação.",
                })
                continue
            row, err = auth.preparar_usuario_row(
                r.get("usuario", ""), r.get("senha", ""), r.get("destino", ""),
                r.get("nome", ""), perfil, r.get("email", ""), ocupados)
            if err:
                erros.append({"linha": int(i) + 2, "usuario": r.get("usuario", ""), "motivo": err})
            else:
                rows.append(row)
                ocupados.add(row[0])

        if rows:
            dados.inserir_usuarios_lote(rows)
        st.success(f"{len(rows)} usuário(s) importado(s).")
        if erros:
            st.warning(f"{len(erros)} linha(s) ignorada(s):")
            st.dataframe(pd.DataFrame(erros), width="stretch", hide_index=True)
        if rows:
            st.rerun()


def page_2():
    user = st.session_state.get("usuario") or {}
    eh_admin = user.get("perfil") == auth.PERFIL_ADM
    eh_gdl = user.get("perfil") == auth.PERFIL_GDL

    if not (eh_admin or eh_gdl):
        st.error("Acesso não autorizado.")
        return

    titulo = "Administração de usuários" if eh_admin else "Usuários de Operação"
    subtitulo = ("Cadastre, consulte e gerencie os acessos ao Portal Leves." if eh_admin
                 else "Cadastre e gerencie os usuários vinculados à sua operação.")
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
        .modulo-header { font-family:'Montserrat',sans-serif !important; text-align:left; }
        .modulo-breadcrumb { color:#7B8798 !important; font-family:'Montserrat',sans-serif !important; font-size:11px !important; font-weight:600 !important; letter-spacing:.55px !important; margin:0 0 7px !important; }
        .modulo-title { color:#172B4D !important; font-family:'Montserrat',sans-serif !important; font-size:38px !important; line-height:1.18 !important; font-weight:800 !important; letter-spacing:-.8px !important; margin:0 !important; text-align:left !important; }
        .modulo-subtitle { color:#627895 !important; font-family:'Montserrat',sans-serif !important; font-size:16px !important; font-weight:600 !important; line-height:1.55 !important; margin:2px 0 18px !important; text-align:left !important; }
        /* Padronização da tabela de usuários com as demais tabelas do portal */
        [data-testid="stDataEditor"] {
            font-family:'Montserrat',sans-serif !important;
            --gdg-font-family: 'Montserrat', sans-serif;
            --gdg-header-font-style: 700 12px 'Montserrat', sans-serif;
            --gdg-header-background: #0756B8;
            --gdg-header-text: #FFFFFF;
            --gdg-header-border-color: #D6E5FA;
            --gdg-border-color: #D6E5FA;
            --gdg-cell-text: #183B6B;
            --gdg-bg-cell: #FFFFFF;
            --gdg-bg-cell-medium: #F1F6FD;
            --gdg-accent-color: #0866F5;
            border:1px solid #C8DDF8;
            border-radius:12px;
            overflow:hidden;
        }
        [data-testid="stDataEditor"] * {
            font-family:'Montserrat',sans-serif !important;
        }
        [data-testid="stDataEditor"] canvas {
            font-family:'Montserrat',sans-serif !important;
        }
        [data-testid="stTextInput"] label,
        [data-testid="stTextInput"] input {
            font-family:'Montserrat',sans-serif !important;
        }
        </style>
        <div class="modulo-header">
            <div class="modulo-breadcrumb">PORTAL LEVES &nbsp;/&nbsp; USUÁRIOS</div>
            <div class="modulo-title">{titulo}</div>
            <p class="modulo-subtitle">{subtitulo}</p>
        </div>
        """.replace("{titulo}", titulo).replace("{subtitulo}", subtitulo),
        unsafe_allow_html=True,
    )

    if eh_gdl:
        st.info("Perfil GDL: você pode cadastrar e ativar/desativar apenas usuários com perfil Operação.")

    with st.expander("📥 Importar usuários em massa (CSV)"):
        _importar_massa(eh_gdl=eh_gdl)

    esq, dir_ = st.columns([1, 1.4])

    with esq:
        st.markdown("<p class='subtitle'>Novo usuário</p>", unsafe_allow_html=True)
        # Destinos sugeridos a partir dos envios.
        df = dp.envios_df()
        destinos = sorted(df["destino"].unique()) if not df.empty else []
        with st.form("novo_user", clear_on_submit=True):
            nome = st.text_input("Nome da operação", placeholder="Ex.: Base São Paulo")
            usuario = st.text_input("Usuário (login)", placeholder="ex.: base_sp")
            senha = st.text_input("Senha", placeholder="mín. 6 caracteres")
            email = st.text_input("E-mail (para cobrança)", placeholder="ex.: base_sp@empresa.com")
            perfil_lbl = st.selectbox("Perfil", ["Operação"] if eh_gdl else ["Operação", "Administrador", "Recebimento", "GDL"])
            if destinos:
                destino = st.selectbox("Destino (da planilha)", options=[""] + destinos)
                destino_livre = st.text_input("...ou digite um destino novo")
                destino = destino_livre.strip() or destino
            else:
                destino = st.text_input("Destino (exato da planilha)")
            st.caption("Admin e Recebimento não usam destino. GDL deve ser vinculado ao destino/base correspondente.")
            criar = st.form_submit_button("Criar usuário", type="primary", width="stretch")

        if criar:
            perfil = {
                "Administrador": auth.PERFIL_ADM,
                "Recebimento": auth.PERFIL_RECEB,
                "GDL": auth.PERFIL_GDL,
            }.get(perfil_lbl, auth.PERFIL_OP)
            # Admin/Recebimento veem tudo — destino não é usado para filtro.
            if perfil in (auth.PERFIL_ADM, auth.PERFIL_RECEB, auth.PERFIL_GDL,
            ) and not destino.strip():
                destino = "*"
            ok, msg = auth.criar_usuario(usuario, senha, destino, nome, perfil, email=email)
            (st.success if ok else st.error)(msg)

    with dir_:
        st.markdown("<p class='subtitle'>Usuários cadastrados</p>", unsafe_allow_html=True)
        _tabela_usuarios(eh_gdl=eh_gdl)


PERFIL_LABEL = {"admin": "Admin", "recebimento": "Recebimento", "operacao": "Operação"}


def _tabela_usuarios(eh_gdl: bool = False):
    usuarios = dados.ler_usuarios()
    if eh_gdl:
        usuarios = [u for u in usuarios if u.get("perfil") == auth.PERFIL_OP]
    if not usuarios:
        st.info("Nenhum usuário cadastrado.")
        return

    logado = (st.session_state.get("usuario") or {}).get("usuario")
    linha_por_login = {u["usuario"]: u["linha"] for u in usuarios}
    orig_ativo = {u["usuario"]: bool(u["ativo"]) for u in usuarios}

    filtro = st.text_input("Buscar (nome, login, destino ou e-mail)", key="busca_users",
                           placeholder="digite para filtrar...")
    linhas = []
    for u in usuarios:
        alvo = f"{u['nome']} {u['usuario']} {u['destino']} {u.get('email','')}".lower()
        if filtro and filtro.strip().lower() not in alvo:
            continue
        linhas.append({
            "Nome": u["nome"], "Login": u["usuario"], "Destino": u["destino"],
            "E-mail": u.get("email") or "", "Perfil": PERFIL_LABEL.get(u["perfil"], "Operação"),
            "Ativo": bool(u["ativo"]),
        })
    if not linhas:
        st.caption("Nenhum usuário para o filtro.")
        return
    novos_status = {}

    # Tabela com checkbox integrado, cabeçalho contínuo e grade azul-clara.
    widths = [3.5, 1.15, 1.1, 3.0, 1.4, 0.7]
    with st.container(height=500, border=False, gap="none"):
        st.markdown("""
        <style>
        .usuarios-grid-header {
            background:#0067FC;color:#FFFFFF;font-family:'Montserrat',sans-serif;
            font-size:12px;font-weight:700;padding:11px 6px;text-align:center;
            min-height:42px;white-space:nowrap;display:flex;
            align-items:center;justify-content:center;line-height:1.2;
            border:1px solid #BFD7F5;
        }
        .usuarios-grid-cell {
            color:#172B4D;font-family:'Montserrat',sans-serif;font-size:12px;
            font-weight:600;padding:9px 8px;min-height:48px;
            border:1px solid #D6E5FA;display:flex;align-items:center;
            line-height:1.3;overflow-wrap:anywhere;word-break:normal;
            background:#FFFFFF;
        }
        .usuarios-grid-cell.alt {background:#F4F8FE;}
        .usuarios-grid-cell.nome,.usuarios-grid-cell.email {text-align:left;justify-content:flex-start;}
        .usuarios-grid-cell.centro {text-align:center;justify-content:center;white-space:nowrap;}
        [data-testid="stCheckbox"] {display:flex;justify-content:center!important;align-items:center;min-height:48px;width:100%;}
        [data-testid="stCheckbox"] > label {justify-content:center!important;width:100%;}
        [data-testid="stCheckbox"] > label > div:first-child {margin:0 auto!important;}
        </style>
        """, unsafe_allow_html=True)

        headers = ["Nome", "Login", "Destino", "E-mail", "Perfil", "Ativo"]
        hcols = st.columns(widths, gap="none")
        for col, label in zip(hcols, headers):
            col.markdown(f'<div class="usuarios-grid-header">{label}</div>', unsafe_allow_html=True)

        for idx, u in enumerate(usuarios):
            alt = " alt" if idx % 2 else ""
            cells = st.columns(widths, gap="none")
            values = [
                (u["nome"], "nome"),
                (u["usuario"], "centro"),
                (u["destino"], "centro"),
                (u.get("email") or "—", "email"),
                (PERFIL_LABEL.get(u["perfil"], "Operação"), "centro"),
            ]
            for col, (value, extra) in zip(cells[:5], values):
                safe_value = html.escape(str(value))
                col.markdown(
                    f'<div class="usuarios-grid-cell{alt} {extra}">{safe_value}</div>',
                    unsafe_allow_html=True,
                )
            novos_status[u["usuario"]] = cells[5].checkbox(
                "Ativo",
                value=bool(u["ativo"]),
                key=f"status_user_{u['usuario']}",
                label_visibility="collapsed",
            )

    c1, c2 = st.columns([1, 2])
    if c1.button("Salvar alterações", type="primary", width="stretch"):
        mudou, bloqueado = 0, False
        for login, novo in novos_status.items():
            if novo == orig_ativo.get(login):
                continue
            if login == logado:
                bloqueado = True
                continue
            dados.definir_ativo(linha_por_login[login], novo)
            mudou += 1
        if bloqueado:
            st.warning("Você não pode alterar o próprio status — ignorado.")
        if mudou:
            st.success(f"{mudou} alteração(ões) salva(s).")
            st.rerun()
        elif not bloqueado:
            st.info("Nenhuma alteração para salvar.")
