import streamlit as st
import pandas as pd
from pdf4_utils import gerar_pdf_4

# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================
st.set_page_config(
    page_title="Gestão de Servidores",
    page_icon="📊",
    layout="wide"
)

# =====================================================
# BLOQUEIO DE ACESSO
# =====================================================
if "usuario" not in st.session_state:
    st.warning("Acesso restrito. Faça login.")
    st.stop()

if st.session_state.get("perfil") not in ["Secretario", "Administrador"]:
    st.error("Acesso permitido apenas ao Secretário ou Administrador.")
    st.stop()

st.title("📊 Gestão de Servidores")

# =====================================================
# CARREGAMENTO DAS BASES
# =====================================================
df_proc = pd.read_csv("data/processos.csv")
df_and = pd.read_csv("data/andamentos.csv")

df_and["data"] = pd.to_datetime(df_and["data"], errors="coerce")
df_proc["data_entrada"] = pd.to_datetime(df_proc["data_entrada"], errors="coerce")

# =====================================================
# SELEÇÃO DO SERVIDOR
# =====================================================
st.subheader("🔍 Consulta por Servidor")

servidor_sel = st.selectbox(
    "Selecione o servidor",
    sorted(df_and["servidor"].dropna().unique())
)

hist_servidor = df_and[df_and["servidor"] == servidor_sel].copy()

if hist_servidor.empty:
    st.info("Nenhum registro encontrado para o servidor selecionado.")
    st.stop()

# =====================================================
# FILTRO POR PERÍODO
# =====================================================
st.subheader("📅 Filtrar por Período")

col1, col2 = st.columns(2)

data_inicio = col1.date_input(
    "Data de Início",
    value=hist_servidor["data"].min().date(),
    format="DD/MM/YYYY"
)

data_fim = col2.date_input(
    "Data Final",
    value=hist_servidor["data"].max().date(),
    format="DD/MM/YYYY"
)

hist_servidor = hist_servidor[
    (hist_servidor["data"].dt.date >= data_inicio) &
    (hist_servidor["data"].dt.date <= data_fim)
]

# =====================================================
# VINCULAR STATUS DO PROCESSO
# =====================================================
hist_servidor = hist_servidor.merge(
    df_proc[["id_processo", "status"]],
    on="id_processo",
    how="left"
)

# =====================================================
# TIPO DE RELATÓRIO
# =====================================================
tipo_relatorio = st.radio(
    "Tipo de Relatório",
    (
        "Relatório por momento de movimentação",
        "Relatório por processo"
    )
)

modo = "por_momento" if "momento" in tipo_relatorio else "por_processo"

# =====================================================
# EXIBIÇÃO
# =====================================================
hist_display = hist_servidor.copy()
hist_display["data"] = hist_display["data"].dt.strftime("%d/%m/%Y %H:%M")

st.dataframe(
    hist_display.sort_values("data")[
        [
            "id_processo",
            "data",
            "acao",
            "status",
            "observacao",
            "setor_origem",
            "setor_destino"
        ]
    ].rename(columns={
        "id_processo": "Processo",
        "data": "Data",
        "acao": "Ação",
        "status": "Status",
        "observacao": "Observação",
        "setor_origem": "Setor anterior",
        "setor_destino": "Setor atual"
    }),
    use_container_width=True
)

# =====================================================
# GERAR PDF
# =====================================================
st.subheader("📄 Gerar PDF do Histórico")

nome_pdf = f"historico_{servidor_sel.replace(' ', '_')}.pdf"
logo_path = "logo.png"  # ajuste se necessário

if st.button("📄 Gerar PDF"):
    caminho_pdf = gerar_pdf_4(
        servidor=servidor_sel,
        historico=hist_servidor,
        nome_arquivo=nome_pdf,
        tipo_relatorio=modo,
        logo_path=logo_path,
        usuario_emissor=st.session_state["usuario"]
    )

    with open(caminho_pdf, "rb") as f:
        st.download_button(
            label="⬇️ Baixar PDF",
            data=f,
            file_name=nome_pdf,
            mime="application/pdf"
        )

