import streamlit as st
import pandas as pd
from io import StringIO
from datetime import datetime
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

perfil_logado = st.session_state.get("perfil", "")
if perfil_logado not in ["Secretario", "Administrador"]:
    st.error("Acesso permitido apenas ao Secretário ou Administrador.")
    st.stop()

usuario_logado = st.session_state["usuario"]

st.title("📊 Gestão de Servidores")

# =====================================================
# CONFIGURAÇÃO GITHUB
# =====================================================
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
BRANCH = "main"

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

def carregar_csv_github(caminho, colunas=None):
    """Carrega CSV do GitHub, cria vazio se não existir"""
    try:
        arquivo = repo.get_contents(caminho, ref=BRANCH)
        conteudo = arquivo.decoded_content.decode("utf-8")
        df = pd.read_csv(StringIO(conteudo))
    except Exception as e:
        st.warning(f"⚠️ Não conseguiu ler do GitHub: {caminho}, criando vazio. Detalhe: {e}")
        df = pd.DataFrame(columns=colunas) if colunas else pd.DataFrame()
    return df

# =====================================================
# CARREGAR BASES
# =====================================================
df_proc = carregar_csv_github("data/processos.csv", [
    "id_processo","numero_protocolo","data_entrada","numero_referencia",
    "setor_origem","assunto","descricao","setor_atual","status","id_setor_atual","acao"
])

df_and = carregar_csv_github("data/andamentos.csv", [
    "id_andamento","id_processo","data","servidor","perfil",
    "acao","observacao","setor_origem","setor_destino"
])

df_users = carregar_csv_github("data/usuarios.csv", [
    "usuario","senha","perfil","setor","nome_completo"
])

# =====================================================
# PROCESSAR DATAS
# =====================================================
df_and["data"] = pd.to_datetime(df_and["data"], errors="coerce")
df_proc["data_entrada"] = pd.to_datetime(df_proc["data_entrada"], errors="coerce")

# =====================================================
# FILTRAR SERVIDORES VÁLIDOS
# =====================================================
perfis_validos = ["Servidor", "Chefia", "Protocolo"]
df_servidores = df_users[df_users["perfil"].isin(perfis_validos)]

if df_servidores.empty:
    st.warning("Nenhum servidor cadastrado para consulta.")
    st.stop()

# Servidores que possuem registros de andamento
servidores_disponiveis = df_and["servidor"].dropna().unique()
servidores_disponiveis = [s for s in servidores_disponiveis if s in df_servidores["usuario"].values]

if len(servidores_disponiveis) == 0:
    st.info("Nenhum servidor cadastrado com movimentação.")
    st.stop()

# =====================================================
# SELEÇÃO DO SERVIDOR
# =====================================================
st.subheader("🔍 Consulta por Servidor")
servidor_sel = st.selectbox(
    "Selecione o servidor",
    servidores_disponiveis,
    format_func=lambda x: df_servidores.loc[df_servidores["usuario"] == x, "nome_completo"].values[0]
)

# =====================================================
# FILTRO POR PERÍODO
# =====================================================
st.subheader("📅 Filtrar por Período")
hist_servidor = df_and[df_and["servidor"] == servidor_sel].copy()

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
            "id_processo","data","acao","status",
            "observacao","setor_origem","setor_destino"
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
        servidor=df_servidores.loc[df_servidores["usuario"] == servidor_sel, "nome_completo"].values[0],
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
