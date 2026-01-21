import streamlit as st
import pandas as pd
from datetime import datetime
from io import StringIO
from github import Github

# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================
st.set_page_config(page_title="Registro de Protocolo", layout="wide")

# =====================================================
# BLOQUEIO DE ACESSO
# =====================================================
if "usuario" not in st.session_state:
    st.warning("Acesso restrito. Faça login.")
    st.stop()

usuario_logado = st.session_state["usuario"]
perfil_logado = st.session_state.get("perfil", "Servidor")
setor_logado = st.session_state.get("setor", "Protocolo")

st.title("📄 Registro de Protocolo")
st.markdown("Preencha os dados do documento recebido para iniciar o processo.")

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
CAMINHO_PROC = "data/processos.csv"
CAMINHO_AND = "data/andamentos.csv"

# =====================================================
# FORMULÁRIO
# =====================================================
with st.form("form_protocolo"):
    col1, col2 = st.columns(2)

    with col1:
        numero_referencia = st.text_input("Número de Referência do Documento")
        setor_origem = st.text_input("Setor de Origem")

    with col2:
        assunto = st.text_input("Assunto do Processo")

    descricao = st.text_area("Descrição / Observações Iniciais")

    registrar = st.form_submit_button("📌 Registrar Protocolo")

# =====================================================
# REGISTRO
# =====================================================
if registrar:

    ano_atual = datetime.now().year

    # =====================================================
    # PROCESSOS
    # =====================================================
    try:
        arquivo_proc = repo.get_contents(CAMINHO_PROC, ref=BRANCH)
        conteudo = arquivo_proc.decoded_content.decode("utf-8")
        df_proc = pd.read_csv(StringIO(conteudo))
    except Exception as e:
        st.warning(f"processos.csv não encontrado, criando novo. Detalhe: {e}")
        df_proc = pd.DataFrame(columns=[
            "id_processo",
            "numero_protocolo",
            "data_entrada",
            "numero_referencia",
            "setor_origem",
            "assunto",
            "descricao",
            "setor_atual",
            "status",
            "id_setor_atual"
        ])

    novo_id = 1 if df_proc.empty else int(df_proc["id_processo"].max()) + 1

    df_ano = df_proc[
        df_proc["numero_protocolo"]
        .astype(str)
        .str.endswith(f"/{ano_atual}", na=False)
    ]

    sequencial = 1 if df_ano.empty else (
        df_ano["numero_protocolo"]
        .str.split("/")
        .str[0]
        .astype(int)
        .max() + 1
    )

    numero_protocolo = f"{sequencial:03d}/{ano_atual}"

    novo_processo = {
        "id_processo": novo_id,
        "numero_protocolo": numero_protocolo,
        "data_entrada": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "numero_referencia": numero_referencia,
        "setor_origem": setor_origem,
        "assunto": assunto,
        "descricao": descricao,
        "setor_atual": "Protocolo",
        "status": "Em Trâmite",
        "id_setor_atual": 1
    }

    df_proc = pd.concat([df_proc, pd.DataFrame([novo_processo])], ignore_index=True)

    salvar_csv_github(
        df_proc,
        CAMINHO_PROC,
        f"Novo protocolo {numero_protocolo}"
    )

    # =====================================================
    # ANDAMENTOS
    # =====================================================
    try:
        arquivo_and = repo.get_contents(CAMINHO_AND, ref=BRANCH)
        conteudo_and = arquivo_and.decoded_content.decode("utf-8")
        df_and = pd.read_csv(StringIO(conteudo_and))
    except Exception as e:
        st.warning(f"andamentos.csv não encontrado, criando novo. Detalhe: {e}")
        df_and = pd.DataFrame(columns=[
            "id_andamento",
            "id_processo",
            "data",
            "servidor",
            "perfil",
            "acao",
            "observacao",
            "setor_origem",
            "setor_destino"
        ])

    novo_and_id = 1 if df_and.empty else int(df_and["id_andamento"].max()) + 1

    novo_andamento = {
        "id_andamento": novo_and_id,
        "id_processo": novo_id,
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "servidor": usuario_logado,
        "perfil": perfil_logado,
        "acao": "Protocolo Inicial",
        "observacao": descricao,
        "setor_origem": setor_origem if setor_origem else "Externo",
        "setor_destino": setor_logado
    }

    df_and = pd.concat([df_and, pd.DataFrame([novo_andamento])], ignore_index=True)

    salvar_csv_github(
        df_and,
        CAMINHO_AND,
        f"Andamento inicial do processo {numero_protocolo}"
    )

    # =====================================================
    # FEEDBACK
    # =====================================================
    st.success(f"✅ Protocolo nº {numero_protocolo} criado com sucesso!")
    st.info("O processo já está disponível para tramitação.")
