"""
page_5.py — Visão analítica mensal de devoluções por insumo.
Usa a conciliação oficial da aplicação: envios, recebimentos e cobranças.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

import data_processing as dp


TIPOS = ["SACA", "GAYLORD", "PALLET"]
NOMES = {"SACA": "Saca", "GAYLORD": "Gaylord", "PALLET": "Pallet"}
CORES = {"SACA": "#0866F5", "GAYLORD": "#00A9D8", "PALLET": "#B5651D"}


def _qtd(v) -> str:
    return f"{float(v):,.0f}".replace(",", ".")


def _brl(v) -> str:
    return "R$ " + f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _cabecalho():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
    [data-testid="stAppViewContainer"],[data-testid="stAppViewContainer"] * {font-family:'Montserrat',sans-serif}
    .rel-breadcrumb {color:#8290A5;font-size:11px;font-weight:700;letter-spacing:.6px;margin:0 0 7px}
    .rel-title {color:#172B4D;font-size:35px;line-height:1.2;font-weight:800;letter-spacing:-.6px;margin:0}
    .rel-subtitle {color:#627895;font-size:14px;font-weight:600;line-height:1.55;margin:5px 0 18px}
    .rel-section {color:#172B4D;font-size:18px;font-weight:800;margin:8px 0 4px}
    .rel-caption {color:#71829A;font-size:12px;margin:0 0 12px}
    .insumo-card {background:#FFFFFF;border:1px solid #DCE7F6;border-radius:13px;padding:16px 16px 14px;height:100%}
    .insumo-name {font-size:16px;font-weight:800;color:#172B4D;margin:0 0 8px}
    .insumo-percent {font-size:29px;font-weight:800;line-height:1.1;margin:0}
    .insumo-track {height:9px;background:#EAF0F8;border-radius:20px;overflow:hidden;margin:10px 0 14px}
    .insumo-fill {height:100%;border-radius:20px}
    .insumo-grid {display:grid;grid-template-columns:1fr 1fr;gap:13px 10px}
    .insumo-label {font-size:11px;color:#71829A;font-weight:600;margin-bottom:3px}
    .insumo-value {font-size:15px;color:#17385F;font-weight:800;white-space:nowrap}
    [data-testid="stDataFrame"] {border:1px solid #DCE7F6;border-radius:10px}
    [data-testid="stMetric"] {background:#F5F8FE;border:1px solid #E0EAF8;border-radius:12px;padding:12px}
    </style>
    <div>
      <div class="rel-breadcrumb">PORTAL LEVES &nbsp;/&nbsp; RELATÓRIOS</div>
      <div class="rel-title">Relatórios de devoluções</div>
      <p class="rel-subtitle">Acompanhe, por insumo, quanto foi enviado, quanto já voltou e qual valor continua pendente.</p>
    </div>
    """, unsafe_allow_html=True)


def _filtrar_destino(df: pd.DataFrame, destino: str) -> pd.DataFrame:
    if df.empty or destino == "Todas":
        return df
    return df[df["destino"].map(dp._normalizar) == dp._normalizar(destino)].copy()


