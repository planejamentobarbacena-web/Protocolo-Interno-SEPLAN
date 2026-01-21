import streamlit as st
import pandas as pd
from datetime import datetime
from io import StringIO
from github import Github
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

usuario_logado = st.session_state["usuario"]
perfil_logado = st.session_state["perfil"]

st.title("📊 Gestão de Servidores")

# =====================================================
# GITHUB CONFIG
# =====================================================
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
BRANCH = "main"

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

def carregar_csv_github(caminho, colunas=None):
    """
    Tenta ler CSV do GitHub. Se não conseguir, retorna DataFrame vazio com colunas.
    """
    try:
        arquivo = repo.get_contents(caminho, ref=BRANCH)
        conteudo = arquivo.decoded_content.decode("utf-8")
        return pd.read_csv(StringIO(conteudo))
    except Exception as e:
        st.warning(f"⚠️ Não conseguiu ler do GitHub: {caminho}, criando vazio. Detalhe: {e}")
        return pd.DataFrame(columns=colunas)

# =====================================================
# CARREGAR BASES
# =====================================================
CAMINHO_PROC = "data/processos.csv"
CAMINHO_AND = "data/andamentos.csv"
CAMINHO_USERS = "data/usuarios.csv"

df_proc = carregar_csv_github(CAMINHO_PROC, columns=[
    "id_processo","numero_protocolo","data_entrada","numero_referencia",
    "setor_origem","assunto","descricao","setor_atual","status","id_setor_atual","acao"
])

df_and = carregar_csv_github(CAMINHO_AND, columns=[
    "id_andamento","id_processo","data","servidor","perfil","acao",
    "observacao","setor_origem","setor_destino"
])

df_users = carregar_csv_github(CAMINHO_USERS, columns=[
    "usuario","senha","perfil","setor","nome_completo"
])

# =====================================================
# TRATAMENTO DE DATAS
# =====================================================
df_proc["data_entrada"] = pd.to_datetime(df_proc["data_entrada"], errors="coerce")
df_and["data"] = pd.to_datetime(df_and["data"], errors="coerce")

# =====================================================
# FILTRAR SERVIDORES COM MOVIMENTAÇÃO
# =====================================================
hist_servidor_base = df_and.dropna(subset=["servidor"]).copy()

servidores_disponiveis = hist_servidor_base["servidor"].unique()

if len(servidores_disponiveis) == 0:
    st.info("Nenhum servidor cadastrado para consulta.")
    st.stop()

# =====================================================
# SELEÇÃO DO SERVIDOR
# =====================================================
st.subheader("🔍 Consulta por Servidor")
servidor_sel = st.selectbox(
    "Selecione o servidor",
    servidores_disponiveis
)

hist_servidor = hist_servidor_base[hist_servidor_base["servidor"] == servidor_sel].copy()

# =====================================================
# FILTRO POR PERÍODO
# =====================================================
st.subheader("📅 Filtrar por Período")
col1, col2 = st.columns(2)

data_inicio = col1.date_input(
    "Data de Início",
    value=hist_servidor["data"].min().date() if not hist_servidor.empty else datetime.today().date()
)

data_fim = col2.date_input(
    "Data Final",
    value=hist_servidor["data"].max().date() if not hist_servidor.empty else datetime.today().date()
)

hist_servidor = hist_servidor[
    (hist_servidor["data"].dt.date >= data_inicio) &
    (hist_servidor["data"].dt.date <= data_fim)
].copy()

# =====================================================
# VINCULAR STATUS DO PROCESSO
# =====================================================
hist_servidor = hist_servidor.merge(
    df_proc[["id_processo","status"]],
    on="id_processo",
    how="left"
)

# =====================================================
# TIPO DE RELATÓRIO
# =====================================================
tipo_relatorio = st.radio(
    "Tipo de Relatório",
    ("Relatório por momento de movimentação","Relatório por processo")
)

modo = "por_momento" if "momento" in tipo_relatorio else "por_processo"

# =====================================================
# EXIBIÇÃO
# =====================================================
hist_display = hist_servidor.copy()
hist_display["data"] = hist_display["data"].dt.strftime("%d/%m/%Y %H:%M")

st.dataframe(
    hist_display.sort_values("data")[
        ["id_processo","data","acao","status","observacao","setor_origem","setor_destino"]
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
        usuario_emissor=usuario_logado
    )

    with open(caminho_pdf, "rb") as f:
        st.download_button(
            label="⬇️ Baixar PDF",
            data=f,
            file_name=nome_pdf,
            mime="application/pdf"
        )
