import streamlit as st
import pandas as pd
import os
from pdf_utils import gerar_pdf_processo

st.set_page_config(page_title="Consulta de Protocolos", layout="wide")

# =====================================================
# 🔐 BLOQUEIO
# =====================================================
if "usuario" not in st.session_state:
    st.warning("Acesso restrito. Faça login.")
    st.stop()

usuario_logado = st.session_state["usuario"]

st.title("🔍 Consulta de Protocolos e Andamentos")

# =====================================================
# 📂 BASES
# =====================================================
df_proc = pd.read_csv("data/Processos.csv")
df_and = pd.read_csv("data/andamentos.csv")

CAMINHO_DESTINACOES = "data/destinacoes.csv"
df_dest = pd.read_csv(CAMINHO_DESTINACOES) if os.path.exists(CAMINHO_DESTINACOES) else pd.DataFrame()

df_proc["id_processo"] = pd.to_numeric(df_proc["id_processo"], errors="coerce")
df_and["id_processo"] = pd.to_numeric(df_and["id_processo"], errors="coerce")
df_and["data"] = pd.to_datetime(df_and["data"], errors="coerce")

df_proc = df_proc.dropna(subset=["id_processo"])

# =====================================================
# 🔎 FILTRO POR NÚMERO DE REFERÊNCIA
# =====================================================
st.subheader("🔎 Filtro")

referencias = sorted(df_proc["numero_referencia"].dropna().unique().tolist())
referencias.insert(0, "Todos")

ref_sel = st.selectbox(
    "Referência",
    referencias
)

df_filtrado = df_proc if ref_sel == "Todos" else df_proc[df_proc["numero_referencia"] == ref_sel]

# =====================================================
# 🔽 SELECTBOX (PROTOCOLO + ASSUNTO)
# =====================================================
df_filtrado["label"] = (
    df_filtrado["numero_protocolo"].astype(str)
    + " - "
    + df_filtrado["assunto"].astype(str)
)

opcoes = dict(zip(df_filtrado["label"], df_filtrado["id_processo"].astype(int)))

if not opcoes:
    st.info("Nenhum processo encontrado para este filtro.")
    st.stop()

label_escolhido = st.selectbox(
    "Selecione o processo",
    options=opcoes.keys()
)

id_processo = opcoes[label_escolhido]
proc = df_proc[df_proc["id_processo"] == id_processo].iloc[0]

# =====================================================
# 📜 HISTÓRICO INTERNO
# =====================================================
st.subheader("📜 Histórico do Processo")

hist = (
    df_and[df_and["id_processo"] == id_processo]
    .sort_values("data")
    .copy()
)

if hist.empty:
    st.info("Nenhum andamento interno registrado.")
else:
    hist["Data/Hora"] = hist["data"].dt.strftime("%d/%m/%Y %H:%M")
    hist["Referência"] = proc["numero_referencia"]
    hist["Assunto"] = proc["assunto"]

    hist_exibir = hist[[
        "Data/Hora",
        "Referência",
        "Assunto",
        "servidor",
        "acao",
        "observacao",
        "setor_origem",
        "setor_destino"
    ]].rename(columns={
        "servidor": "Servidor",
        "acao": "Ação",
        "observacao": "Observação",
        "setor_origem": "Setor de Origem",
        "setor_destino": "Setor Atual"
    })

    st.dataframe(
        hist_exibir,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Observação": st.column_config.TextColumn("Observação", width="large")
        }
    )

# =====================================================
# 📤 ENCAMINHAMENTO EXTERNO
# =====================================================
st.divider()
st.subheader("📤 Encaminhamento Externo")

dest = df_dest[df_dest["id_processo"] == id_processo].copy()

if dest.empty:
    st.info("Este processo não possui encaminhamento externo.")
else:
    dest["Data/Hora"] = pd.to_datetime(
        dest["data_saida"], errors="coerce", dayfirst=True
    ).dt.strftime("%d/%m/%Y %H:%M")

    dest_exibir = dest[[
        "Data/Hora",
        "protocolista",
        "destino",
        "observacao"
    ]].rename(columns={
        "protocolista": "Responsável",
        "destino": "Destino Externo",
        "observacao": "Observação"
    })

    st.dataframe(
        dest_exibir,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Observação": st.column_config.TextColumn("Observação", width="large")
        }
    )

# =====================================================
# 📄 PDF (INALTERADO)
# =====================================================
st.divider()
st.subheader("📄 Gerar PDF")

if st.button("Gerar PDF"):
    nome = f"processo_{proc['numero_protocolo'].replace('/', '-')}.pdf"

    caminho = gerar_pdf_processo(
        processo=proc,
        historico=hist,
        nome_arquivo=nome,
        usuario_emissor=usuario_logado
    )

    with open(caminho, "rb") as f:
        st.download_button(
            "⬇️ Baixar PDF",
            data=f,
            file_name=nome,
            mime="application/pdf"
        )