def page_5():
    _cabecalho()
    env = dp.envios_df()
    if env.empty:
        st.info("Ainda não existem envios registrados para montar o relatório.")
        return

    env = env.copy()
    env["tipo"] = env["tipo"].astype(str).str.upper().str.strip()
    env = env[env["tipo"].isin(TIPOS)].copy()
    env["ano"] = env["dt"].dt.year.astype(str)
    anos = sorted(env["ano"].dropna().unique().tolist(), reverse=True)
    destinos = sorted(d for d in env["destino"].dropna().astype(str).unique() if d.strip())

    with st.container(border=True):
        st.markdown("**Filtros da análise**")
        c1, c2 = st.columns([1, 1.6])
        with c1:
            ano = st.selectbox("Ano", ["Todos"] + anos, key="rel5_ano_analitico")
        with c2:
            destino = st.selectbox("Operação / destino", ["Todas"] + destinos, key="rel5_destino_analitico")

    env_f = env[env["ano"] == ano].copy() if ano != "Todos" else env.copy()
    env_f = _filtrar_destino(env_f, destino)
    if env_f.empty:
        st.info("Não há envios para os filtros selecionados.")
        return

    precos = dp.precos()
    meses = sorted(env_f["mes"].dropna().astype(str).unique().tolist())

    # Usa a conciliação oficial da aplicação para contar apenas devoluções
    # efetivamente recebidas e descontar cobranças já lançadas da pendência.
    conciliacoes = []
    for mes in meses:
        conc = dp.conciliacao(mes)
        if conc.empty:
            continue
        conc = _filtrar_destino(conc, destino)
        if conc.empty:
            continue
        conc = conc.copy()
        conc["mes"] = mes
        conciliacoes.append(conc)

    if conciliacoes:
        base = pd.concat(conciliacoes, ignore_index=True)
    else:
        base = pd.DataFrame(columns=["destino", "tipo", "enviado", "devolvido", "cobrado", "em_aberto", "cobravel", "mes"])

    if not base.empty:
        base = base[base["tipo"].isin(TIPOS)].copy()
        for col in ["enviado", "devolvido", "cobrado", "em_aberto"]:
            base[col] = pd.to_numeric(base[col], errors="coerce").fillna(0)
    else:
        st.info("Não há dados de conciliação de devoluções para os envios selecionados.")
        return

    st.markdown('<div class="rel-section">Desempenho por insumo</div>', unsafe_allow_html=True)
    st.markdown('<div class="rel-caption">O percentual mostra a quantidade efetivamente recebida em relação ao total enviado. A pendência desconta também as cobranças já lançadas.</div>', unsafe_allow_html=True)

    totais = base.groupby("tipo", as_index=True)[["enviado", "devolvido", "cobrado", "em_aberto"]].sum()
    cards = st.columns(3, gap="medium")
    for idx, tipo in enumerate(TIPOS):
        linha = totais.loc[tipo] if tipo in totais.index else pd.Series({"enviado": 0, "devolvido": 0, "cobrado": 0, "em_aberto": 0})
        enviado = float(linha["enviado"])
        devolvido = float(linha["devolvido"])
        cobrado = float(linha["cobrado"])
        pendente = float(linha["em_aberto"])
        percentual = min((devolvido / enviado * 100) if enviado else 0, 100)
        valor_pendente = pendente * float(precos.get(tipo, 0))
        cor = CORES[tipo]
        with cards[idx]:
            st.markdown(f"""
            <div class="insumo-card">
              <div class="insumo-name">{NOMES[tipo]}</div>
              <div class="insumo-percent" style="color:{cor}">{percentual:.1f}%</div>
              <div class="insumo-label">do volume enviado já devolvido</div>
              <div class="insumo-track"><div class="insumo-fill" style="width:{percentual:.2f}%;background:{cor}"></div></div>
              <div class="insumo-grid">
                <div><div class="insumo-label">Quantidade enviada</div><div class="insumo-value">{_qtd(enviado)}</div></div>
                <div><div class="insumo-label">Quantidade devolvida</div><div class="insumo-value">{_qtd(devolvido)}</div></div>
                <div><div class="insumo-label">Pendente</div><div class="insumo-value">{_qtd(pendente)}</div></div>
                <div><div class="insumo-label">Valor pendente</div><div class="insumo-value">{_brl(valor_pendente)}</div></div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            if cobrado:
                st.caption(f"Já cobrado: {_qtd(cobrado)} un.")

    st.markdown("---")
    st.markdown('<div class="rel-section">Acompanhamento mês a mês</div>', unsafe_allow_html=True)
    st.markdown('<div class="rel-caption">Veja o volume enviado, o que foi efetivamente devolvido e o saldo financeiro pendente em cada competência.</div>', unsafe_allow_html=True)

    linhas = []
    for mes in meses:
        fatia = base[base["mes"] == mes]
        for tipo in TIPOS:
            parte = fatia[fatia["tipo"] == tipo]
            enviado = float(parte["enviado"].sum())
            devolvido = float(parte["devolvido"].sum())
            cobrado = float(parte["cobrado"].sum())
            pendente = float(parte["em_aberto"].sum())
            if enviado == 0 and devolvido == 0 and cobrado == 0 and pendente == 0:
                continue
            percentual = (devolvido / enviado * 100) if enviado else 0
            linhas.append({
                "Competência": dp.rotulo_mes(mes),
                "Insumo": NOMES[tipo],
                "Enviado": _qtd(enviado),
                "Devolvido": _qtd(devolvido),
                "% devolução": f"{percentual:.1f}%",
                "Pendente": _qtd(pendente),
                "Valor pendente": _brl(pendente * float(precos.get(tipo, 0))),
            })

    tabela = pd.DataFrame(linhas)
    st.dataframe(tabela, width="stretch", hide_index=True, height=min(560, max(150, 38 + 38 * len(tabela))))

    st.download_button(
        "Baixar análise mensal (CSV)",
        tabela.to_csv(index=False).encode("utf-8-sig"),
        file_name="analise_mensal_devolucoes_por_insumo.csv",
        mime="text/csv",
        key="rel5_csv_analitico",
    )
