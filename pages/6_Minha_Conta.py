import streamlit as st
import pandas as pd
import os
from github import Github

# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================
st.set_page_config(page_title="Minha Conta", layout="centered")

# =====================================================
# BLOQUEIO DE ACESSO
# =====================================================
if "usuario" not in st.session_state:
    st.warning("Acesso restrito. Faça login.")
    st.stop()

st.title("⚙️ Minha Conta")
st.subheader("Alterar senha")

USUARIO_LOGADO = st.session_state["usuario"]
CAMINHO_USUARIOS = "data/usuarios.csv"

# =====================================================
# GITHUB CONFIG (MESMO PADRÃO DO 7_)
# =====================================================
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
BRANCH = "main"

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

def salvar_csv_github(df, caminho_github, mensagem_commit):
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    try:
        arquivo = repo.get_contents(caminho_github, ref=BRANCH)
        repo.update_file(
            path=arquivo.path,
            message=mensagem_commit,
            content=csv_bytes,
            sha=arquivo.sha,
            branch=BRANCH
        )
    except:
        repo.create_file(
            path=caminho_github,
            message=mensagem_commit,
            content=csv_bytes,
            branch=BRANCH
        )

# =====================================================
# BASE DE USUÁRIOS
# =====================================================
if not os.path.exists(CAMINHO_USUARIOS):
    st.error("Base de usuários não encontrada.")
    st.stop()

df_users = pd.read_csv(CAMINHO_USUARIOS)

if USUARIO_LOGADO not in df_users["usuario"].values:
    st.error("Usuário não encontrado na base.")
    st.stop()

dados_usuario = df_users[df_users["usuario"] == USUARIO_LOGADO].iloc[0]

# =====================================================
# INFORMAÇÕES DO USUÁRIO
# =====================================================
st.markdown(f"""
**Usuário:** `{dados_usuario['usuario']}`  
**Perfil:** `{dados_usuario['perfil']}`  
**Setor:** `{dados_usuario['setor']}`
""")

st.divider()

# =====================================================
# FORMULÁRIO
# =====================================================
senha_atual = st.text_input("Senha atual", type="password")
nova_senha = st.text_input("Nova senha", type="password")
confirmar_senha = st.text_input("Confirmar nova senha", type="password")

# =====================================================
# AÇÃO
# =====================================================
if st.button("Alterar senha"):
    if not senha_atual or not nova_senha or not confirmar_senha:
        st.warning("Preencha todos os campos.")
        st.stop()

    if senha_atual != dados_usuario["senha"]:
        st.error("Senha atual incorreta.")
        st.stop()

    if nova_senha != confirmar_senha:
        st.error("A nova senha e a confirmação não conferem.")
        st.stop()

    if len(nova_senha) < 6:
        st.warning("A nova senha deve ter pelo menos 6 caracteres.")
        st.stop()

    if nova_senha == senha_atual:
        st.warning("A nova senha não pode ser igual à senha atual.")
        st.stop()

    # Atualiza senha no DataFrame
    df_users.loc[
        df_users["usuario"] == USUARIO_LOGADO, "senha"
    ] = nova_senha

    # Salva localmente (necessário para o Streamlit)
    df_users.to_csv(CAMINHO_USUARIOS, index=False)

    # Salva no GitHub
    salvar_csv_github(
        df_users,
        CAMINHO_USUARIOS,
        f"Atualização de senha do usuário {USUARIO_LOGADO}"
    )

    st.success("✅ Senha alterada com sucesso!")
