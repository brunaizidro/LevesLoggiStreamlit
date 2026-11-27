"""
data_processing.py — transformação e regras (padrão DLE).

Importa os dados brutos de data_extraction, normaliza tipos e timezone e expõe
o DataFrame canônico de envios usado pelas páginas.

Schema canônico de envios:
  data (str) | tipo | destino | total | dt (datetime) | mes ("AAAA-MM") | dia (date)

Obs.: este painel é de ATIVOS a devolver (SACA/GAYLORD/PALLET), não usa as
regras de expedição/status (AT/NP/AD) do DLE clássico.
"""

from __future__ import annotations

import functools
import os

import pandas as pd
import pytz
import streamlit as st

import data_extraction

TZ = pytz.timezone("America/Sao_Paulo")

# Meses em português para rótulos de filtro/gráfico.
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}

# Cores por tipo de ativo (paleta Loggi — padrão DLE).
CORES_TIPO = {
    "SACA": "#0067fc",
    "GAYLORD": "#00baff",
    "PALLET": "#B5651D",  # derivado 1:1 do GAYLORD
}

# Tipos derivados: para cada GAYLORD enviado, vai 1 PALLET (critério).
TIPOS_OCULTOS_PORTAL = {"ROLLCONTAINER"}
TIPO_ORIGEM_DERIVADO = "GAYLORD"
TIPO_DERIVADO = "PALLET"

# Estados de uma devolução.
STATUS_TRANSITO = "EM_TRANSITO"
STATUS_RECEBIDO = "RECEBIDO"
STATUS_CONFERIDO = "CONFERIDO"
STATUS_DIVERGENTE = "DIVERGENTE"
STATUS_CANCELADO = "CANCELADO"

# Rótulos e cores de status para a UI.
STATUS_LABEL = {
    STATUS_TRANSITO: "🚚 Em trânsito",
    STATUS_RECEBIDO: "📥 Recebido",
    STATUS_CONFERIDO: "✅ Conferido",
    STATUS_DIVERGENTE: "⚠️ Divergente",
    STATUS_CANCELADO: "🚫 Cancelado",
}
# Comprometidos = tudo que "saiu" do saldo (não cancelado).
STATUS_COMPROMETIDOS = {STATUS_TRANSITO, STATUS_RECEBIDO, STATUS_CONFERIDO, STATUS_DIVERGENTE}
# Recebidos de fato (contam para conciliação/cobrança).
STATUS_RECEBIDOS = {STATUS_RECEBIDO, STATUS_CONFERIDO, STATUS_DIVERGENTE}

# Prazo padrão (dias) para devolver antes de virar cobrável.
PRAZO_PADRAO_DIAS = 15


def agora_sp() -> pd.Timestamp:
    """Retorna o horário atual de São Paulo sem timezone (compatível com datas do app)."""
    return pd.Timestamp.now(tz=TZ).tz_localize(None)


def parse_datas(valores) -> pd.Series:
    """Converte datas ISO/BR em lote; timestamps com fuso são normalizados para SP."""
    serie = pd.Series(valores, copy=False).astype("string").str.strip()
    vazias = serie.isna() | serie.str.lower().isin({"", "nan", "nat", "none"})
    iso = serie.str.match(r"^\d{4}-\d{2}-\d{2}", na=False)
    # Somente timestamps ISO com Z ou offset explícito precisam de conversão de fuso.
    com_fuso = iso & serie.str.contains(r"(?:Z|[+-]\d{2}:?\d{2})$", case=False, na=False)

    resultado = pd.Series(pd.NaT, index=serie.index, dtype="datetime64[ns]")

    # Caminho rápido: o formato da aba Envios é sempre dd/mm/aaaa. Com o
    # formato explícito o pandas não precisa inferir linha a linha.
    br_curta = ~iso & ~vazias & serie.str.fullmatch(r"\d{2}/\d{2}/\d{4}", na=False)
    if br_curta.any():
        resultado.loc[br_curta] = pd.to_datetime(
            serie.loc[br_curta], format="%d/%m/%Y", errors="coerce"
        )
    vazias = vazias | br_curta  # já tratadas; o restante segue a regra antiga

    iso_sem_fuso = iso & ~com_fuso & ~vazias
    if iso_sem_fuso.any():
        resultado.loc[iso_sem_fuso] = pd.to_datetime(
            serie.loc[iso_sem_fuso], format="ISO8601", errors="coerce"
        )

    brasileiras = ~iso & ~vazias
    if brasileiras.any():
        resultado.loc[brasileiras] = pd.to_datetime(
            serie.loc[brasileiras], dayfirst=True, errors="coerce"
        )

    if com_fuso.any():
        datas_utc = pd.to_datetime(
            serie.loc[com_fuso], errors="coerce", utc=True
        )
        resultado.loc[com_fuso] = (
            datas_utc.dt.tz_convert(TZ).dt.tz_localize(None)
        )

    return resultado


