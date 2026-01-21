import streamlit as st
import pandas as pd
import os
from datetime import datetime
import tempfile
from pdf6_utils import gerar_pdf_remessa_multi_setor
from github import Github

# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================
st.set_page_config(
    page_title="Arquivamento e Destinação (DEBUG)",
    page_icon="🗂️",
    layout="wide"
)

# =====================================================
# CAMINHOS
# =====================================================
CAMINHO_PROC = "data/processos.csv"
CAMINHO_DESTINACOES = "data/destinacoes.csv"
CAMINHO_SETOR_DESTINO = "data/setores_destinos.csv"
CAMINHO_USUARIOS = "data/usuarios.csv"

# =====================================================
# GITHUB
# =====================================================
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN")
REPO_NAME = st.secrets.get("REPO_NAME")
BRANCH = "main"

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

def salvar_csv_github(df, caminho, mensagem):
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    try:
        arquivo = repo.get_contents(caminho, ref=BRANCH)
        repo.update_file(
            path=arquivo.path,
            message=mensagem,
            content=csv_bytes,
            sha=arquivo.sha,
            branch=BRANCH
        )
    except:
        repo.create_file(
            path=caminho,
            message=mensagem,
            content=csv_bytes,
            branch=BRANCH
        )

# =====================================================
# FUNÇÕES AUXILIARES
# =====================================================
def carregar_csv(caminho, colunas=None):
    if not os.path.exists(caminho):
        df = pd.DataFrame(columns=colunas) if colunas else pd.DataFrame()
        df.to_csv(caminho, index=False)
    return pd.read_csv(caminho)


def registrar_destinacao(id_processo, data_saida, protocolista, destino, observacao):
    colunas = [
        "id_destinacao",
        "id_processo",
        "data_saida",
        "protocolista",
        "destino",
        "observacao"
    ]

    try:
        arquivo_dest = repo.get_contents(CAMINHO_DESTINACOES, ref=BRANCH)
        df_dest = pd.read_csv(pd.compat.StringIO(arquivo_dest.decoded_content.decode("utf-8")))
    except:
        df_dest = pd.DataFrame(columns=colunas)

    novo_id = 1 if df_dest.empty else df_dest["id_destinacao"].max() + 1

    df_dest.loc[len(df_dest)] = [
        novo_id,
        id_processo,
        data_saida,
        protocolista,
        destino,
        observacao
    ]

    salvar_csv_github(
        df_dest,
        CAMINHO_DESTINACOES,
        f"Registrar destinação externa de processo {id_processo}"
    )
    return novo_id

# =====================================================
# CONTROLE DE ACESSO
# =====================================================
if "usuario" not in st.session_state:
    st.error("⛔ Acesso restrito. Faça login.")
    st.stop()

usuario_logado = st.session_state["usuario"]

# =====================================================
# CARREGAR DADOS COM DEBUG
# =====================================================
# Processos
try:
    arquivo_proc = repo.get_contents(CAMINHO_PROC, ref=BRANCH)
    df_proc = pd.read_csv(pd.compat.StringIO(arquivo_proc.decoded_content.decode("utf-8")))
    st.success(f"✅ {len(df_proc)} processos carregados do GitHub")
except:
    df_proc = carregar_csv(CAMINHO_PROC)
    st.warning(f"⚠️ Não conseguiu ler do GitHub, {len(df_proc)} processos carregados do CSV local")

st.dataframe(df_proc)  # DEBUG: mostra todos os processos

# Destinações
try:
    arquivo_dest = repo.get_contents(CAMINHO_DESTINACOES, ref=BRANCH)
    df_dest = pd.read_csv(pd.compat.StringIO(arquivo_dest.decoded_content.decode("utf-8")))
    st.success(f"✅ {len(df_dest)} destinações carregadas do GitHub")
except:
    df_dest = carregar_csv(CAMINHO_DESTINACOES)
    st.warning(f"⚠️ Não conseguiu ler do GitHub, {len(df_dest)} destinações carregadas do CSV local")

st.dataframe(df_dest)  # DEBUG: mostra todas as destinações

# Setores destino
df_setores_destino = carregar_csv(CAMINHO_SETOR_DESTINO)
st.dataframe(df_setores_destino)  # DEBUG

# =====================================================
# PROCESSOS DISPONÍVEIS PARA DESTINAÇÃO EXTERNA
# =====================================================
ids_ja_destinados = df_dest["id_processo"].unique() if not df_dest.empty else []

ID_SETORES_PROTOCOLO = [1, 2]  # ajuste conforme seus setores do protocolo

df_disponiveis = df_proc[
    (df_proc["status"] == "Em Trâmite") &
    (df_proc["id_setor_atual"].isin(ID_SETORES_PROTOCOLO)) &
    (~df_proc["id_processo"].isin(ids_ja_destinados))
]

st.markdown("### 🔍 Debug Processos Disponíveis para Destinação Externa")
st.write(f"Processos disponíveis: {len(df_disponiveis)}")
st.dataframe(df_disponiveis)

# Aqui seguiria o restante da página (PDF, remessa, envio externo, desarquivamento)
# Mantendo exatamente como você tinha, usando df_disponiveis para seleção
