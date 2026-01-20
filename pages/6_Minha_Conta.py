import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Minha Conta", layout="centered")

# ================= BLOQUEIO =================
if "usuario" not in st.session_state:
    st.warning("Acesso restrito. Faça login.")
    st.stop()

st.title("⚙️ Minha Conta")
st.subheader("Alterar senha")

USUARIO_LOGADO = st.session_state["usuario"]
CAMINHO_USUARIOS = "data/usuarios.csv"

# ================= BASE =================
if not os.path.exists(CAMINHO_USUARIOS):
    st.error("Base de usuários não encontrada.")
    st.stop()

df_users = pd.read_csv(CAMINHO_USUARIOS)

if USUARIO_LOGADO not in df_users["usuario"].values:
    st.error("Usuário não encontrado na base.")
    st.stop()

# ================= INFO DO USUÁRIO =================
dados_usuario = df_users[df_users["usuario"] == USUARIO_LOGADO].iloc[0]

st.markdown(f"""
**Usuário:** `{dados_usuario['usuario']}`  
**Perfil:** `{dados_usuario['perfil']}`  
**Setor:** `{dados_usuario['setor']}`
""")

st.divider()

# ================= FORMULÁRIO =================
senha_atual = st.text_input("Senha atual", type="password")
nova_senha = st.text_input("Nova senha", type="password")
confirmar_senha = st.text_input("Confirmar nova senha", type="password")

# ================= AÇÃO =================
if st.button("Alterar senha"):
    # Validações
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

    # Atualizar senha
    df_users.loc[
        df_users["usuario"] == USUARIO_LOGADO, "senha"
    ] = nova_senha

    df_users.to_csv(CAMINHO_USUARIOS, index=False)

    st.success("✅ Senha alterada com sucesso!")
