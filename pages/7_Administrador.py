import streamlit as st
import pandas as pd
import os
from github import Github

# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================
st.set_page_config(page_title="Administrador", layout="wide")

# =====================================================
# BLOQUEIO DE ACESSO
# =====================================================
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("Acesso restrito. Faça login.")
    st.stop()

if st.session_state.perfil != "Administrador":
    st.error("Acesso permitido apenas ao Administrador.")
    st.stop()

st.title("⚙️ Administração do Sistema")

# =====================================================
# MENSAGENS DE SUCESSO
# =====================================================
if "msg_sucesso" not in st.session_state:
    st.session_state.msg_sucesso = None

def mostrar_sucesso():
    if st.session_state.msg_sucesso:
        st.success(st.session_state.msg_sucesso)
        st.session_state.msg_sucesso = None

# =====================================================
# RÓTULOS VISUAIS
# =====================================================
ROTULOS_USUARIOS = {
    "usuario": "Usuário",
    "nome_completo": "Servidor",
    "senha": "Senha",
    "perfil": "Perfil",
    "setor": "Setor"
}

ROTULOS_SETORES = {
    "id_setor": "ID",
    "setor": "Setor Interno",
    "ativo": "Ativo"
}

ROTULOS_DESTINOS = {
    "id_setor": "ID",
    "setor_destino": "Setor de Destino",
    "secretaria": "Secretaria",
    "ativo": "Ativo"
}

# =====================================================
# GITHUB CONFIG
# =====================================================
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
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
# CAMINHOS
# =====================================================
CAMINHO_USUARIOS = "data/usuarios.csv"
CAMINHO_SETORES = "data/setores.csv"
CAMINHO_DESTINOS = "data/setores_destinos.csv"

# =====================================================
# FUNÇÃO DE CARGA
# =====================================================
def carregar_base(caminho, colunas):
    if not os.path.exists(caminho):
        df = pd.DataFrame(columns=colunas)
        df.to_csv(caminho, index=False)
    return pd.read_csv(caminho)

# =====================================================
# BASES
# =====================================================
df_users = carregar_base(
    CAMINHO_USUARIOS,
    ["usuario", "nome_completo", "senha", "perfil", "setor"]
)

df_setores = carregar_base(
    CAMINHO_SETORES,
    ["id_setor", "setor", "ativo"]
)

df_destinos = carregar_base(
    CAMINHO_DESTINOS,
    ["id_setor", "setor_destino", "secretaria", "ativo"]
)

# =====================================================
# ABAS
# =====================================================
aba_usuarios, aba_setores, aba_destinos = st.tabs(
    ["👤 Usuários", "🏢 Setores Internos", "📦 Setores de Destino"]
)

# =====================================================
# ABA USUÁRIOS
# =====================================================
with aba_usuarios:
    st.subheader("👤 Gestão de Usuários")
    mostrar_sucesso()

    st.dataframe(df_users.rename(columns=ROTULOS_USUARIOS), use_container_width=True)

    st.divider()
    st.markdown("### ➕ Cadastrar usuário")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: usuario = st.text_input("Usuário")
    with col2: nome = st.text_input("Servidor")
    with col3: senha = st.text_input("Senha", type="password")
    with col4: perfil = st.selectbox("Perfil", ["Servidor", "Chefia", "Secretario", "Administrador"])
    with col5: setor = st.selectbox("Setor", df_setores[df_setores["ativo"] == 1]["setor"].tolist())

    if st.button("Cadastrar usuário"):
        if usuario in df_users["usuario"].values:
            st.error("Usuário já existe.")
        else:
            df_users.loc[len(df_users)] = [usuario, nome, senha, perfil, setor]
            salvar_csv_github(df_users, CAMINHO_USUARIOS, f"Cadastro usuário {usuario}")
            st.session_state.msg_sucesso = "Usuário cadastrado com sucesso."
            st.rerun()

# =====================================================
# ABA SETORES INTERNOS
# =====================================================
with aba_setores:
    st.subheader("🏢 Gestão de Setores Internos")
    mostrar_sucesso()

    st.dataframe(
        df_setores.rename(columns=ROTULOS_SETORES),
        use_container_width=True
    )

    st.divider()
    novo_setor = st.text_input("Novo setor interno")

    if st.button("Cadastrar setor interno"):
        if novo_setor.lower() in df_setores["setor"].str.lower().values:
            st.error("Setor já existe.")
        else:
            novo_id = df_setores["id_setor"].max() + 1 if not df_setores.empty else 1
            df_setores.loc[len(df_setores)] = [novo_id, novo_setor, 1]
            salvar_csv_github(df_setores, CAMINHO_SETORES, f"Cadastro setor {novo_setor}")
            st.session_state.msg_sucesso = "Setor cadastrado."
            st.rerun()

# =====================================================
# ABA SETORES DESTINO
# =====================================================
with aba_destinos:
    st.subheader("📦 Gestão de Setores de Destino")
    mostrar_sucesso()

    st.dataframe(
        df_destinos.rename(columns=ROTULOS_DESTINOS)
        .sort_values(["Secretaria", "Setor de Destino"]),
        use_container_width=True
    )

    st.divider()
    st.markdown("### ➕ Cadastrar setor de destino")

    col1, col2 = st.columns(2)
    with col1:
        novo_destino = st.text_input("Setor de destino *")
    with col2:
        secretaria = st.text_input("Secretaria *")

    if st.button("Cadastrar setor de destino"):
        if not novo_destino or not secretaria:
            st.error("Todos os campos são obrigatórios.")
        else:
            novo_id = df_destinos["id_setor"].max() + 1 if not df_destinos.empty else 1
            df_destinos.loc[len(df_destinos)] = [novo_id, novo_destino, secretaria, 1]
            salvar_csv_github(df_destinos, CAMINHO_DESTINOS, f"Cadastro destino {novo_destino}")
            st.session_state.msg_sucesso = "Setor de destino cadastrado."
            st.rerun()
