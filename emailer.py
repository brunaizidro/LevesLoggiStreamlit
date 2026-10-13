"""
emailer.py — envio de e-mail via SMTP (configurado pelo admin no app).
"""

from __future__ import annotations

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import data_extraction as dados

CAMPOS_OBRIGATORIOS = ["smtp_host", "smtp_port", "smtp_user", "smtp_from"]
LOGO_URL = "https://raw.githubusercontent.com/brunaizidro/LevesLoggiStreamlit/master/image_simbolo_lebre.png"
EMAIL_COPIA_FIXA = "materiais@loggi.com"


def config_smtp() -> dict:
    return dados.get_config()


def smtp_configurado() -> bool:
    c = config_smtp()
    return all(str(c.get(k, "")).strip() for k in CAMPOS_OBRIGATORIOS)


def _abrir_conexao(c: dict):
    host = str(c.get("smtp_host", "")).strip()
    port = int(str(c.get("smtp_port", "587")).strip() or 587)
    usar_tls = str(c.get("smtp_tls", "true")).strip().lower() in ("true", "1", "sim")
    if port == 465:
        server = smtplib.SMTP_SSL(host, port, timeout=20, context=ssl.create_default_context())
    else:
        server = smtplib.SMTP(host, port, timeout=20)
        if usar_tls:
            server.starttls(context=ssl.create_default_context())
    user = str(c.get("smtp_user", "")).strip()
    pwd = str(c.get("smtp_password", ""))
    if user:
        server.login(user, pwd)
    return server


def enviar_email(destinatario: str, assunto: str, corpo_html: str,
                 reply_to: str | None = None) -> tuple[bool, str]:
    """Envia HTML para a operação e sempre inclui materiais@loggi.com no CC e no envelope SMTP."""
    destinatario = (destinatario or "").strip()
    if not destinatario:
        return False, "Destinatário vazio."
    c = config_smtp()
    if not smtp_configurado():
        return False, "SMTP não configurado. Preencha em Configurações."

    remetente = str(c.get("smtp_from", "")).strip() or str(c.get("smtp_user", "")).strip()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = remetente
    msg["To"] = destinatario
    msg["Cc"] = EMAIL_COPIA_FIXA
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.attach(MIMEText(corpo_html, "html", "utf-8"))

    # O CC precisa estar também na lista de destinatários do SMTP.
    destinatarios_smtp = [destinatario]
    if EMAIL_COPIA_FIXA.lower() != destinatario.lower():
        destinatarios_smtp.append(EMAIL_COPIA_FIXA)

    server = None
    try:
        server = _abrir_conexao(c)
        resultado = server.sendmail(remetente, destinatarios_smtp, msg.as_string())
        server.quit()
        if resultado:
            return False, f"SMTP não aceitou todos os destinatários: {resultado}"
        return True, f"E-mail enviado para {destinatario}, com cópia para {EMAIL_COPIA_FIXA}."
    except Exception as e:
        if server is not None:
            try:
                server.quit()
            except Exception:
                pass
        return False, f"Falha ao enviar para {destinatario}: {e}"


def email_suporte() -> str:
    return str(config_smtp().get("email_suporte", "")).strip()


def enviar_duvida(nome: str, email_remetente: str, mensagem: str) -> tuple[bool, str]:
    nome = (nome or "").strip()
    email_remetente = (email_remetente or "").strip()
    mensagem = (mensagem or "").strip()
    if not mensagem:
        return False, "Escreva sua mensagem."
    if not email_remetente or "@" not in email_remetente:
        return False, "Informe um e-mail válido para contato."
    destino = email_suporte()
    if not destino:
        return False, "Canal de dúvidas indisponível (suporte não configurado)."
    if not smtp_configurado():
        return False, "Envio indisponível no momento. Tente mais tarde."

    corpo = f"""
    <div style="font-family:Montserrat,Arial,Helvetica,sans-serif;color:#1a1a1a;max-width:560px">
      <div style="font-size:22px;font-weight:800;color:#0067fc">loggi</div>
      <div style="color:#6e6e6e;letter-spacing:2px;text-transform:uppercase;font-size:11px;margin-bottom:14px">Portal LEVES · Dúvida</div>
      <p><b>De:</b> {nome or '(sem nome)'} &lt;{email_remetente}&gt;</p>
      <p><b>Mensagem:</b></p>
      <div style="background:#f1f5fb;border-radius:8px;padding:12px 14px;white-space:pre-wrap">{_escape(mensagem)}</div>
      <p style="color:#6e6e6e;font-size:12px;margin-top:14px">Responda diretamente a este e-mail para falar com a operação.</p>
    </div>
    """
    return enviar_email(destino, f"[Dúvida Portal LEVES] {nome or email_remetente}", corpo, reply_to=email_remetente)


