import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Administrador", layout="wide")

# ================= BLOQUEIO =================
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("Acesso restrito. Faça login.")
    st.stop()

if st.session_state.perfil != "Administrador":
    st.error("Acesso permitido apenas ao Administrador.")
    st.stop()

st.title("⚙️ Administração do Sistema")

# ================= MENSAGENS =================
if "msg_sucesso" not in st.session_state:
    st.session_state.msg_sucesso = None

def mostrar_sucesso():
    if st.session_state.msg_sucesso:
        st.success(st.session_state.msg_sucesso)
        st.session_state.msg_sucesso = None

# ================= RÓTULOS =================
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

# ================= CAMINHOS =================
CAMINHO_USUARIOS = "data/usuarios.csv"
CAMINHO_SETORES = "data/setores.csv"
CAMINHO_SETORES_DESTINO = "data/setores_destinos.csv"

# ================= FUNÇÃO BASE =================
def carregar_base(caminho, colunas):
    if not os.path.exists(caminho):
        pd.DataFrame(columns=colunas).to_csv(caminho, index=False)
    return pd.read_csv(caminho)

# ================= BASES =================
df_users = carregar_base(
    CAMINHO_USUARIOS,
    ["usuario", "nome_completo", "senha", "perfil", "setor"]
)

df_setores = carregar_base(
    CAMINHO_SETORES,
    ["id_setor", "setor", "ativo"]
)

df_setores_destino = carregar_base(
    CAMINHO_SETORES_DESTINO,
    ["id_setor", "setor_destino", "secretaria", "ativo"]
)

# ================= ABAS =================
aba_usuarios, aba_setores, aba_destinos = st.tabs(
    ["👤 Usuários", "🏢 Setores Internos", "📦 Setores de Destino"]
)

# ======================================================
# ================= ABA USUÁRIOS =======================
# ======================================================
with aba_usuarios:
    st.subheader("👤 Gestão de Usuários")
    mostrar_sucesso()

    st.dataframe(df_users.rename(columns=ROTULOS_USUARIOS), use_container_width=True)

    st.divider()
    st.markdown("### ➕ Cadastrar usuário")

    col1, col2, col3, col4, col5 = st.columns(5)
    usuario = col1.text_input("Usuário")
    nome = col2.text_input("Servidor")
    senha = col3.text_input("Senha", type="password")
    perfil = col4.selectbox("Perfil", ["Servidor", "Chefia", "Secretario", "Administrador"])
    setor = col5.selectbox(
        "Setor",
        df_setores[df_setores["ativo"] == 1]["setor"].tolist()
    )

    if st.button("Cadastrar usuário"):
        if usuario in df_users["usuario"].values:
            st.error("Usuário já existe.")
        else:
            df_users.loc[len(df_users)] = [usuario, nome, senha, perfil, setor]
            df_users.to_csv(CAMINHO_USUARIOS, index=False)
            st.session_state.msg_sucesso = "Usuário cadastrado com sucesso."
            st.rerun()

    st.divider()
    st.markdown("### 🗑️ Excluir usuário")

    usuario_exc = st.selectbox("Usuário", df_users["usuario"])
    if st.button("Excluir usuário"):
        df_users = df_users[df_users["usuario"] != usuario_exc]
        df_users.to_csv(CAMINHO_USUARIOS, index=False)
        st.session_state.msg_sucesso = "Usuário excluído."
        st.rerun()

# ======================================================
# ================= ABA SETORES INTERNOS ================
# ======================================================
with aba_setores:
    st.subheader("🏢 Gestão de Setores Internos")
    mostrar_sucesso()

    st.dataframe(
        df_setores.rename(columns=ROTULOS_SETORES).drop(columns=["ID"], errors="ignore"),
        use_container_width=True
    )

    st.divider()
    novo_setor = st.text_input("Nome do setor interno")
    if st.button("Cadastrar setor interno"):
        novo_id = df_setores["id_setor"].max() + 1 if not df_setores.empty else 1
        df_setores.loc[len(df_setores)] = [novo_id, novo_setor, 1]
        df_setores.to_csv(CAMINHO_SETORES, index=False)
        st.session_state.msg_sucesso = "Setor cadastrado."
        st.rerun()

    st.divider()
    setor_sel = st.selectbox("Setor", df_setores["setor"])
    status = st.selectbox("Situação", ["Ativo", "Inativo"])
    if st.button("Atualizar setor"):
        df_setores.loc[df_setores["setor"] == setor_sel, "ativo"] = 1 if status == "Ativo" else 0
        df_setores.to_csv(CAMINHO_SETORES, index=False)
        st.session_state.msg_sucesso = "Status atualizado."
        st.rerun()

    st.divider()
    setor_exc = st.selectbox("Setor para excluir", df_setores["setor"])
    if st.button("Excluir setor"):
        df_setores = df_setores[df_setores["setor"] != setor_exc]
        df_setores.to_csv(CAMINHO_SETORES, index=False)
        st.session_state.msg_sucesso = "Setor excluído."
        st.rerun()

# ======================================================
# ================= ABA SETORES DESTINO =================
# ======================================================
with aba_destinos:
    st.subheader("📦 Gestão de Setores de Destino")
    mostrar_sucesso()

    st.dataframe(
        df_setores_destino.rename(columns=ROTULOS_DESTINOS).drop(columns=["ID"], errors="ignore"),
        use_container_width=True
    )

    st.divider()
    st.markdown("### ➕ Cadastrar setor de destino")

    col1, col2 = st.columns(2)
    novo_destino = col1.text_input("Setor de destino")
    secretaria = col2.text_input("Secretaria (obrigatória)")

    if st.button("Cadastrar destino"):
        novo_id = df_setores_destino["id_setor"].max() + 1 if not df_setores_destino.empty else 1
        df_setores_destino.loc[len(df_setores_destino)] = [
            novo_id, novo_destino, secretaria, 1
        ]
        df_setores_destino.to_csv(CAMINHO_SETORES_DESTINO, index=False)
        st.session_state.msg_sucesso = "Destino cadastrado."
        st.rerun()

    st.divider()
    destino_sel = st.selectbox("Destino", df_setores_destino["setor_destino"])
    status_dest = st.selectbox("Situação", ["Ativo", "Inativo"])
    if st.button("Atualizar destino"):
        df_setores_destino.loc[
            df_setores_destino["setor_destino"] == destino_sel, "ativo"
        ] = 1 if status_dest == "Ativo" else 0
        df_setores_destino.to_csv(CAMINHO_SETORES_DESTINO, index=False)
        st.session_state.msg_sucesso = "Status atualizado."
        st.rerun()

    st.divider()
    destino_exc = st.selectbox("Destino para excluir", df_setores_destino["setor_destino"])
    if st.button("Excluir destino"):
        df_setores_destino = df_setores_destino[
            df_setores_destino["setor_destino"] != destino_exc
        ]
        df_setores_destino.to_csv(CAMINHO_SETORES_DESTINO, index=False)
        st.session_state.msg_sucesso = "Destino excluído."
        st.rerun()