def envios_df() -> pd.DataFrame:
    """DataFrame canônico de todos os envios (sem filtro de usuário).

    O resultado processado fica em cache (antes era recalculado em toda
    interação, várias vezes por página, sobre 100 mil+ linhas).
    """
    return _envios_df_cache(data_extraction.versao("envios"))


@st.cache_data(ttl=data_extraction.TTL_ENVIOS, show_spinner=False, max_entries=3)
def _envios_df_cache(versao_abas: tuple) -> pd.DataFrame:
    cols = data_extraction.ler_envios_colunas()
    df = pd.DataFrame(
        {c: cols[c] for c in ("data", "tipo", "destino", "total")},
        columns=["data", "tipo", "destino", "total"],
    )
    if df.empty:
        return df
    # Aceita datas ISO (aaaa-mm-dd) e brasileiras (dd/mm/aaaa) linha a linha.
    df["dt"] = parse_datas(df["data"])
    df = df.dropna(subset=["dt"]).copy()
    df["tipo"] = df["tipo"].astype(str).str.upper().str.strip()
    df = df[~df["tipo"].isin(TIPOS_OCULTOS_PORTAL)].copy()
    df["destino"] = df["destino"].astype(str).str.strip()
    df["total"] = pd.to_numeric(df["total"], errors="coerce").fillna(0)

    # PALLET é derivado 1:1 do GAYLORD (para cada gaylord enviado, 1 pallet).
    # Só deriva se a planilha ainda não trouxer PALLET como tipo próprio.
    if TIPO_DERIVADO not in set(df["tipo"]):
        gay = df[df["tipo"] == TIPO_ORIGEM_DERIVADO].copy()
        if not gay.empty:
            gay["tipo"] = TIPO_DERIVADO
            df = pd.concat([df, gay], ignore_index=True)

    df["mes"] = df["dt"].dt.to_period("M").astype(str)  # "2026-08"
    df["dia"] = df["dt"].dt.date
    # Destino normalizado calculado uma vez (usado em todos os filtros).
    df["destino_norm"] = df["destino"].map(_normalizar)
    return df.reset_index(drop=True)


def envios_do_usuario(user: dict) -> pd.DataFrame:
    """Admin e GDL visualizam envios de todas as bases.
    Operação visualiza somente o próprio destino.
    """
    df = envios_df()

    if df.empty:
        return df

    perfil = str(user.get("perfil", "")).strip().lower()

    # Administrador e GDL visualizam todos os envios
    if perfil in ("admin", "gdl"):
        return df

    # Demais perfis visualizam somente sua própria base
    alvo = _normalizar(user.get("destino", ""))

    return df[df["destino_norm"] == alvo].copy()


def rotulo_mes(mes: str) -> str:
    """'2026-08' -> 'Agosto/2026'."""
    return f"{MESES_PT[int(mes[5:7])]}/{mes[:4]}"


def _to_float(v) -> float:
    """Converte texto de preço em float, aceitando '1.234,56' ou '1234.56'."""
    s = str(v or "").strip().replace("R$", "").replace(" ", "")
    if not s:
        return 0.0
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def precos() -> dict:
    """Preço unitário por tipo (config preco_<TIPO>). 0 quando não definido."""
    cfg = data_extraction.get_config()
    return {t: _to_float(cfg.get(f"preco_{t}", "")) for t in CORES_TIPO}


def tem_precos() -> bool:
    return any(v > 0 for v in precos().values())


def fmt_brl(v) -> str:
    return "R$ " + f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def destinos_devolucao() -> list[str]:
    """Lista de destinos/locais de devolução configurados (um por linha em config)."""
    import re
    raw = data_extraction.get_config().get("destinos_devolucao", "")
    itens = [s.strip() for s in re.split(r"[\n;,]", str(raw)) if s.strip()]
    seen, out = set(), []
    for i in itens:
        if i.lower() not in seen:
            seen.add(i.lower())
            out.append(i)
    return out


def base_url() -> str:
    """URL pública do app (para o QR). Configure [app].base_url no secrets."""
    b = ""
    try:
        b = st.secrets["app"].get("base_url", "")
    except Exception:  # noqa: BLE001
        b = ""
    return (b or os.environ.get("BASE_URL", "") or "http://localhost:8501").rstrip("/")


def _normalizar(v) -> str:
    # Poucos valores distintos (~200 operações) repetidos em 100 mil linhas:
    # memoiza para não refazer a normalização Unicode a cada linha.
    if v is None or isinstance(v, str):
        return _normalizar_str(v)
    return _normalizar_str(str(v))


@functools.lru_cache(maxsize=4096)
def _normalizar_str(v) -> str:
    import unicodedata
    s = "" if v is None else str(v)
    s = s.strip().lower()
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