def _escape(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def _brl(v) -> str:
    return "R$ " + f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _tabela_itens(itens: list[dict], qtd_key: str, rot_qtd: str, precos: dict | None) -> tuple[str, float]:
    usa_valor = bool(precos) and any((precos or {}).get(str(it["tipo"]).upper(), 0) > 0 for it in itens)
    linhas, valor_total, total_qtd = "", 0.0, 0
    for it in itens:
        q = int(it[qtd_key])
        total_qtd += q
        col_val = ""
        if usa_valor:
            v = q * float((precos or {}).get(str(it["tipo"]).upper(), 0))
            valor_total += v
            col_val = f"<td style='padding:8px 12px;border:1px solid #d9d9d9;text-align:center'>{_brl(v)}</td>"
        linhas += (f"<tr><td style='padding:8px 12px;border:1px solid #d9d9d9;text-align:center'>{it['tipo'].title()}</td>"
                   f"<td style='padding:8px 12px;border:1px solid #d9d9d9;text-align:center'>{_fmt(q)}</td>{col_val}</tr>")
    th_val = "<th style='padding:9px 12px;border:1px solid #0057d9;text-align:center;background:#0067fc;color:#ffffff'>Valor</th>" if usa_valor else ""
    td_val_total = (f"<td style='padding:9px 12px;border:1px solid #d9d9d9;font-weight:700;text-align:center'>{_brl(valor_total)}</td>" if usa_valor else "")
    cabecalho = (f"<tr style='background:#0067fc;color:#ffffff'>"
                 f"<th style='padding:9px 12px;border:1px solid #0057d9;text-align:center;color:#ffffff'>Tipo de insumo</th>"
                 f"<th style='padding:9px 12px;border:1px solid #0057d9;text-align:center;color:#ffffff'>{rot_qtd}</th>{th_val}</tr>")
    rodape = (f"<tr><td style='padding:9px 12px;border:1px solid #d9d9d9;font-weight:700;text-align:center'>Total</td>"
              f"<td style='padding:9px 12px;border:1px solid #d9d9d9;font-weight:700;text-align:center'>{_fmt(total_qtd)}</td>{td_val_total}</tr>")
    html = f"<table style='border-collapse:collapse;width:100%;max-width:770px;margin:16px auto;text-align:center;border:1px solid #d9d9d9'>{cabecalho}{linhas}{rodape}</table>"
    return html, valor_total


def _tabela_resumo_devolucao(itens: list[dict], precos: dict | None = None) -> tuple[str, float]:
    """Tabela visual com volumes enviados, devolvidos, pendentes e valores."""
    precos_norm = {str(k).strip().upper(): float(v or 0) for k, v in (precos or {}).items()}
    linhas = []
    total_enviado = total_devolvido = total_pendente = 0
    total_valor = 0.0
    for it in itens:
        tipo = str(it.get("tipo", "")).strip().upper()
        enviado = int(it.get("enviado", 0) or 0)
        devolvido = int(it.get("devolvido", 0) or 0)
        pendente = int(it.get("pendente", 0) or 0)
        unitario = precos_norm.get(tipo, 0.0)
        valor = pendente * unitario
        total_enviado += enviado
        total_devolvido += devolvido
        total_pendente += pendente
        total_valor += valor
        linhas.append(
            "<tr>"
            f"<td style='padding:10px;border:1px solid #d9e2f0;font-weight:bold'>{_escape(tipo.title())}</td>"
            f"<td style='padding:10px;border:1px solid #d9e2f0;text-align:center'>{_fmt(enviado)}</td>"
            f"<td style='padding:10px;border:1px solid #d9e2f0;text-align:center'>{_fmt(devolvido)}</td>"
            f"<td style='padding:10px;border:1px solid #d9e2f0;text-align:center;color:#d93025;font-weight:bold'>{_fmt(pendente)}</td>"
            f"<td style='padding:10px;border:1px solid #d9e2f0;text-align:right'>{_brl(unitario)}</td>"
            f"<td style='padding:10px;border:1px solid #d9e2f0;text-align:right;font-weight:bold'>{_brl(valor)}</td></tr>"
        )
    linhas.append(
        "<tr style='background:#f2f7ff;font-weight:bold'>"
        "<td style='padding:10px;border:1px solid #d9e2f0'>TOTAL</td>"
        f"<td style='padding:10px;border:1px solid #d9e2f0;text-align:center'>{_fmt(total_enviado)}</td>"
        f"<td style='padding:10px;border:1px solid #d9e2f0;text-align:center'>{_fmt(total_devolvido)}</td>"
        f"<td style='padding:10px;border:1px solid #d9e2f0;text-align:center;color:#d93025'>{_fmt(total_pendente)}</td>"
        "<td style='padding:10px;border:1px solid #d9e2f0'></td>"
        f"<td style='padding:10px;border:1px solid #d9e2f0;text-align:right'>{_brl(total_valor)}</td></tr>"
    )
    headers = ["Insumo", "Enviados", "Devolvidos", "Pendentes", "Valor unit.", "Total pendente"]
    th = "".join(f"<th style='padding:11px 7px;border:1px solid #008bd2;background:#00baff;color:#fff;text-align:center'>{h}</th>" for h in headers)
    html = "<div style='width:100%;text-align:center;margin:20px 0'><table role='presentation' align='center' cellpadding='0' cellspacing='0' style='border-collapse:collapse;width:96%;margin:0 auto;font-family:Montserrat,Arial,sans-serif;font-size:13px'><thead><tr>" + th + "</tr></thead><tbody>" + "".join(linhas) + "</tbody></table>"
    return html, total_valor


def corpo_pendencia(
    operacao: str, itens: list[dict], total: int, precos: dict | None = None,
    competencia_label: str | None = None,
) -> str:
    tabela, valor_total = _tabela_resumo_devolucao(itens, precos)
    competencia = _escape(competencia_label or "mês selecionado")
    link_portal = "https://levesloggiapp-1.streamlit.app/"
    return f"""
    <div style="margin:0;padding:24px 10px;background:#f4f7fb;font-family:Montserrat,Arial,Helvetica,sans-serif;color:#172b4d">
      <div style="max-width:900px;margin:0 auto;background:#fff;border:1px solid #e3eaf4;border-radius:10px;overflow:hidden">
        <div style="background:#0067fc;padding:22px 28px;text-align:center">
          <img src="{LOGO_URL}" alt="Loggi" width="96" style="display:block;margin:0 auto 8px;height:auto;filter:brightness(0) invert(1)">
          <div style="font-family:Montserrat,Arial,sans-serif;font-size:13px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#fff">Portal LEVES</div>
        </div>
        <div style="padding:26px 28px">
          <h2 style="margin:0 0 18px;font-size:22px;color:#172b4d">Acompanhamento de devolução de insumos</h2>
          <p style="font-size:15px;line-height:1.6">Olá, <b>{_escape(operacao)}</b>.</p>
          <p style="font-size:15px;line-height:1.6">Este é um comunicado sobre o acompanhamento dos insumos de propriedade da Loggi (sacas, gaylords e pallets) enviados à sua operação. Para a competência <b>{competencia}</b>, consolidamos os volumes enviados e devolvidos para identificar possíveis pendências.</p>
          {tabela}
          <div style="margin:18px 0;padding:14px 16px;background:#fff5f4;border-left:4px solid #e53935;border-radius:4px;font-size:15px"><b>Valor total pendente de devolução: {_brl(valor_total)}</b></div>
          <div style="text-align:center;margin:24px 0 28px"><a href="{link_portal}" style="display:inline-block;background:#00baff;color:#fff;text-decoration:none;font-family:Montserrat,Arial,sans-serif;font-weight:bold;padding:14px 28px;border-radius:5px">Formalizar Devolução Aqui</a></div>
          <p style="font-size:14px;line-height:1.6">Solicitamos a regularização desta pendência o quanto antes, para evitar descontos. Caso haja divergências nos números ou dificuldades no processo, entre em contato pelo e-mail <a href="mailto:materiais@loggi.com" style="color:#0067fc">materiais@loggi.com</a>, para que possamos realizar os ajustes antes do desconto.</p>
          <p style="font-size:14px;line-height:1.6">Contamos com o apoio de todos para que as devoluções ocorram dentro do prazo e em conformidade com as orientações do processo.</p>
          <div style="border-top:1px solid #e3eaf4;padding-top:14px;margin-top:24px;color:#6b778c;font-size:12px">Comunicado automático do Portal LEVES · Loggi</div>
        </div>
      </div>
    </div>
    """


def enviar_pendencia(
    destinatario: str, operacao: str, itens: list[dict], total: int,
    precos: dict | None = None, competencia_label: str | None = None,
) -> tuple[bool, str]:
    assunto_comp = f" — {competencia_label}" if competencia_label else ""
    corpo = corpo_pendencia(operacao, itens, total, precos, competencia_label)
    return enviar_email(
        destinatario,
        f"Pendência de devolução{assunto_comp} — {operacao} — Portal LEVES",
        corpo,
    )


def corpo_cobranca(operacao: str, competencia_label: str, prazo: str, itens: list[dict], total: int, precos: dict | None = None) -> str:
    tabela, _ = _tabela_itens(itens, "qtd", "Quantidade", precos)
    return f"""
    <div style="font-family:Arial,Helvetica,sans-serif;color:#1a1a1a;max-width:770px;margin:0 auto">
      <div style="text-align:center;margin-bottom:8px">
        <img src="{LOGO_URL}" alt="Loggi" width="110" style="display:block;margin:0 auto;height:auto">
      </div>
      <div style="color:#6e6e6e;letter-spacing:2px;text-transform:uppercase;font-size:11px;margin-bottom:16px;text-align:center">Portal LEVES</div>
      <p>Olá, <b>{operacao}</b>.</p>
      <p>Referente à competência <b>{competencia_label}</b>, identificamos insumos enviados que <b>não foram devolvidos até o prazo</b> ({prazo}). Segue o detalhamento para acerto:</p>
      {tabela}
      <p style="color:#6e6e6e;font-size:13px">Este é um aviso automático do Portal LEVES. Em caso de dúvida, responda a este e-mail.</p>
    </div>
    """
