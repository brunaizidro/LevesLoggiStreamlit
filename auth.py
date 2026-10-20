"""
auth.py — Autenticação do Portal LEVES

Padrão de senha:
    SHA-256(salt + senha)

Compatível com a estrutura da aba Usuarios:
    usuario, senha_hash, salt, destino, nome, perfil, ativo,
    criado_em, email, primeiro_acesso, codigo_recuperacao_hash,
    codigo_expira_em
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import unicodedata
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from html import escape

import data_extraction as sheets
import emailer


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
    """Mesmo padrão utilizado pelo portal: SHA-256(salt + senha)."""
    return hashlib.sha256((salt + senha).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# NORMALIZAÇÃO
# ---------------------------------------------------------------------------

def normalizar(v) -> str:
    s = "" if v is None else str(v)
    s = s.strip().lower()
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


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
    """Retorna o dicionário do usuário quando válido; caso contrário, None."""
    usuario = (usuario or "").strip().lower()

    if not usuario or senha is None:
        return None

    try:
        sheets.ler_usuarios.clear()
    except Exception:
        pass

    u = buscar_usuario(usuario)
    if not u or not u.get("ativo"):
        return None

    salt = str(u.get("salt", ""))
    senha_hash = str(u.get("senha_hash", ""))

    if not salt or not senha_hash:
        return None

    calculado = hash_senha(senha, salt)
    if not hmac.compare_digest(calculado, senha_hash):
        return None

    u["perfil"] = normalizar_perfil(u.get("perfil", ""))
    return u


def diagnosticar_login(
    usuario: str,
    senha: str,
) -> tuple[bool, str, dict | None]:
    """Diagnóstico de login; não deve ser usado para liberar acesso."""
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
        return False, f"Não foi possível acessar a base de usuários: {e}", None

    u = None
    for item in usuarios:
        if str(item.get("usuario", "")).strip().lower() == usuario:
            u = item
            break

    if not u:
        return False, f'O usuário "{usuario_original}" não foi encontrado na aba Usuarios.', None
    if not u.get("ativo"):
        return False, "O usuário está cadastrado, mas está INATIVO.", u

    salt = str(u.get("salt", "")).strip()
    senha_hash = str(u.get("senha_hash", "")).strip()

    if not salt:
        return False, "O usuário está sem SALT na coluna C.", u
    if not senha_hash:
        return False, "O usuário está sem SENHA_HASH na coluna B.", u

    calculado = hash_senha(senha, salt)
    if not hmac.compare_digest(calculado, senha_hash):
        return False, "A senha informada não corresponde à senha cadastrada.", u

    u["perfil"] = normalizar_perfil(u.get("perfil", ""))
    return True, "Login validado com sucesso.", u


# ---------------------------------------------------------------------------
# ALTERAR SENHA
# ---------------------------------------------------------------------------

def alterar_senha(usuario: str, nova_senha: str) -> tuple[bool, str]:
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
    novo_hash = hash_senha(nova_senha, novo_salt)
    sheets.atualizar_senha_usuario(u["linha"], novo_hash, novo_salt)

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

    if perfil in (PERFIL_ADM, PERFIL_RECEB) and not destino:
        destino = "*"

    if not usuario or not senha or not destino:
        return False, "Usuário, senha e destino são obrigatórios."
    if " " in usuario:
        return False, "O usuário não pode conter espaços."
    if len(senha) < 6:
        return False, "A senha deve ter pelo menos 6 caracteres."
    if email and ("@" not in email or "." not in email.split("@")[-1]):
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


# ---------------------------------------------------------------------------
# RECUPERAÇÃO DE SENHA
# ---------------------------------------------------------------------------

def _enviar_email_recuperacao(
    destinatario: str,
    nome: str,
    codigo: str,
) -> None:
    """
    Envia o código usando a configuração SMTP da aba Config do portal.
    A recuperação é enviada somente ao usuário, sem cópia do código para terceiros.
    """
    destinatario = (destinatario or "").strip()
    if not destinatario or "@" not in destinatario:
        raise RuntimeError("O e-mail cadastrado para recuperação é inválido.")

    # Reutiliza a configuração SMTP já usada pelos outros e-mails do portal.
    cfg = emailer.config_smtp()
    obrigatorios = ("smtp_host", "smtp_port", "smtp_user", "smtp_from")
    faltantes = [k for k in obrigatorios if not str(cfg.get(k, "")).strip()]
    if faltantes:
        raise RuntimeError(
            "SMTP não configurado na aba Config. Verifique: "
            + ", ".join(faltantes)
        )

    corpo_html = f"""
    <div style="font-family:Arial,sans-serif;color:#172033;max-width:560px;margin:auto">
      <div style="font-size:24px;font-weight:800;color:#0067fc">loggi</div>
      <div style="color:#6e6e6e;letter-spacing:2px;text-transform:uppercase;font-size:11px;margin:4px 0 20px">Portal LEVES</div>
      <p>Olá, {escape(nome or "usuário")}!</p>
      <p>Recebemos uma solicitação para redefinir sua senha do Portal LEVES.</p>
      <p>Seu código de recuperação é:</p>
      <div style="font-size:30px;font-weight:bold;letter-spacing:7px;color:#0067fc;padding:12px 0">{escape(codigo)}</div>
      <p>O código é válido por 15 minutos e pode ser utilizado uma única vez.</p>
      <p>Se você não solicitou a redefinição, ignore este e-mail.</p>
      <p style="color:#6e6e6e;font-size:12px;margin-top:24px">Portal LEVES · Loggi</p>
    </div>
    """

    remetente = str(cfg.get("smtp_from", "")).strip() or str(cfg.get("smtp_user", "")).strip()
    msg = EmailMessage()
    msg["Subject"] = "Portal LEVES — Recuperação de senha"
    msg["From"] = remetente
    msg["To"] = destinatario
    msg.set_content(
        f"Olá, {nome or 'usuário'}!\n\n"
        "Recebemos uma solicitação para redefinir sua senha do Portal LEVES.\n\n"
        f"Seu código de recuperação é: {codigo}\n\n"
        "O código é válido por 15 minutos e pode ser utilizado uma única vez.\n"
        "Se você não solicitou a redefinição, ignore este e-mail.\n"
    )
    msg.add_alternative(corpo_html, subtype="html")

    server = None
    try:
        # A função de conexão é a mesma usada pelo emailer.py.
        server = emailer._abrir_conexao(cfg)
        recusados = server.send_message(
            msg,
            from_addr=remetente,
            to_addrs=[destinatario],
        )
        if recusados:
            raise RuntimeError(f"Servidor recusou o destinatário: {recusados}")
    except Exception as e:
        raise RuntimeError(f"Falha no SMTP ao enviar para {destinatario}: {e}") from e
    finally:
        if server is not None:
            try:
                server.quit()
            except Exception:
                pass



def buscar_usuario_por_email(email: str) -> dict | None:
    """Localiza uma conta ativa pelo e-mail cadastrado."""
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        return None

    try:
        sheets.ler_usuarios.clear()
    except Exception:
        pass

    encontrados = [
        u for u in sheets.ler_usuarios()
        if u.get("ativo")
        and str(u.get("email", "")).strip().lower() == email
    ]
    return encontrados[0] if len(encontrados) == 1 else None


def solicitar_recuperacao_por_email(email: str) -> tuple[bool, str, str]:
    """Solicita recuperação a partir do e-mail cadastrado."""
    u = buscar_usuario_por_email(email)
    mensagem = (
        "Se houver uma conta ativa vinculada a esse e-mail, "
        "enviaremos um código de recuperação."
    )
    if not u:
        return True, mensagem, ""

    ok, retorno = solicitar_recuperacao(u["usuario"])
    return ok, retorno, u["usuario"]


def solicitar_recuperacao(usuario: str) -> tuple[bool, str]:
    usuario = (usuario or "").strip().lower()
    u = buscar_usuario(usuario)

    mensagem = (
        "Se os dados informados forem válidos, enviaremos um código de "
        "recuperação para o e-mail cadastrado."
    )

    # Resposta genérica para não revelar se o login existe.
    if not u or not u.get("ativo") or not u.get("email"):
        return True, mensagem

    codigo = f"{secrets.randbelow(1_000_000):06d}"
    codigo_hash = hash_senha(codigo, u["salt"])
    expira_em = (
        datetime.now(timezone.utc) + timedelta(minutes=15)
    ).isoformat()

    # Grava o código para que possa ser validado no fluxo de redefinição.
    sheets.salvar_codigo_recuperacao(u["linha"], codigo_hash, expira_em)

    try:
        _enviar_email_recuperacao(
            u["email"],
            u.get("nome", ""),
            codigo,
        )
    except Exception:
        # Invalida o código caso o envio falhe, para não deixar código inutilizável ativo.
        try:
            sheets.limpar_codigo_recuperacao(u["linha"])
        except Exception:
            pass
        raise

    return True, mensagem


def redefinir_senha_com_codigo(
    usuario: str,
    codigo: str,
    nova_senha: str,
) -> tuple[bool, str]:
    usuario = (usuario or "").strip().lower()
    codigo = (codigo or "").strip()
    nova_senha = nova_senha or ""

    if len(codigo) != 6 or not codigo.isdigit():
        return False, "Digite o código de 6 dígitos."
    if len(nova_senha) < 6:
        return False, "A nova senha deve ter pelo menos 6 caracteres."

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

    calculado = hash_senha(codigo, u["salt"])
    if not hmac.compare_digest(calculado, codigo_hash):
        return False, "Código inválido ou expirado."

    novo_salt = gerar_salt()
    novo_hash = hash_senha(nova_senha, novo_salt)
    sheets.atualizar_senha_usuario(u["linha"], novo_hash, novo_salt)
    sheets.limpar_codigo_recuperacao(u["linha"])

    return True, "Senha redefinida com sucesso."