# ---------------------------------------------------------------------------
# Devoluções
# ---------------------------------------------------------------------------

def devolucoes_df() -> pd.DataFrame:
    return _devolucoes_df_cache(data_extraction.versao("devolucoes"))


@st.cache_data(ttl=data_extraction.TTL_ABAS, show_spinner=False, max_entries=3)
def _devolucoes_df_cache(versao_abas: tuple) -> pd.DataFrame:
    devs = data_extraction.ler_devolucoes()
    df = pd.DataFrame(devs)
    if df.empty:
        return df
    for c in ("total_declarado", "total_recebido"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    # Padroniza status e datas para que históricos antigos também entrem
    # na conciliação, mesmo quando a planilha contém caixa/ espaços ou datas BR.
    df["status"] = (
        df["status"].astype(str).str.strip().str.upper()
        .str.normalize("NFKD").str.encode("ascii", errors="ignore").str.decode("ascii")
        .str.replace(" ", "_", regex=False)
    )
    df["dt_criacao"] = parse_datas(df["data_criacao"])
    df["dt_recebimento"] = parse_datas(df["data_recebimento"])
    # Competência calculada uma vez, vetorizada (antes era um apply linha a
    # linha que chamava parse_datas para cada devolução, várias vezes por tela).
    comp = df["competencia"].fillna("").astype(str).str.strip()
    comp_legado = df["dt_criacao"].dt.strftime("%Y-%m").fillna("")
    df["comp"] = comp.where(comp != "", comp_legado)
    df["destino_norm"] = df["destino"].map(_normalizar)
    return df


def itens_df() -> pd.DataFrame:
    return _itens_df_cache(data_extraction.versao("itens"))


@st.cache_data(ttl=data_extraction.TTL_ABAS, show_spinner=False, max_entries=3)
def _itens_df_cache(versao_abas: tuple) -> pd.DataFrame:
    df = pd.DataFrame(data_extraction.ler_dev_itens())
    if df.empty:
        return df
    df["tipo"] = df["tipo"].astype(str).str.upper().str.strip()
    df = df[~df["tipo"].isin(TIPOS_OCULTOS_PORTAL)].copy()
    df["qtd_declarada"] = pd.to_numeric(df["qtd_declarada"], errors="coerce").fillna(0)
    return df


def saldo_por_tipo(destino: str) -> pd.DataFrame:
    """Saldo a devolver por tipo: enviado − devolvido_comprometido.

    Retorna colunas: tipo, enviado, devolvido, saldo (saldo >= 0).
    """
    alvo = _normalizar(destino)

    env = envios_df()
    if env.empty:
        enviado = {}
    else:
        e = env[env["destino"].map(_normalizar) == alvo]
        enviado = e.groupby("tipo")["total"].sum().to_dict()

    # Devolvido comprometido (não cancelado) para este destino.
    devolvido = {}
    devs = devolucoes_df()
    its = itens_df()
    if not devs.empty and not its.empty:
        devs_dest = devs[
            (devs["destino"].map(_normalizar) == alvo)
            & (devs["status"].isin(STATUS_COMPROMETIDOS))
        ]
        ids = set(devs_dest["id"])
        it = its[its["id_devolucao"].isin(ids)]
        devolvido = it.groupby("tipo")["qtd_declarada"].sum().to_dict()

    # Já cobrado (baixado) — sai do saldo, pois não aceita mais devolução.
    cobrado = _cobrado_por_chave(agora_sp())
    cobrado = {t: q for (dn, t), q in cobrado.items() if dn == alvo}

    tipos = sorted(set(enviado) | set(devolvido) | set(cobrado) | set(CORES_TIPO))
    linhas = []
    for t in tipos:
        env_v = int(enviado.get(t, 0))
        dev_v = int(devolvido.get(t, 0))
        cob_v = int(cobrado.get(t, 0))
        linhas.append({"tipo": t, "enviado": env_v, "devolvido": dev_v,
                       "saldo": max(env_v - dev_v - cob_v, 0)})
    return pd.DataFrame(linhas)


def itens_da_devolucao(id_dev: str) -> pd.DataFrame:
    its = itens_df()
    if its.empty:
        return its
    return its[its["id_devolucao"] == id_dev].copy()


# ---------------------------------------------------------------------------
# Conciliação enviado × devolvido (cobrança)
# ---------------------------------------------------------------------------

def _quinto_dia_util_mes_seguinte(mes: str) -> pd.Timestamp:
    """Retorna o 5º dia útil do mês seguinte, considerando segunda a sexta."""
    primeiro = (pd.Period(mes, freq="M") + 1).start_time
    dias_uteis = 0
    atual = primeiro

    while True:
        if atual.weekday() < 5:  # segunda (0) a sexta (4)
            dias_uteis += 1
            if dias_uteis == 5:
                return atual + pd.Timedelta(hours=23, minutes=59, seconds=59)
        atual += pd.Timedelta(days=1)


def prazo_devolucao(mes: str) -> pd.Timestamp:
    """Prazo de devolução da competência: 5º dia útil do mês seguinte (fim do dia)."""
    return _quinto_dia_util_mes_seguinte(mes)


def competencia_fechavel(mes: str) -> bool:
    """True quando já passou o prazo (5º dia útil do mês seguinte) e a competência pode ser fechada."""
    return agora_sp() > prazo_devolucao(mes)


def _cutoff_competencia(mes: str) -> pd.Timestamp:
    """Corte para contar devoluções: outubro/2026 considera recebimentos até hoje; demais meses seguem o prazo normal."""
    agora = agora_sp()
    if mes == "2026-10":
        return agora
    return min(prazo_devolucao(mes), agora)


def _competencia_do_dev(row) -> str:
    """Competência de uma devolução: o campo escolhido; senão, o mês da criação (legado)."""
    c = str(row.get("competencia", "") or "").strip()
    if c:
        return c
    dt = parse_datas([row.get("data_criacao")]).iloc[0]
    return dt.to_period("M").strftime("%Y-%m") if pd.notna(dt) else ""


def competencias_elegiveis(destino: str) -> list[str]:
    """Meses (competências) que a operação ainda pode devolver: dentro do prazo (até dia 5 do mês seguinte)."""
    env = envios_df()
    if env.empty:
        return []
    alvo = _normalizar(destino)
    e = env[env["destino"].map(_normalizar) == alvo]
    if e.empty:
        return []
    # Compara usando o horário de São Paulo, independentemente do fuso
    # configurado no servidor Streamlit.
    now = agora_sp()
    meses = sorted(set(e["mes"]), reverse=True)
    return [m for m in meses if now <= prazo_devolucao(m)]


def pending_mes_tipo(destino: str, mes: str) -> dict:
    """Pendência por tipo de UMA competência: enviado no mês − devolvido(comp==mes) − cobrado(comp==mes)."""
    alvo = _normalizar(destino)
    per = pd.Period(mes, freq="M")
    ini, fim = per.start_time, per.end_time

    env = envios_df()
    enviado = {}
    if not env.empty:
        e = env[(env["destino"].map(_normalizar) == alvo) & (env["dt"] >= ini) & (env["dt"] <= fim)]
        enviado = e.groupby("tipo")["total"].sum().to_dict()

    devolvido = {}
    devs = devolucoes_df()
    its = itens_df()
    if not devs.empty and not its.empty:
        d = devs[(devs["destino"].map(_normalizar) == alvo)
                 & (devs["status"].isin(STATUS_COMPROMETIDOS))].copy()
        if not d.empty:
            # "comp" já vem calculada (vetorizada) em devolucoes_df().
            d = d[d["comp"] == mes]
            it = its[its["id_devolucao"].isin(set(d["id"]))]
            devolvido = it.groupby("tipo")["qtd_declarada"].sum().to_dict()

    cobrado = {t: q for (dn, t), q in _cobrado_por_competencia(mes, ate=False).items() if dn == alvo}

    tipos = set(enviado) | set(devolvido) | set(cobrado)
    return {t: max(int(enviado.get(t, 0)) - int(devolvido.get(t, 0)) - int(cobrado.get(t, 0)), 0)
            for t in tipos}


def resumo_devolucao(destino: str, mes: str | None = None) -> pd.DataFrame:
    """Quadro enviado → em trânsito → recebido no CD → cobrado → saldo, por tipo.

    Usa as mesmas regras do saldo (pending_mes_tipo / saldo_por_tipo), só que
    separando o "devolvido" em EM TRÂNSITO e RECEBIDO NO CD para a tela.
    `mes=None` considera todos os meses (visão do GDL).
    Quantidades de devolução = qtd declarada (a que compromete o saldo).
    """
    cols = ["tipo", "enviado", "em_transito", "recebido", "cobrado", "saldo"]
    alvo = _normalizar(destino)

    env = envios_df()
    enviado = {}
    if not env.empty:
        e = env[env["destino_norm"] == alvo]
        if mes:
            e = e[e["mes"] == mes]
        enviado = e.groupby("tipo")["total"].sum().to_dict()

    transito, recebido = {}, {}
    devs = devolucoes_df()
    its = itens_df()
    if not devs.empty and not its.empty:
        d = devs[(devs["destino_norm"] == alvo) & (devs["status"].isin(STATUS_COMPROMETIDOS))]
        if mes:
            d = d[d["comp"] == mes]
        for status_set, alvo_dict in (({STATUS_TRANSITO}, transito), (STATUS_RECEBIDOS, recebido)):
            ids = set(d.loc[d["status"].isin(status_set), "id"])
            it = its[its["id_devolucao"].isin(ids)]
            alvo_dict.update(it.groupby("tipo")["qtd_declarada"].sum().to_dict())

    if mes:
        cob_raw = _cobrado_por_competencia(mes, ate=False)
    else:
        cob_raw = _cobrado_por_chave(agora_sp())
    cobrado = {t: q for (dn, t), q in cob_raw.items() if dn == alvo}

    linhas = []
    for t in sorted(set(enviado) | set(transito) | set(recebido) | set(cobrado)):
        env_v = int(enviado.get(t, 0))
        tr_v = int(transito.get(t, 0))
        rec_v = int(recebido.get(t, 0))
        cob_v = int(cobrado.get(t, 0))
        linhas.append({"tipo": t, "enviado": env_v, "em_transito": tr_v, "recebido": rec_v,
                       "cobrado": cob_v, "saldo": max(env_v - tr_v - rec_v - cob_v, 0)})
    return pd.DataFrame(linhas, columns=cols)


TIPOS_DEVOLUCAO = ("SACA", "GAYLORD", "PALLET")


def _valor_brl(v) -> float:
    """' R$  1.000,00 ' -> 1000.0 ; aceita também '1000.5' e números."""
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v or "").replace("R$", "").replace("\xa0", "").strip().replace(" ", "")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def notas_credito() -> pd.DataFrame:
    """Notas de crédito (aba Cobrancas): uma por base por mês, lançadas à mão.

    Colunas: nota, dt, mes ('2026-09'), rotulo ('Setembro/2026'), destino,
    destino_norm, valor, emitida_por. Linhas no formato antigo do fechamento
    automático (tipo SACA/GAYLORD/PALLET, quantidade na coluna de valor) são
    ignoradas aqui para não virar R$.
    """
    cols = ["nota", "dt", "mes", "rotulo", "destino", "destino_norm", "valor", "emitida_por"]
    linhas = data_extraction._valores("Cobrancas")
    if not linhas or len(linhas) < 2:
        return pd.DataFrame(columns=cols)
    cab = [str(c).strip().lower() for c in linhas[0]]
    df = pd.DataFrame([list(r) + [""] * (len(cab) - len(r)) for r in linhas[1:]], columns=cab)
    df = df[df.apply(lambda r: any(str(x).strip() for x in r), axis=1)]
    if "tipo" in df.columns:
        df = df[~df["tipo"].astype(str).str.strip().str.upper().isin(TIPOS_DEVOLUCAO)]
    if df.empty:
        return pd.DataFrame(columns=cols)
    dt = pd.to_datetime(df.get("data", ""), format="%d/%m/%Y", errors="coerce")
    nomes = {v.lower(): k for k, v in MESES_PT.items()}

    def _mes(comp, d):
        c = str(comp or "").strip()
        if len(c) == 7 and c[4] == "-":
            return c
        n = nomes.get(c.lower())
        if n and pd.notna(d):
            # nota emitida no início do mês seguinte refere-se ao mês anterior do mesmo ciclo
            ano = d.year - 1 if (n == 12 and d.month == 1) else d.year
            return f"{ano}-{n:02d}"
        return d.strftime("%Y-%m") if pd.notna(d) else ""

    out = pd.DataFrame({
        "nota": df.get("id", "").astype(str).str.strip(),
        "dt": dt,
        "mes": [_mes(c, d) for c, d in zip(df.get("competencia", ""), dt)],
        "destino": df.get("destino", "").astype(str).str.strip(),
        "valor": df.get("valor", "").map(_valor_brl),
        "emitida_por": df.get("gerado_por", "").astype(str).str.strip(),
    })
    out["rotulo"] = out["mes"].map(lambda m: rotulo_mes(m) if len(str(m)) == 7 else "—")
    out["destino_norm"] = out["destino"].map(_normalizar)
    return out[cols].reset_index(drop=True)


