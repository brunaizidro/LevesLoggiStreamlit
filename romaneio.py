"""
romaneio.py — geração do Romaneio de Devolução em PDF (com QR code).

O QR aponta para a URL do app com o id e o token da devolução, de modo que a
câmera do time de recebimento abra direto a página de conferência.

Visual no padrão do portal: logo Loggi azul, cartões arredondados, rótulos
cinza em maiúsculas, tabela sem grade vertical e a faixa em degradê oficial
(Azul Claro → Azul Médio). Usa Montserrat se os arquivos estiverem em
assets/fonts (Montserrat-Regular/SemiBold/Bold/ExtraBold.ttf); senão, Helvetica.
"""

from __future__ import annotations

import io
import os

import qrcode
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

_RAIZ = os.path.dirname(os.path.abspath(__file__))

# Paleta do portal
AZUL = HexColor("#006aff")        # Azul Médio
AZUL_CLARO = HexColor("#00baff")  # Azul Claro
AZUL_BG = HexColor("#eaf3ff")
TEXTO = HexColor("#14213d")
TEXTO_2 = HexColor("#66728a")
CINZA_ROT = HexColor("#8a96aa")
LINHA = HexColor("#e3e9f2")
FUNDO_CARD = HexColor("#f7f9fc")
VERDE, VERDE_BG = HexColor("#0f8a4b"), HexColor("#e5f6ec")
AMARELO, AMARELO_BG = HexColor("#9a6700"), HexColor("#fff4d6")
CINZA_PILL, CINZA_BG = HexColor("#5b6b82"), HexColor("#eef1f6")

MESES = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
         "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
NOME_TIPO = {"SACA": "Sacas", "GAYLORD": "Gaylords", "PALLET": "Pallets"}
STATUS = {
    "EM_TRANSITO": ("Em trânsito", AZUL, AZUL_BG),
    "RECEBIDO": ("Recebido", VERDE, VERDE_BG),
    "CONFERIDO": ("Conferido", VERDE, VERDE_BG),
    "DIVERGENTE": ("Divergente", AMARELO, AMARELO_BG),
    "CANCELADO": ("Cancelado", CINZA_PILL, CINZA_BG),
}


def _registrar_fontes() -> dict:
    """Montserrat quando disponível; Helvetica como alternativa."""
    pasta = os.path.join(_RAIZ, "assets", "fonts")
    pesos = {"r": "Regular", "sb": "SemiBold", "b": "Bold", "xb": "ExtraBold"}
    try:
        for chave, peso in pesos.items():
            nome = f"Montserrat-{peso}"
            if nome not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(nome, os.path.join(pasta, f"{nome}.ttf")))
        return {k: f"Montserrat-{p}" for k, p in pesos.items()}
    except Exception:  # noqa: BLE001 — sem os arquivos, segue com Helvetica
        return {"r": "Helvetica", "sb": "Helvetica-Bold", "b": "Helvetica-Bold", "xb": "Helvetica-Bold"}


def url_devolucao(base_url: str, id_dev: str, token: str) -> str:
    base = (base_url or "").rstrip("/")
    return f"{base}/?dev={id_dev}&t={token}"


def _qr_png(dados: str) -> ImageReader:
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(dados)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#14213d", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def _imagem(nome: str) -> ImageReader | None:
    caminho = os.path.join(_RAIZ, nome)
    return ImageReader(caminho) if os.path.exists(caminho) else None


def _fmt(n) -> str:
    return f"{int(n or 0):,}".replace(",", ".")


def _competencia(comp: str) -> str:
    comp = str(comp or "")
    if len(comp) == 7 and comp[5:7].isdigit():
        return f"{MESES[int(comp[5:7])]}/{comp[:4]}"
    return "—"


def _data_br(valor) -> str:
    """'2026-11-27 14:03:10' -> '27/11/2026 às 14:03'."""
    s = str(valor or "").strip()
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        data = f"{s[8:10]}/{s[5:7]}/{s[:4]}"
        return f"{data} às {s[11:16]}" if len(s) >= 16 else data
    return s or "—"


