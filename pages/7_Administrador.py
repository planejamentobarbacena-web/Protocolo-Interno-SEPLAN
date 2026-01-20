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

# ================= MENSAGENS DE SUCESSO =================
if "msg_sucesso" not in st.session_state:
    st.session_state.msg_sucesso = None

def mostrar_sucesso():
    if st.session_state.msg_sucesso:
        st.success(st.session_state.msg_sucesso)
        st.session_state.msg_sucesso = None

# ================= RÓTULOS VISUAIS =================
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
    "ativo": "Ativo"
}

# ================= CAMINHOS =================
CAMINHO_USUARIOS = "data/usuarios.csv"
CAMINHO_SETORES = "data/setores.csv"
CAMINHO_SETORES_DESTINO = "data/setores_destinos.csv"

# ================= FUNÇÃO BASE =================
def carregar_base(caminho, colunas):
    if not os.path.exists(caminho):
        df = pd.DataFrame(columns=colunas)
        df.to_csv(caminho, index=False)
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
    ["id_setor", "setor_destino", "ativo"]
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

    st.dataframe(
        df_users.rename(columns=ROTULOS_USUARIOS),
        use_container_width=True
    )

    st.divider()
    st.markdown("### ➕ Cadastrar usuário")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        usuario = st.text_input("Usuário", key="cad_usuario")
    with col2:
        nome = st.text_input("Servidor", key="cad_nome")
    with col3:
        senha = st.text_input("Senha", type="password", key="cad_senha")
    with col4:
        perfil = st.selectbox(
            "Perfil",
            ["Servidor", "Chefia", "Secretario", "Administrador"],
            key="cad_perfil"
        )
    with col5:
        setor = st.selectbox(
            "Setor",
            df_setores[df_setores["ativo"] == 1]["setor"].tolist(),
            key="cad_setor"
        )

    if st.button("Cadastrar usuário", key="btn_cad_usuario"):
        if usuario in df_users["usuario"].values:
            st.error("Usuário já existe.")
        else:
            df_users.loc[len(df_users)] = [
                usuario, nome, senha, perfil, setor
            ]
            df_users.to_csv(CAMINHO_USUARIOS, index=False)
            st.session_state.msg_sucesso = "Usuário cadastrado com sucesso."
            st.rerun()

    st.divider()
    st.markdown("### 🗑️ Excluir usuário")

    usuario_exc = st.selectbox(
        "Usuário",
        df_users["usuario"],
        key="exc_usuario"
    )

    if st.button("Excluir usuário", key="btn_exc_usuario"):
        df_users = df_users[df_users["usuario"] != usuario_exc]
        df_users.to_csv(CAMINHO_USUARIOS, index=False)
        st.session_state.msg_sucesso = "Usuário excluído com sucesso."
        st.rerun()

# ======================================================
# ================= ABA SETORES INTERNOS ================
# ======================================================
with aba_setores:
    st.subheader("🏢 Gestão de Setores Internos")
    mostrar_sucesso()

    st.dataframe(
        df_setores
        .rename(columns=ROTULOS_SETORES)
        .drop(columns=["ID"], errors="ignore")
        .sort_values("Setor Interno"),
        use_container_width=True
    )

    st.divider()
    st.markdown("### ➕ Cadastrar setor interno")

    novo_setor = st.text_input("Nome do setor interno", key="cad_setor_interno")

    if st.button("Cadastrar setor interno", key="btn_cad_setor"):
        if novo_setor.lower() in df_setores["setor"].str.lower().values:
            st.error("Setor já existe.")
        else:
            novo_id = df_setores["id_setor"].max() + 1 if not df_setores.empty else 1
            df_setores.loc[len(df_setores)] = [novo_id, novo_setor, 1]
            df_setores.to_csv(CAMINHO_SETORES, index=False)
            st.session_state.msg_sucesso = "Setor interno cadastrado."
            st.rerun()

    st.divider()
    st.markdown("### ✏️ Ativar / Desativar setor")

    setor_sel = st.selectbox(
        "Setor",
        df_setores["setor"],
        key="alt_setor"
    )

    novo_status = st.selectbox(
        "Nova situação",
        ["Ativo", "Inativo"],
        key="alt_status_setor"
    )

    if st.button("Atualizar setor", key="btn_alt_setor"):
        df_setores.loc[
            df_setores["setor"] == setor_sel, "ativo"
        ] = 1 if novo_status == "Ativo" else 0
        df_setores.to_csv(CAMINHO_SETORES, index=False)
        st.session_state.msg_sucesso = "Situação do setor atualizada."
        st.rerun()

    st.divider()
    st.markdown("### 🗑️ Excluir setor interno")

    setor_exc = st.selectbox(
        "Setor para excluir",
        df_setores["setor"],
        key="exc_setor"
    )

    if st.button("Excluir setor interno", key="btn_exc_setor"):
        df_setores = df_setores[df_setores["setor"] != setor_exc]
        df_setores.to_csv(CAMINHO_SETORES, index=False)
        st.session_state.msg_sucesso = "Setor interno excluído."
        st.rerun()

# ======================================================
# ================= ABA SETORES DESTINO =================
# ======================================================
with aba_destinos:
    st.subheader("📦 Gestão de Setores de Destino")
    mostrar_sucesso()

    st.dataframe(
        df_setores_destino
        .rename(columns=ROTULOS_DESTINOS)
        .drop(columns=["ID"], errors="ignore")
        .sort_values("Setor de Destino"),
        use_container_width=True
    )

    st.divider()
    st.markdown("### ➕ Cadastrar setor de destino")

    novo_destino = st.text_input(
        "Nome do setor de destino",
        key="cad_destino"
    )

    if st.button("Cadastrar setor de destino", key="btn_cad_destino"):
        if novo_destino.lower() in df_setores_destino["setor_destino"].str.lower().values:
            st.error("Destino já existe.")
        else:
            novo_id = (
                df_setores_destino["id_setor"].max() + 1
                if not df_setores_destino.empty else 1
            )
            df_setores_destino.loc[len(df_setores_destino)] = [
                novo_id, novo_destino, 1
            ]
            df_setores_destino.to_csv(CAMINHO_SETORES_DESTINO, index=False)
            st.session_state.msg_sucesso = "Setor de destino cadastrado."
            st.rerun()

    st.divider()
    st.markdown("### ✏️ Ativar / Desativar destino")

    destino_sel = st.selectbox(
        "Setor de destino",
        df_setores_destino["setor_destino"],
        key="alt_destino"
    )

    novo_status_dest = st.selectbox(
        "Nova situação",
        ["Ativo", "Inativo"],
        key="alt_status_destino"
    )

    if st.button("Atualizar destino", key="btn_alt_destino"):
        df_setores_destino.loc[
            df_setores_destino["setor_destino"] == destino_sel, "ativo"
        ] = 1 if novo_status_dest == "Ativo" else 0
        df_setores_destino.to_csv(CAMINHO_SETORES_DESTINO, index=False)
        st.session_state.msg_sucesso = "Situação do destino atualizada."
        st.rerun()

    st.divider()
    st.markdown("### 🗑️ Excluir setor de destino")

    destino_exc = st.selectbox(
        "Destino para excluir",
        df_setores_destino["setor_destino"],
        key="exc_destino"
    )

    if st.button("Excluir setor de destino", key="btn_exc_destino"):
        df_setores_destino = df_setores_destino[
            df_setores_destino["setor_destino"] != destino_exc
        ]
        df_setores_destino.to_csv(CAMINHO_SETORES_DESTINO, index=False)
        st.session_state.msg_sucesso = "Setor de destino excluído."
        st.rerun()