def pendencias_da_operacao(destino: str) -> pd.DataFrame:
    """Pendência da operação mês a mês (competência), com prazo e situação.

    Usa a mesma regra do saldo da tela de Devoluções (resumo_devolucao).
    Situação: "Em dia" (nada a devolver), "No prazo" (ainda dá para devolver),
    "Prazo encerrado" (vira cobrança no fechamento) ou "Cobrado".
    """
    cols = ["mes", "rotulo", "tipo", "enviado", "devolvido", "cobrado", "saldo",
            "valor", "prazo", "situacao"]
    env = envios_df()
    if env.empty:
        return pd.DataFrame(columns=cols)
    alvo = _normalizar(destino)
    meses = sorted(env.loc[env["destino_norm"] == alvo, "mes"].unique(), reverse=True)
    pr = precos()
    agora = agora_sp()
    linhas = []
    for mes in meses:
        r = resumo_devolucao(destino, mes)
        r = r[r["tipo"].isin(TIPOS_DEVOLUCAO)].copy()
        r = r.sort_values("tipo", key=lambda s: s.map({t: i for i, t in enumerate(TIPOS_DEVOLUCAO)}))
        prazo = prazo_devolucao(mes)
        saldo_mes = int(r["saldo"].sum())
        cobrado_mes = int(r["cobrado"].sum())
        if saldo_mes == 0:
            situacao = "Cobrado" if cobrado_mes > 0 else "Em dia"
        elif agora <= prazo:
            situacao = "No prazo"
        else:
            situacao = "Prazo encerrado"
        for _, x in r.iterrows():
            linhas.append({
                "mes": mes, "rotulo": rotulo_mes(mes), "tipo": x["tipo"],
                "enviado": int(x["enviado"]),
                "devolvido": int(x["em_transito"]) + int(x["recebido"]),
                "cobrado": int(x["cobrado"]), "saldo": int(x["saldo"]),
                "valor": int(x["saldo"]) * float(pr.get(x["tipo"], 0) or 0),
                "prazo": prazo, "situacao": situacao,
            })
    return pd.DataFrame(linhas, columns=cols)