def _pill(c, x, y, texto, fonte, tam, cor, fundo, alinhar="esq") -> float:
    """Selo arredondado; devolve a largura. `y` é a base do texto."""
    larg = pdfmetrics.stringWidth(texto, fonte, tam) + 7 * mm
    alt = tam + 3.4 * mm
    x0 = x - larg if alinhar == "dir" else x
    c.setFillColor(fundo)
    c.roundRect(x0, y - 1.6 * mm, larg, alt, alt / 2, stroke=0, fill=1)
    c.setFillColor(cor)
    c.setFont(fonte, tam)
    c.drawCentredString(x0 + larg / 2, y + 0.1 * mm, texto)
    return larg


def _degrade(c, x, y, larg, alt, raio=0):
    """Faixa em degradê linear Azul Claro → Azul Médio (padrão da marca)."""
    c.saveState()
    p = c.beginPath()
    if raio:
        p.roundRect(x, y, larg, alt, raio)
    else:
        p.rect(x, y, larg, alt)
    c.clipPath(p, stroke=0, fill=0)
    c.linearGradient(x, y, x + larg, y, (AZUL_CLARO, AZUL), extend=True)
    c.restoreState()


def gerar_romaneio_pdf(dev: dict, itens: list[dict], base_url: str) -> bytes:
    """Gera o PDF do romaneio. `dev` é o cabeçalho; `itens` são {tipo, qtd_declarada}."""
    F = _registrar_fontes()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"Romaneio {dev.get('id', '')}")
    w, h = A4
    m = 18 * mm                      # margem lateral
    larg_util = w - 2 * m

    # ---- faixa da marca no topo ----
    _degrade(c, 0, h - 5 * mm, w, 5 * mm)

    # ---- cabeçalho: logo, título e QR ----
    topo = h - 16 * mm
    logo = _imagem("image_logo_loggi_azul.png")
    if logo:
        lw = 34 * mm
        c.drawImage(logo, m, topo - lw * 250 / 764, lw, lw * 250 / 764, mask="auto")
    else:
        c.setFillColor(AZUL)
        c.setFont(F["xb"], 24)
        c.drawString(m, topo - 9 * mm, "loggi")

    c.setFillColor(TEXTO)
    c.setFont(F["xb"], 22)
    c.drawString(m, topo - 24 * mm, "Romaneio de devolução")
    c.setFillColor(TEXTO_2)
    c.setFont(F["r"], 9.5)
    c.drawString(m, topo - 30 * mm, "Portal Leves · envie este documento impresso junto com os insumos.")

    # ID e status em selos
    _pill(c, m, topo - 41 * mm, str(dev.get("id", "")), F["xb"], 12, AZUL, AZUL_BG)
    rot, cor, fundo = STATUS.get(str(dev.get("status", "")).upper(),
                                 (str(dev.get("status", "")) or "—", CINZA_PILL, CINZA_BG))
    larg_id = pdfmetrics.stringWidth(str(dev.get("id", "")), F["xb"], 12) + 7 * mm
    _pill(c, m + larg_id + 3 * mm, topo - 40.6 * mm, rot.upper(), F["b"], 8.5, cor, fundo)

    # QR num cartão arredondado à direita
    qr = 34 * mm
    card_w, card_h = qr + 10 * mm, qr + 17 * mm
    card_x, card_y = w - m - card_w, topo - card_h + 2 * mm
    c.setFillColor(HexColor("#ffffff"))
    c.setStrokeColor(LINHA)
    c.setLineWidth(0.8)
    c.roundRect(card_x, card_y, card_w, card_h, 4 * mm, stroke=1, fill=1)
    url = url_devolucao(base_url, dev.get("id", ""), dev.get("token", ""))
    c.drawImage(_qr_png(url), card_x + 5 * mm, card_y + 12 * mm, qr, qr)
    c.setFillColor(AZUL)
    c.setFont(F["b"], 7.5)
    c.drawCentredString(card_x + card_w / 2, card_y + 7 * mm, "ESCANEIE NO RECEBIMENTO")
    c.setFillColor(TEXTO_2)
    c.setFont(F["r"], 6.5)
    c.drawCentredString(card_x + card_w / 2, card_y + 3.6 * mm, "abre a conferência no portal")

    # ---- dados da devolução (grade de cartões 3 x 2) ----
    y = topo - 56 * mm
    campos = [
        ("BASE (DESTINO)", dev.get("destino", "") or "—"),
        ("OPERAÇÃO", dev.get("usuario", "") or "—"),
        ("COMPETÊNCIA", _competencia(dev.get("competencia", ""))),
        ("PLACA DO VEÍCULO", dev.get("placa", "") or "—"),
        ("DEVOLVER PARA", dev.get("local_devolucao", "") or "CD Loggi"),
        ("EMISSÃO", _data_br(dev.get("data_criacao", ""))),
    ]
    gap = 4 * mm
    cw = (larg_util - 2 * gap) / 3
    ch = 17 * mm
    for i, (rot_c, val) in enumerate(campos):
        col, lin = i % 3, i // 3
        cx = m + col * (cw + gap)
        cy = y - (lin + 1) * ch - lin * gap
        c.setFillColor(FUNDO_CARD)
        c.setStrokeColor(LINHA)
        c.setLineWidth(0.6)
        c.roundRect(cx, cy, cw, ch, 3 * mm, stroke=1, fill=1)
        c.setFillColor(CINZA_ROT)
        c.setFont(F["b"], 7)
        c.drawString(cx + 4.5 * mm, cy + ch - 6 * mm, rot_c)
        c.setFillColor(TEXTO)
        tam = 11.5
        texto = str(val)
        while pdfmetrics.stringWidth(texto, F["b"], tam) > cw - 9 * mm and tam > 7.5:
            tam -= 0.5
        if pdfmetrics.stringWidth(texto, F["b"], tam) > cw - 9 * mm:
            while texto and pdfmetrics.stringWidth(texto + "…", F["b"], tam) > cw - 9 * mm:
                texto = texto[:-1]
            texto += "…"
        c.setFont(F["b"], tam)
        c.drawString(cx + 4.5 * mm, cy + 4.8 * mm, texto)
    y = y - 2 * ch - gap - 10 * mm

    # ---- tabela de insumos ----
    c.setFillColor(TEXTO)
    c.setFont(F["xb"], 12.5)
    c.drawString(m, y, "Insumos devolvidos")
    y -= 7 * mm
    col_ins = m + 5 * mm
    col_decl = m + larg_util * 0.62
    col_rec = w - m - 5 * mm
    c.setFillColor(CINZA_ROT)
    c.setFont(F["b"], 7.5)
    c.drawString(col_ins, y, "INSUMO")
    c.drawCentredString(col_decl, y, "QTD. DECLARADA")
    c.drawRightString(col_rec, y, "QTD. RECEBIDA NO CD")
    y -= 3.5 * mm
    c.setStrokeColor(LINHA)
    c.setLineWidth(0.8)
    c.line(m, y, w - m, y)

    total = 0
    alt_l = 11 * mm
    for it in itens:
        tipo = str(it.get("tipo", "")).upper()
        qtd = int(it.get("qtd_declarada", 0) or 0)
        total += qtd
        base_txt = y - alt_l + 4 * mm
        _pill(c, col_ins - 1.5 * mm, base_txt, tipo, F["b"], 8, AZUL, AZUL_BG)
        c.setFillColor(TEXTO)
        c.setFont(F["xb"], 13)
        c.drawCentredString(col_decl, base_txt, _fmt(qtd))
        # espaço para anotar a contagem
        c.setStrokeColor(HexColor("#c9d3e2"))
        c.setLineWidth(0.7)
        c.line(col_rec - 30 * mm, base_txt - 1 * mm, col_rec, base_txt - 1 * mm)
        y -= alt_l
        c.setStrokeColor(LINHA)
        c.setLineWidth(0.6)
        c.line(m, y, w - m, y)

    # linha de total
    y -= 2 * mm
    c.setFillColor(AZUL_BG)
    c.roundRect(m, y - 11 * mm, larg_util, 11 * mm, 3 * mm, stroke=0, fill=1)
    c.setFillColor(TEXTO)
    c.setFont(F["xb"], 10.5)
    c.drawString(col_ins, y - 7 * mm, "TOTAL DE INSUMOS")
    c.setFillColor(AZUL)
    c.setFont(F["xb"], 14)
    c.drawCentredString(col_decl, y - 7.3 * mm, _fmt(total))
    c.setStrokeColor(HexColor("#9cc3ff"))
    c.line(col_rec - 30 * mm, y - 8 * mm, col_rec, y - 8 * mm)
    y -= 11 * mm + 9 * mm

    # ---- observação ----
    observacao = str(dev.get("obs", "") or "").strip()
    if observacao:
        linhas_obs = simpleSplit(observacao, F["r"], 9.5, larg_util - 10 * mm)[:5]
        alt_o = 11 * mm + len(linhas_obs) * 4.6 * mm
        c.setFillColor(FUNDO_CARD)
        c.setStrokeColor(LINHA)
        c.roundRect(m, y - alt_o, larg_util, alt_o, 3 * mm, stroke=1, fill=1)
        c.setFillColor(CINZA_ROT)
        c.setFont(F["b"], 7)
        c.drawString(m + 5 * mm, y - 6 * mm, "OBSERVAÇÃO")
        c.setFillColor(TEXTO)
        c.setFont(F["r"], 9.5)
        yy = y - 11 * mm
        for lo in linhas_obs:
            c.drawString(m + 5 * mm, yy, lo)
            yy -= 4.6 * mm
        y -= alt_o + 8 * mm

    # ---- conferência no recebimento ----
    alt_r = 34 * mm
    c.setFillColor(HexColor("#ffffff"))
    c.setStrokeColor(LINHA)
    c.setLineWidth(0.8)
    c.roundRect(m, y - alt_r, larg_util, alt_r, 4 * mm, stroke=1, fill=1)
    # filete azul à esquerda, recortado pelo canto arredondado do quadro
    c.saveState()
    p = c.beginPath()
    p.roundRect(m, y - alt_r, larg_util, alt_r, 4 * mm)
    c.clipPath(p, stroke=0, fill=0)
    _degrade(c, m, y - alt_r, 1.8 * mm, alt_r)
    c.restoreState()
    c.setStrokeColor(LINHA)
    c.roundRect(m, y - alt_r, larg_util, alt_r, 4 * mm, stroke=1, fill=0)
    c.setFillColor(TEXTO)
    c.setFont(F["xb"], 11)
    c.drawString(m + 7 * mm, y - 8 * mm, "Conferência no recebimento")
    c.setFillColor(TEXTO_2)
    c.setFont(F["r"], 8.5)
    c.drawString(m + 7 * mm, y - 13 * mm,
                 "Uso do time do CD: a contagem também é registrada no portal ao ler o QR code.")
    campos_ass = [("RECEBIDO POR", 0.0, 0.42), ("DATA", 0.46, 0.66), ("ASSINATURA", 0.70, 1.0)]
    for rot_a, ini, fim in campos_ass:
        x0 = m + 7 * mm + (larg_util - 14 * mm) * ini
        x1 = m + 7 * mm + (larg_util - 14 * mm) * fim
        c.setStrokeColor(HexColor("#c9d3e2"))
        c.setLineWidth(0.7)
        c.line(x0, y - 25 * mm, x1, y - 25 * mm)
        c.setFillColor(CINZA_ROT)
        c.setFont(F["b"], 6.8)
        c.drawString(x0, y - 29 * mm, rot_a)
    if True:  # barras da data
        x0 = m + 7 * mm + (larg_util - 14 * mm) * 0.46
        c.setFillColor(HexColor("#c9d3e2"))
        c.setFont(F["r"], 10)
        c.drawString(x0 + 7 * mm, y - 24 * mm, "/")
        c.drawString(x0 + 16 * mm, y - 24 * mm, "/")

    # ---- rodapé ----
    c.setStrokeColor(LINHA)
    c.setLineWidth(0.6)
    c.line(m, 17 * mm, w - m, 17 * mm)
    simbolo = _imagem("image_simbolo_lebre_azul.png")
    if simbolo:
        c.drawImage(simbolo, m, 9.6 * mm, 5 * mm, 5 * mm, mask="auto")
    c.setFillColor(TEXTO_2)
    c.setFont(F["sb"], 7.5)
    c.drawString(m + 7 * mm, 11.2 * mm, "Portal Leves · Loggi")
    c.setFont(F["r"], 7)
    c.drawRightString(w - m, 11.2 * mm,
                      f"{dev.get('id', '')} · código de validação {str(dev.get('token', ''))[:8]}")
    _degrade(c, 0, 0, w, 3 * mm)

    c.showPage()
    c.save()
    return buf.getvalue()
