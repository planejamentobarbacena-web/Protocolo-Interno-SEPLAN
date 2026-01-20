import streamlit as st
import pandas as pd
import os
from github import Github

# =====================================================
# CONFIGURAÇÃO
# =====================================================
st.set_page_config(page_title="Administrador", layout="wide")

# =====================================================
# SEGURANÇA
# =====================================================
if "logado" not in st.session_state or not st.session_state.logado:
    st.stop()

if st.session_state.perfil != "Administrador":
    st.error("Acesso restrito ao Administrador.")
    st.stop()

st.title("⚙️ Administração do Sistema")

# =====================================================
# GITHUB
# =====================================================
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
BRANCH = "main"

repo = Github(GITHUB_TOKEN).get_repo(REPO_NAME)

def salvar_csv(df, caminho, msg):
    csv = df.to_csv(index=False).encode("utf-8")
    try:
        arq = repo.get_contents(caminho, ref=BRANCH)
        repo.update_file(arq.path, msg, csv, arq.sha, branch=BRANCH)
    except:
        repo.create_file(caminho, msg, csv, branch=BRANCH)

# =====================================================
# CAMINHOS
# =====================================================
CAM_USUARIOS = "data/usuarios.csv"
CAM_SETORES = "data/setores.csv"
CAM_DESTINOS = "data/setores_destinos.csv"

# =====================================================
# BASE
# =====================================================
def carregar(caminho, colunas):
    if not os.path.exists(caminho):
        pd.DataFrame(columns=colunas).to_csv(caminho, index=False)
    return pd.read_csv(caminho)

df_users = carregar(CAM_USUARIOS, ["usuario","nome_completo","senha","perfil","setor","ativo"])
df_setores = carregar(CAM_SETORES, ["id_setor","setor","ativo"])
df_destinos = carregar(CAM_DESTINOS, ["id_setor","setor_destino","secretaria","ativo"])

# =====================================================
# ABAS
# =====================================================
aba_users, aba_setores, aba_destinos = st.tabs(
    ["👤 Usuários", "🏢 Setores Internos", "📦 Setores de Destino"]
)

# =====================================================
# 👤 USUÁRIOS
# =====================================================
with aba_users:
    st.subheader("Usuários")

    st.dataframe(df_users, use_container_width=True)

    st.divider()
    st.markdown("### Ações")

    usuario_sel = st.selectbox("Usuário", df_users["usuario"])

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Ativar / Desativar"):
            idx = df_users[df_users["usuario"] == usuario_sel].index[0]
            df_users.at[idx, "ativo"] = 0 if df_users.at[idx, "ativo"] == 1 else 1
            salvar_csv(df_users, CAM_USUARIOS, "Alteração status usuário")
            st.rerun()

    with col2:
        if st.button("Excluir usuário"):
            if st.confirm(f"Excluir usuário {usuario_sel}?"):
                df_users = df_users[df_users["usuario"] != usuario_sel]
                salvar_csv(df_users, CAM_USUARIOS, "Exclusão usuário")
                st.rerun()

# =====================================================
# 🏢 SETORES INTERNOS
# =====================================================
with aba_setores:
    st.subheader("Setores Internos")

    st.dataframe(df_setores, use_container_width=True)

    st.divider()
    setor_sel = st.selectbox("Setor", df_setores["setor"])

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Ativar / Desativar setor"):
            idx = df_setores[df_setores["setor"] == setor_sel].index[0]
            df_setores.at[idx, "ativo"] = 0 if df_setores.at[idx, "ativo"] == 1 else 1
            salvar_csv(df_setores, CAM_SETORES, "Alteração status setor")
            st.rerun()

    with col2:
        if st.button("Excluir setor"):
            if st.confirm(f"Excluir setor {setor_sel}?"):
                df_setores = df_setores[df_setores["setor"] != setor_sel]
                salvar_csv(df_setores, CAM_SETORES, "Exclusão setor")
                st.rerun()

# =====================================================
# 📦 SETORES DESTINO
# =====================================================
with aba_destinos:
    st.subheader("Setores de Destino")

    st.dataframe(df_destinos, use_container_width=True)

    st.divider()
    destino_sel = st.selectbox(
        "Setor de destino",
        df_destinos["setor_destino"] + " (" + df_destinos["secretaria"] + ")"
    )

    idx = df_destinos.index[
        (df_destinos["setor_destino"] + " (" + df_destinos["secretaria"] + ")") == destino_sel
    ][0]

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Ativar / Desativar destino"):
            df_destinos.at[idx, "ativo"] = 0 if df_destinos.at[idx, "ativo"] == 1 else 1
            salvar_csv(df_destinos, CAM_DESTINOS, "Alteração status destino")
            st.rerun()

    with col2:
        if st.button("Excluir destino"):
            if st.confirm(f"Excluir {destino_sel}?"):
                df_destinos = df_destinos.drop(idx)
                salvar_csv(df_destinos, CAM_DESTINOS, "Exclusão destino")
                st.rerun()