def envios_atualizados_ate():
    """Maior data presente na aba Envios (os dados são colados manualmente)."""
    env = envios_df()
    if env.empty:
        return None
    return env["dt"].max()


def _consome_fifo(lots: list, retornado: float) -> list:
    """Consome `retornado` dos lotes mais antigos (FIFO). Devolve os lotes restantes."""
    r = retornado
    rem = []
    for d, q in lots:
        if r <= 0:
            rem.append((d, q))
        elif r >= q:
            r -= q
        else:
            rem.append((d, q - r))
            r = 0
    return rem


def _recebido_por_chave(cutoff: pd.Timestamp) -> dict:
    """Qtd efetivamente recebida por (destino_norm, tipo) até o corte."""
    devs = devolucoes_df()
    its = itens_df()
    if devs.empty or its.empty:
        return {}
    d = devs[devs["status"].isin(STATUS_RECEBIDOS)].copy()
    if d.empty:
        return {}
    # Usa a data de recebimento; em registros históricos sem essa coluna
    # preenchida, considera a data de criação da devolução já marcada como recebida.
    d["dt_receb"] = d["dt_recebimento"].fillna(d["dt_criacao"])
    d = d[d["dt_receb"].notna() & (d["dt_receb"] <= cutoff)]
    if d.empty:
        return {}
    d["destino_norm"] = d["destino"].map(_normalizar)
    mapa = d.set_index("id")["destino_norm"].to_dict()
    it = its[its["id_devolucao"].isin(set(d["id"]))].copy()
    it["q"] = it["qtd_recebida"].fillna(it["qtd_declarada"])
    it["destino_norm"] = it["id_devolucao"].map(mapa)
    it = it.dropna(subset=["destino_norm"])
    g = it.groupby(["destino_norm", "tipo"])["q"].sum()
    return {k: int(v) for k, v in g.items()}


