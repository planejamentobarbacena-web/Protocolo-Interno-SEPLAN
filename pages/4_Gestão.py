import streamlit as st
import pandas as pd
from datetime import datetime
from pdf4_utils import gerar_pdf_4
import pytz
from io import StringIO
from github import Github

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
# GITHUB CONFIG
# =====================================================
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
BRANCH = "main"

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

def carregar_csv_github(caminho, columns=None):
    try:
        arquivo = repo.get_contents(caminho, ref=BRANCH)
        conteudo = arquivo.decoded_content.decode("utf-8")
        df = pd.read_csv(StringIO(conteudo))
        if columns:
            for col in columns:
                if col not in df.columns:
                    df[col] = None
        return df
    except:
        return pd.DataFrame(columns=columns if columns else [])

# =====================================================
# CAMINHOS
# =====================================================
CAMINHO_PROC = "data/processos.csv"
CAMINHO_AND = "data/andamentos.csv"

# =====================================================
# CARREGAMENTO DAS BASES
# =====================================================
df_proc = carregar_csv_github(CAMINHO_PROC, columns=[
    "id_processo","numero_protocolo","data_entrada","numero_referencia",
    "setor_origem","assunto","descricao","setor_atual","status","id_setor_atual"
])
df_and = carregar_csv_github(CAMINHO_AND, columns=[
    "id_andamento","id_processo","data","servidor","perfil",
    "acao","observacao","setor_origem","setor_destino"
])

# =====================================================
# AJUSTE DE HORÁRIO
# =====================================================
fuso = pytz.timezone("America/Sao_Paulo")
df_and["data"] = pd.to_datetime(df_and["data"], errors="coerce")
# Apenas converte se não for tz-aware
if df_and["data"].dt.tz is None:
    df_and["data"] = df_and["data"].dt.tz_localize('UTC').dt.tz_convert(fuso)

df_proc["data_entrada"] = pd.to_datetime(df_proc["data_entrada"], errors="coerce")
if df_proc["data_entrada"].dt.tz is None:
    df_proc["data_entrada"] = df_proc["data_entrada"].dt.tz_localize('UTC').dt.tz_convert(fuso)

# =====================================================
# SERVIDORES (BASEADOS EM ANDAMENTOS)
# =====================================================
df_and["servidor"] = df_and["servidor"].astype(str)
servidores_disponiveis = df_and["servidor"].dropna().unique()
servidores_disponiveis.sort()

if len(servidores_disponiveis) == 0:
    st.warning("Nenhum servidor cadastrado para consulta.")
    st.stop()

st.subheader("🔍 Consulta por Servidor")
servidor_sel = st.selectbox("Selecione o servidor", servidores_disponiveis)

# Histórico do servidor selecionado
hist_servidor = df_and[df_and["servidor"] == servidor_sel].copy()

# =====================================================
# FILTRO POR PERÍODO
# =====================================================
st.subheader("📅 Filtrar por Período")
col1, col2 = st.columns(2)

data_inicio = col1.date_input(
    "Data de Início",
    value=hist_servidor["data"].min().date() if not hist_servidor.empty else datetime.now().date(),
    format="DD/MM/YYYY"
)

data_fim = col2.date_input(
    "Data Final",
    value=hist_servidor["data"].max().date() if not hist_servidor.empty else datetime.now().date(),
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
nome_pdf = f"historico_{servidor_sel}.pdf"
logo_path = "logo.png"

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
