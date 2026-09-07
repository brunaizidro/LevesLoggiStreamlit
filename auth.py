"""
auth.py
Autenticação do Portal LEVES (versão Streamlit).

Compatível com o app em Apps Script: usa o MESMO esquema de hash
  senha_hash = SHA-256(salt + senha)  (hex)
com salt único por usuário.

Fluxo de senha:
- Usuário novo é criado com primeiro_acesso = TRUE.
- No primeiro login, o usuário é obrigado a criar uma nova senha.
- Após alterar a senha, primeiro_acesso passa para FALSE.
- A nova senha continua armazenada usando hash + salt.
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


PERFIL_ADM = "admin"
PERFIL_OP = "operacao"
PERFIL_RECEB = "recebimento"

PERFIS_VALIDOS = (
    PERFIL_ADM,
    PERFIL_OP,
    PERFIL_RECEB,
)


def gerar_salt() -> str:
    """Gera um salt aleatório e único para cada senha."""
    return os.urandom(16).hex()


def hash_senha(senha: str, salt: str) -> str:
    """
    Gera o hash da senha.

    Mantém compatibilidade com o Apps Script:
    SHA-256(salt + senha)
    """
    return hashlib.sha256(
        (salt + senha).encode("utf-8")
    ).hexdigest()


def normalizar(v) -> str:
    """trim + minúsculas + sem acento (para comparar destinos)."""
    s = "" if v is None else str(v)
    s = s.strip().lower()
    s = unicodedata.normalize("NFD", s)
    return "".join(
        c for c in s
        if unicodedata.category(c) != "Mn"
    )


def buscar_usuario(usuario: str) -> dict | None:
    """Busca um usuário pelo login."""
    usuario = (usuario or "").strip().lower()

    for u in sheets.ler_usuarios():
        if u["usuario"] == usuario:
            return u

    return None


def autenticar(usuario: str, senha: str) -> dict | None:
    """
    Retorna o usuário se as credenciais forem válidas
    e o usuário estiver ativo.
    """
    u = buscar_usuario(usuario)

    if not u or not u["ativo"]:
        return None

    calc = hash_senha(senha, u["salt"])

    if not hmac.compare_digest(
        calc,
        u["senha_hash"],
    ):
        return None

    return u


def alterar_senha(
    usuario: str,
    nova_senha: str,
) -> tuple[bool, str]:
    """
    Altera a senha do usuário.

    Gera um novo salt, cria um novo hash,
    atualiza a planilha e finaliza o primeiro acesso.
    """
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


def criar_usuario(
    usuario,
    senha,
    destino,
    nome,
    perfil=PERFIL_OP,
    email="",
) -> tuple[bool, str]:
    """Valida e cria um usuário. Todo usuário novo inicia em primeiro_acesso."""
    usuario = (usuario or "").strip().lower()
    senha = senha or ""
    destino = (destino or "").strip()
    nome = (nome or "").strip() or usuario
    email = (email or "").strip()
    perfil = perfil if perfil in PERFIS_VALIDOS else PERFIL_OP

    if not usuario or not senha or not destino:
        return False, "Usuário, senha e destino são obrigatórios."

    if " " in usuario:
        return False, "O usuário não pode conter espaços."

    if len(senha) < 6:
        return False, "A senha deve ter pelo menos 6 caracteres."

    if email and (
        "@" not in email
        or "." not in email.split("@")[-1]
    ):
        return False, "E-mail inválido."

    if buscar_usuario(usuario):
        return False, "Já existe um usuário com esse login."

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

    return True, f'Usuário "{usuario}" criado com sucesso.'


def preparar_usuario_row(
    usuario,
    senha,
    destino,
    nome,
    perfil,
    email,
    ocupados: set,
):
    """
    Valida um registro para importação em massa e devolve a linha pronta.

    Retorna (row, None) ou (None, erro). Não escreve nada.
    """
    from datetime import datetime

    usuario = str(usuario or "").strip().lower()
    senha = str(senha or "")
    destino = str(destino or "").strip()
    nome = str(nome or "").strip() or usuario
    email = str(email or "").strip()
    perfil = perfil if perfil in PERFIS_VALIDOS else PERFIL_OP

    if perfil in (PERFIL_ADM, PERFIL_RECEB) and not destino:
        destino = "*"

    if not usuario or not senha or not destino:
        return None, "usuário, senha e destino são obrigatórios"

    if " " in usuario:
        return None, "usuário não pode conter espaços"

    if len(senha) < 6:
        return None, "senha deve ter ao menos 6 caracteres"

    if email and (
        "@" not in email
        or "." not in email.split("@")[-1]
    ):
        return None, "e-mail inválido"

    if usuario in ocupados:
        return None, "login duplicado"

    salt = gerar_salt()

    row = [
        usuario,
        hash_senha(senha, salt),
        salt,
        destino,
        nome,
        perfil,
        "TRUE",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        email,
        "TRUE",
        "",
        "",
    ]

    return row, None



def _config_email():
    """Lê a configuração SMTP do Streamlit Secrets."""
    cfg = st.secrets.get("email", {}) if hasattr(st, "secrets") else {}
    return {
        "host": str(cfg.get("smtp_host", "")).strip(),
        "port": int(cfg.get("smtp_port", 587)),
        "user": str(cfg.get("smtp_user", "")).strip(),
        "password": str(cfg.get("smtp_password", "")),
        "from": str(cfg.get("smtp_from", "")).strip(),
        "use_ssl": str(cfg.get("smtp_ssl", "false")).lower() in ("1", "true", "sim", "yes"),
    }


def _enviar_email_recuperacao(destinatario: str, nome: str, codigo: str):
    """Envia o código de recuperação usando SMTP configurado nos Secrets."""
    cfg = _config_email()
    if not all((cfg["host"], cfg["user"], cfg["password"], cfg["from"])):
        raise RuntimeError(
            "Configuração de e-mail não encontrada. Configure a seção [email] no Streamlit Secrets."
        )

    msg = EmailMessage()
    msg["Subject"] = "Portal LEVES — Recuperação de senha"
    msg["From"] = cfg["from"]
    msg["To"] = destinatario
    msg.set_content(
        f"Olá, {nome or 'usuário'}!\n\n"
        "Recebemos uma solicitação para redefinir a senha do Portal LEVES.\n\n"
        f"Seu código de recuperação é: {codigo}\n\n"
        "O código é válido por 15 minutos e pode ser usado uma única vez.\n"
        "Se você não solicitou a recuperação, ignore este e-mail.\n\n"
        "Portal LEVES · Loggi"
    )

    if cfg["use_ssl"] or cfg["port"] == 465:
        with smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=20) as smtp:
            smtp.login(cfg["user"], cfg["password"])
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=20) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(cfg["user"], cfg["password"])
            smtp.send_message(msg)


def solicitar_recuperacao(usuario: str) -> tuple[bool, str]:
    """Gera e envia um código de recuperação para o e-mail cadastrado."""
    usuario = (usuario or "").strip().lower()
    u = buscar_usuario(usuario)

    # Resposta genérica para não revelar se um login existe.
    mensagem = "Se os dados informados forem válidos, enviaremos um código de recuperação para o e-mail cadastrado."

    if not u or not u.get("ativo") or not u.get("email"):
        return True, mensagem

    codigo = f"{secrets.randbelow(1_000_000):06d}"
    codigo_hash = hash_senha(codigo, u["salt"])
    expira_em = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()

    sheets.salvar_codigo_recuperacao(u["linha"], codigo_hash, expira_em)
    _enviar_email_recuperacao(u["email"], u.get("nome", ""), codigo)
    return True, mensagem


def redefinir_senha_com_codigo(usuario: str, codigo: str, nova_senha: str) -> tuple[bool, str]:
    """Valida o código de recuperação e define uma nova senha."""
    usuario = (usuario or "").strip().lower()
    codigo = (codigo or "").strip()
    nova_senha = nova_senha or ""

    if len(codigo) != 6 or not codigo.isdigit():
        return False, "Digite o código de 6 dígitos recebido por e-mail."
    if len(nova_senha) < 6:
        return False, "A senha deve ter pelo menos 6 caracteres."

    u = buscar_usuario(usuario)
    if not u or not u.get("ativo"):
        return False, "Código inválido ou expirado."

    codigo_hash = u.get("codigo_recuperacao_hash", "")
    expira_em = u.get("codigo_expira_em", "")
    if not codigo_hash or not expira_em:
        return False, "Código inválido ou expirado."

    try:
        expira = datetime.fromisoformat(str(expira_em).replace("Z", "+00:00"))
        if expira.tzinfo is None:
            expira = expira.replace(tzinfo=timezone.utc)
    except ValueError:
        return False, "Código inválido ou expirado."

    if datetime.now(timezone.utc) > expira:
        sheets.limpar_codigo_recuperacao(u["linha"])
        return False, "Código inválido ou expirado."

    calc = hash_senha(codigo, u["salt"])
    if not hmac.compare_digest(calc, codigo_hash):
        return False, "Código inválido ou expirado."

    novo_salt = gerar_salt()
    novo_hash = hash_senha(nova_senha, novo_salt)
    sheets.atualizar_senha_usuario(u["linha"], novo_hash, novo_salt)
    sheets.limpar_codigo_recuperacao(u["linha"])
    return True, "Senha redefinida com sucesso."

def normalizar_perfil(v) -> str:
    """Converte rótulos livres de perfil para o valor canônico."""
    s = str(v or "").strip().lower()

    if s in ("admin", "administrador"):
        return PERFIL_ADM

    if s in ("recebimento", "recebedor"):
        return PERFIL_RECEB

    return PERFIL_OP