def emails_por_destino(destino: str) -> list[str]:
    """E-mails dos usuários ativos daquele destino (para cobrança/lembrete)."""
    alvo = _normalizar(destino)
    return [u["email"] for u in data_extraction.ler_usuarios()
            if u.get("email") and u.get("ativo") and _normalizar(u["destino"]) == alvo]


def pendencias_df() -> pd.DataFrame:
    """Pendência de devolução por destino×tipo (em aberto = enviado − devolvido − cobrado).

    Considera TODO o período (não é por competência). Só linhas com pendente > 0.
    """
    cols = ["destino", "tipo", "enviado", "devolvido", "cobrado", "pendente"]
    env = envios_df()
    if env.empty:
        return pd.DataFrame(columns=cols)
    env = env.copy()
    env["destino_norm"] = env["destino"].map(_normalizar)
    enviado = env.groupby(["destino_norm", "tipo"])["total"].sum()
    disp = env.groupby("destino_norm")["destino"].first().to_dict()

    devolvido = {}
    devs = devolucoes_df()
    its = itens_df()
    if not devs.empty and not its.empty:
        d = devs[devs["status"].isin(STATUS_COMPROMETIDOS)].copy()
        d["destino_norm"] = d["destino"].map(_normalizar)
        mapa = d.set_index("id")["destino_norm"].to_dict()
        it = its[its["id_devolucao"].isin(set(d["id"]))].copy()
        it["destino_norm"] = it["id_devolucao"].map(mapa)
        it = it.dropna(subset=["destino_norm"])
        devolvido = it.groupby(["destino_norm", "tipo"])["qtd_declarada"].sum().to_dict()

    cobrado = _cobrado_por_chave(agora_sp())

    linhas = []
    for (dn, tipo), env_v in enviado.items():
        dev_v = int(devolvido.get((dn, tipo), 0))
        cob_v = int(cobrado.get((dn, tipo), 0))
        pend = max(int(env_v) - dev_v - cob_v, 0)
        if pend > 0:
            linhas.append({"destino": disp.get(dn, dn), "tipo": tipo, "enviado": int(env_v),
                           "devolvido": dev_v, "cobrado": cob_v, "pendente": pend})
    return pd.DataFrame(linhas, columns=cols).sort_values(["destino", "tipo"]).reset_index(drop=True)


