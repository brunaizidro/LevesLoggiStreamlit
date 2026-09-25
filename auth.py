"""
auth.py — Autenticação do Portal LEVES

Padrão de senha:
    SHA-256(salt + senha)

Compatível com a estrutura da aba Usuarios:
    usuario
    senha_hash
    salt
    destino
    nome
    perfil
    ativo
    criado_em
    email
    primeiro_acesso
    codigo_recuperacao_hash
    codigo_expira_em
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import smtplib
import unicodedata

from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

import streamlit as st
import data_extraction as sheets


# ---------------------------------------------------------------------------
# PERFIS
# ---------------------------------------------------------------------------

PERFIL_ADM = "admin"
PERFIL_OP = "operacao"
PERFIL_RECEB = "recebimento"
PERFIL_GDL = "gdl"

PERFIS_VALIDOS = (
    PERFIL_ADM,
    PERFIL_OP,
    PERFIL_RECEB,
    PERFIL_GDL,
)


# ---------------------------------------------------------------------------
# SENHA
# ---------------------------------------------------------------------------

def gerar_salt() -> str:
    return os.urandom(16).hex()


def hash_senha(senha: str, salt: str) -> str:
    """
    Mesmo padrão utilizado pelo portal:
    SHA-256(salt + senha)
    """
    return hashlib.sha256(
        (salt + senha).encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------------------
# NORMALIZAÇÃO
# ---------------------------------------------------------------------------

def normalizar(v) -> str:
    s = "" if v is None else str(v)
    s = s.strip().lower()

    s = unicodedata.normalize("NFD", s)

    return "".join(
        c for c in s
        if unicodedata.category(c) != "Mn"
    )


def normalizar_perfil(v) -> str:
    s = str(v or "").strip().lower()

    if s in ("admin", "administrador"):
        return PERFIL_ADM

    if s in ("recebimento", "recebedor"):
        return PERFIL_RECEB

    if s in ("gdl", "g.d.l"):
        return PERFIL_GDL

    return PERFIL_OP


# ---------------------------------------------------------------------------
# USUÁRIO
# ---------------------------------------------------------------------------

def buscar_usuario(usuario: str) -> dict | None:
    usuario = (usuario or "").strip().lower()

    if not usuario:
        return None

    for u in sheets.ler_usuarios():
        if u["usuario"] == usuario:
            return u

    return None


# ---------------------------------------------------------------------------
# AUTENTICAÇÃO
# ---------------------------------------------------------------------------

def autenticar(usuario: str, senha: str) -> dict | None:
    """
    Autenticação normal.

    Retorna:
        dict do usuário quando válido
        None quando inválido
    """

    usuario = (usuario or "").strip().lower()

    if not usuario or senha is None:
        return None

    # Garante que alterações recentes na planilha sejam lidas.
    try:
        sheets.ler_usuarios.clear()
    except Exception:
        pass

    u = buscar_usuario(usuario)

    if not u:
        return None

    if not u.get("ativo"):
        return None

    salt = str(u.get("salt", ""))
    senha_hash = str(u.get("senha_hash", ""))

    if not salt or not senha_hash:
        return None

    calculado = hash_senha(senha, salt)

    if not hmac.compare_digest(
        calculado,
        senha_hash,
    ):
        return None

    u["perfil"] = normalizar_perfil(
        u.get("perfil", "")
    )

    return u


def diagnosticar_login(
    usuario: str,
    senha: str,
) -> tuple[bool, str, dict | None]:
    """
    Versão para diagnóstico.

    Não deve ser usada para liberar acesso.
    Serve para identificar por que o login falhou.
    """

    usuario_original = usuario
    usuario = (usuario or "").strip().lower()

    if not usuario:
        return False, "Digite o usuário.", None

    if senha is None or senha == "":
        return False, "Digite a senha.", None

    try:
        sheets.ler_usuarios.clear()
    except Exception:
        pass

    try:
        usuarios = sheets.ler_usuarios()
    except Exception as e:
        return (
            False,
            f"Não foi possível acessar a base de usuários: {e}",
            None,
        )

    u = None

    for item in usuarios:
        if str(item.get("usuario", "")).strip().lower() == usuario:
            u = item
            break

    if not u:
        return (
            False,
            f'O usuário "{usuario_original}" não foi encontrado na aba Usuarios.',
            None,
        )

    if not u.get("ativo"):
        return (
            False,
            "O usuário está cadastrado, mas está INATIVO.",
            u,
        )

    salt = str(u.get("salt", "")).strip()
    senha_hash = str(u.get("senha_hash", "")).strip()

    if not salt:
        return (
            False,
            "O usuário está sem SALT na coluna C.",
            u,
        )

    if not senha_hash:
        return (
            False,
            "O usuário está sem SENHA_HASH na coluna B.",
            u,
        )

    calculado = hash_senha(senha, salt)

    if not hmac.compare_digest(
        calculado,
        senha_hash,
    ):
        return (
            False,
            "A senha informada não corresponde à senha cadastrada.",
            u,
        )

    u["perfil"] = normalizar_perfil(
        u.get("perfil", "")
    )

    return True, "Login validado com sucesso.", u


# ---------------------------------------------------------------------------
# ALTERAR SENHA
# ---------------------------------------------------------------------------

def alterar_senha(
    usuario: str,
    nova_senha: str,
) -> tuple[bool, str]:

    usuario = (usuario or "").strip().lower()
    nova_senha = nova_senha or ""

    if not usuario:
        return False, "Usuário inválido."

    if not nova_senha:
        return False, "Digite uma nova senha."

    if len(nova_senha) < 6:
        return False, "A senha deve ter pelo menos 6 caracteres."

    u = buscar_usuario(usuario)

    if not u:
        return False, "Usuário não encontrado."

    novo_salt = gerar_salt()

    novo_hash = hash_senha(
        nova_senha,
        novo_salt,
    )

    sheets.atualizar_senha_usuario(
        u["linha"],
        novo_hash,
        novo_salt,
    )

    return True, "Senha alterada com sucesso."


# ---------------------------------------------------------------------------
# CRIAR USUÁRIO
# ---------------------------------------------------------------------------

def criar_usuario(
    usuario,
    senha,
    destino,
    nome,
    perfil=PERFIL_OP,
    email="",
) -> tuple[bool, str]:

    usuario = (usuario or "").strip().lower()
    senha = senha or ""
    destino = (destino or "").strip()
    nome = (nome or "").strip() or usuario
    email = (email or "").strip()

    perfil = normalizar_perfil(perfil)

    # Admin / recebimento podem usar *
    if perfil in (
        PERFIL_ADM,
        PERFIL_RECEB,
    ) and not destino:
        destino = "*"

    if not usuario or not senha or not destino:
        return (
            False,
            "Usuário, senha e destino são obrigatórios.",
        )

    if " " in usuario:
        return (
            False,
            "O usuário não pode conter espaços.",
        )

    if len(senha) < 6:
        return (
            False,
            "A senha deve ter pelo menos 6 caracteres.",
        )

    if email and (
        "@" not in email
        or "." not in email.split("@")[-1]
    ):
        return False, "E-mail inválido."

    if buscar_usuario(usuario):
        return (
            False,
            "Já existe um usuário com esse login.",
        )

    salt = gerar_salt()

    sheets.inserir_usuario(
        usuario,
        hash_senha(senha, salt),
        salt,
        destino,
        nome,
        perfil,
        email=email,
    )

    return (
        True,
        f'Usuário "{usuario}" criado com sucesso.',
    )


# ---------------------------------------------------------------------------
# RECUPERAÇÃO DE SENHA
# ---------------------------------------------------------------------------

def _config_email():
    cfg = (
        st.secrets.get("email", {})
        if hasattr(st, "secrets")
        else {}
    )

    return {
        "host": str(
            cfg.get("smtp_host", "")
        ).strip(),

        "port": int(
            cfg.get("smtp_port", 587)
        ),

        "user": str(
            cfg.get("smtp_user", "")
        ).strip(),

        "password": str(
            cfg.get("smtp_password", "")
        ),

        "from": str(
            cfg.get("smtp_from", "")
        ).strip(),

        "use_ssl": str(
            cfg.get("smtp_ssl", "false")
        ).lower() in (
            "1",
            "true",
            "sim",
            "yes",
        ),
    }


def _enviar_email_recuperacao(
    destinatario: str,
    nome: str,
    codigo: str,
):

    cfg = _config_email()

    if not all(
        (
            cfg["host"],
            cfg["user"],
            cfg["password"],
            cfg["from"],
        )
    ):
        raise RuntimeError(
            "Configuração de e-mail não encontrada."
        )

    msg = EmailMessage()

    msg["Subject"] = (
        "Portal LEVES — Recuperação de senha"
    )

    msg["From"] = cfg["from"]
    msg["To"] = destinatario

    msg.set_content(
        f"Olá, {nome or 'usuário'}!\n\n"
        "Recebemos uma solicitação para redefinir "
        "a senha do Portal LEVES.\n\n"
        f"Seu código de recuperação é: {codigo}\n\n"
        "O código é válido por 15 minutos e pode "
        "ser usado uma única vez.\n\n"
        "Portal LEVES · Loggi"
    )

    if cfg["use_ssl"] or cfg["port"] == 465:

        with smtplib.SMTP_SSL(
            cfg["host"],
            cfg["port"],
            timeout=20,
        ) as smtp:

            smtp.login(
                cfg["user"],
                cfg["password"],
            )

            smtp.send_message(msg)

    else:

        with smtplib.SMTP(
            cfg["host"],
            cfg["port"],
            timeout=20,
        ) as smtp:

            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()

            smtp.login(
                cfg["user"],
                cfg["password"],
            )

            smtp.send_message(msg)


def solicitar_recuperacao(
    usuario: str,
) -> tuple[bool, str]:

    usuario = (
        usuario or ""
    ).strip().lower()

    u = buscar_usuario(usuario)

    mensagem = (
        "Se os dados informados forem válidos, "
        "enviaremos um código de recuperação "
        "para o e-mail cadastrado."
    )

    if (
        not u
        or not u.get("ativo")
        or not u.get("email")
    ):
        return True, mensagem

    codigo = (
        f"{secrets.randbelow(1_000_000):06d}"
    )

    codigo_hash = hash_senha(
        codigo,
        u["salt"],
    )

    expira_em = (
        datetime.now(timezone.utc)
        + timedelta(minutes=15)
    ).isoformat()

    sheets.salvar_codigo_recuperacao(
        u["linha"],
        codigo_hash,
        expira_em,
    )

    _enviar_email_recuperacao(
        u["email"],
        u.get("nome", ""),
        codigo,
    )

    return True, mensagem


def redefinir_senha_com_codigo(
    usuario: str,
    codigo: str,
    nova_senha: str,
) -> tuple[bool, str]:

    usuario = (
        usuario or ""
    ).strip().lower()

    codigo = (
        codigo or ""
    ).strip()

    nova_senha = nova_senha or ""

    if (
        len(codigo) != 6
        or not codigo.isdigit()
    ):
        return (
            False,
            "Digite o código de 6 dígitos.",
        )

    if len(nova_senha) < 6:
        return (
            False,
            "A nova senha deve ter pelo menos 6 caracteres.",
        )

    u = buscar_usuario(usuario)

    if not u or not u.get("ativo"):
        return (
            False,
            "Código inválido ou expirado.",
        )

    codigo_hash = u.get(
        "codigo_recuperacao_hash",
        "",
    )

    expira_em = u.get(
        "codigo_expira_em",
        "",
    )

    if not codigo_hash or not expira_em:
        return (
            False,
            "Código inválido ou expirado.",
        )

    try:

        expira = datetime.fromisoformat(
            str(expira_em).replace(
                "Z",
                "+00:00",
            )
        )

        if expira.tzinfo is None:
            expira = expira.replace(
                tzinfo=timezone.utc
            )

    except ValueError:

        return (
            False,
            "Código inválido ou expirado.",
        )

    if datetime.now(timezone.utc) > expira:

        sheets.limpar_codigo_recuperacao(
            u["linha"]
        )

        return (
            False,
            "Código inválido ou expirado.",
        )

    calc = hash_senha(
        codigo,
        u["salt"],
    )

    if not hmac.compare_digest(
        calc,
        codigo_hash,
    ):
        return (
            False,
            "Código inválido ou expirado.",
        )

    novo_salt = gerar_salt()

    novo_hash = hash_senha(
        nova_senha,
        novo_salt,
    )

    sheets.atualizar_senha_usuario(
        u["linha"],
        novo_hash,
        novo_salt,
    )

    sheets.limpar_codigo_recuperacao(
        u["linha"]
    )

    return (
        True,
        "Senha redefinida com sucesso.",
    )