def cobrancas_df() -> pd.DataFrame:
    """Histórico de cobranças fechadas (aba Cobrancas)."""
    cobs = data_extraction.ler_cobrancas()
    df = pd.DataFrame(cobs)
    if df.empty:
        return df
    df["qtd"] = pd.to_numeric(df["qtd"], errors="coerce").fillna(0).astype(int)
    df["dt"] = pd.to_datetime(df["data"], errors="coerce")
    return df


def _cobrado_por_chave(cutoff: pd.Timestamp) -> dict:
    """Qtd já cobrada (baixada) por (destino_norm, tipo) até o corte."""
    cobs = data_extraction.ler_cobrancas()
    if not cobs:
        return {}
    df = pd.DataFrame(cobs)
    df["dt_cob"] = pd.to_datetime(df["data"], errors="coerce")
    df = df[df["dt_cob"].notna() & (df["dt_cob"] <= cutoff)]
    if df.empty:
        return {}
    df["destino_norm"] = df["destino"].map(_normalizar)
    df["tipo"] = df["tipo"].astype(str).str.upper().str.strip()
    df["qtd"] = pd.to_numeric(df["qtd"], errors="coerce").fillna(0)
    g = df.groupby(["destino_norm", "tipo"])["qtd"].sum()
    return {k: int(v) for k, v in g.items()}


def _cobrado_por_competencia(mes: str, ate: bool = True) -> dict:
    """Qtd cobrada por (destino_norm, tipo). ate=True: competências <= mes; senão só == mes."""
    cobs = data_extraction.ler_cobrancas()
    if not cobs:
        return {}
    df = pd.DataFrame(cobs)
    df["competencia"] = df["competencia"].astype(str)
    df = df[df["competencia"] <= mes] if ate else df[df["competencia"] == mes]
    if df.empty:
        return {}
    df["destino_norm"] = df["destino"].map(_normalizar)
    df["tipo"] = df["tipo"].astype(str).str.upper().str.strip()
    df["qtd"] = pd.to_numeric(df["qtd"], errors="coerce").fillna(0)
    g = df.groupby(["destino_norm", "tipo"])["qtd"].sum()
    return {k: int(v) for k, v in g.items()}


def _recebido_por_competencia(mes: str, cutoff: pd.Timestamp) -> dict:
    """Qtd efetivamente recebida por competência, até o corte."""
    devs = devolucoes_df()
    its = itens_df()
    if devs.empty or its.empty:
        return {}
    d = devs[devs["status"].isin(STATUS_RECEBIDOS)].copy()
    if d.empty:
        return {}
    # Usa a data de recebimento; em registros históricos sem essa coluna
    # preenchida, considera a data de criação da devolução já marcada como recebida.
    d["dt_receb"] = d["dt_recebimento"].fillna(d["dt_criacao"])
    d = d[d["dt_receb"].notna() & (d["dt_receb"] <= cutoff)]
    if d.empty:
        return {}
    # "comp" já vem calculada (vetorizada) em devolucoes_df().
    d = d[d["comp"] == mes]
    if d.empty:
        return {}
    d["destino_norm"] = d["destino"].map(_normalizar)
    mapa = d.set_index("id")["destino_norm"].to_dict()
    it = its[its["id_devolucao"].isin(set(d["id"]))].copy()
    it["q"] = it["qtd_recebida"].fillna(it["qtd_declarada"])
    it["destino_norm"] = it["id_devolucao"].map(mapa)
    it = it.dropna(subset=["destino_norm"])
    g = it.groupby(["destino_norm", "tipo"])["q"].sum()
    return {k: int(v) for k, v in g.items()}


def _comprometido_por_competencia(mes: str) -> dict:
    """Qtd declarada em devoluções não canceladas da competência, inclusive em trânsito."""
    devs = devolucoes_df()
    its = itens_df()
    if devs.empty or its.empty:
        return {}
    d = devs[devs["status"].isin(STATUS_COMPROMETIDOS)].copy()
    if d.empty:
        return {}
    # "comp" já vem calculada (vetorizada) em devolucoes_df().
    d = d[d["comp"] == mes]
    if d.empty:
        return {}
    d["destino_norm"] = d["destino"].map(_normalizar)
    mapa = d.set_index("id")["destino_norm"].to_dict()
    it = its[its["id_devolucao"].isin(set(d["id"]))].copy()
    it["destino_norm"] = it["id_devolucao"].map(mapa)
    it = it.dropna(subset=["destino_norm"])
    g = it.groupby(["destino_norm", "tipo"])["qtd_declarada"].sum()
    return {k: int(v) for k, v in g.items()}


def _alocar_devolucoes_fifo(
    envc: pd.DataFrame,
    devs: pd.DataFrame,
    its: pd.DataFrame,
    mes: str,
    cutoff: pd.Timestamp,
    *,
    recebido: bool,
) -> dict:
    """Soma devoluções da competência, sem restringir pela data dos envios.

    A regra é a mesma do módulo Devoluções: todas as devoluções válidas da
    competência abatem o total enviado daquela competência. Para recebidas,
    respeita-se o corte de recebimento. O excedente é limitado ao total enviado
    na conciliação e deve ser sinalizado separadamente em auditoria.
    """
    if envc.empty or devs.empty or its.empty:
        return {}

    status_validos = STATUS_RECEBIDOS if recebido else STATUS_COMPROMETIDOS
    d = devs[devs["status"].isin(status_validos)].copy()
    if d.empty:
        return {}

    # "comp" já vem calculada (vetorizada) em devolucoes_df().
    d = d[d["comp"] == mes].copy()
    if recebido:
        d["data_evento"] = d["dt_recebimento"].fillna(d["dt_criacao"])
        d = d[d["data_evento"].notna() & (d["data_evento"] <= cutoff)]
        qtd_col = "qtd_recebida"
    else:
        # A competência selecionada define o abatimento; sem corte pela data do envio.
        qtd_col = "qtd_declarada"

    if d.empty:
        return {}

    d["destino_norm"] = d["destino"].map(_normalizar)
    mapa = d.set_index("id")["destino_norm"].to_dict()
    it = its[its["id_devolucao"].isin(set(d["id"]))].copy()
    if it.empty:
        return {}

    it["destino_norm"] = it["id_devolucao"].map(mapa)
    it = it.dropna(subset=["destino_norm"])
    if recebido:
        it["qtd_evento"] = it[qtd_col].fillna(it["qtd_declarada"])
    else:
        it["qtd_evento"] = it[qtd_col]
    it["qtd_evento"] = pd.to_numeric(it["qtd_evento"], errors="coerce").fillna(0).clip(lower=0)
    g = it.groupby(["destino_norm", "tipo"])["qtd_evento"].sum()
    return {k: int(v) for k, v in g.items()}

def conciliacao(mes: str) -> pd.DataFrame:
    """Concilia por competência: todas as devoluções da competência abatem os envios.

    A quantidade declarada compromete o saldo; a recebida compõe o indicador
    Devolvido. Ambas são limitadas ao total enviado na competência.

    Em cache por (mês, versão das abas): Pendências chamava esta função 7
    vezes por interação (mês atual + evolução de 6 meses).
    """
    return _conciliacao_cache(
        mes, data_extraction.versao("envios", "devolucoes", "itens", "cobrancas")
    )


@st.cache_data(ttl=data_extraction.TTL_ABAS, show_spinner=False, max_entries=48)
def _conciliacao_cache(mes: str, versao_abas: tuple) -> pd.DataFrame:
    cols =["destino", "tipo", "enviado", "devolvido", "cobrado", "em_aberto", "cobravel"]
    env = envios_df()
    if env.empty:
        return pd.DataFrame(columns=cols)

    per = pd.Period(mes, freq="M")
    ini, fim = per.start_time, per.end_time
    cutoff = _cutoff_competencia(mes)

    envc = env[(env["dt"] >= ini) & (env["dt"] <= fim)].copy()
    if envc.empty:
        return pd.DataFrame(columns=cols)
    enviado =envc.groupby(["destino_norm", "tipo"])["total"].sum()
    disp = envc.groupby("destino_norm")["destino"].first().to_dict()

    devs = devolucoes_df()
    its = itens_df()
    comprometido = _alocar_devolucoes_fifo(
        envc, devs, its, mes, cutoff, recebido=False
    )
    recebido = _alocar_devolucoes_fifo(
        envc, devs, its, mes, cutoff, recebido=True
    )
    cobrado_mes = _cobrado_por_competencia(mes, ate=False)

    linhas = []
    for (dn, tipo), env_v in enviado.items():
        env_i = int(env_v)
        r = int(recebido.get((dn, tipo), 0))
        declarado = int(comprometido.get((dn, tipo), 0))
        cb = int(cobrado_mes.get((dn, tipo), 0))
        # Todas as devoluções declaradas da competência comprometem o saldo.
        em_aberto = max(env_i - declarado - cb, 0)
        linhas.append({
            "destino": disp.get(dn, dn), "tipo": tipo, "enviado": env_i,
            "devolvido": min(r, env_i), "cobrado": min(cb, env_i),
            "em_aberto": em_aberto, "cobravel": em_aberto,
        })
    return pd.DataFrame(linhas, columns=cols).sort_values(["destino", "tipo"]).reset_index(drop=True)
