import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Registro de Protocolo", layout="wide")

# 🔐 Verificação de login
if "usuario" not in st.session_state:
    st.warning("Acesso restrito. Faça login.")
    st.stop()

usuario_logado = st.session_state["usuario"]
perfil_logado = st.session_state.get("perfil", "Servidor")
setor_logado = st.session_state.get("setor", "Protocolo")

st.title("📄 Registro de Protocolo")
st.markdown("Preencha os dados do documento recebido para iniciar o processo.")

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

    # 📂 PROCESSOS
    if os.path.exists(CAMINHO_PROC):
        df_proc = pd.read_csv(CAMINHO_PROC)
    else:
        df_proc = pd.DataFrame(columns=[
            "id_processo",
            "numero_protocolo",
            "data_entrada",
            "numero_referencia",
            "setor_origem",
            "assunto",
            "descricao",
            "setor_atual",
            "status"
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
        "data_entrada": datetime.now(),
        "numero_referencia": numero_referencia,
        "setor_origem": setor_origem,
        "assunto": assunto,
        "descricao": descricao,
        "setor_atual": "Protocolo",
        "status": "Em Trâmite"
    }

    df_proc = pd.concat([df_proc, pd.DataFrame([novo_processo])], ignore_index=True)
    df_proc.to_csv(CAMINHO_PROC, index=False)

    # =====================================================
    # ANDAMENTOS
    # =====================================================
    if os.path.exists(CAMINHO_AND):
        df_and = pd.read_csv(CAMINHO_AND)
    else:
        df_and = pd.DataFrame(columns=[
            "id_processo",
            "data",
            "servidor",
            "perfil",
            "acao",
            "observacao",
            "setor_origem",
            "setor_destino"
        ])

    novo_andamento = {
        "id_processo": novo_id,
        "data": datetime.now(),
        "servidor": usuario_logado,
        "perfil": perfil_logado,
        "acao": "Protocolo Inicial",
        "observacao": descricao,
        "setor_origem": setor_origem if setor_origem else "Externo",
        "setor_destino": "Protocolo"
    }

    df_and = pd.concat([df_and, pd.DataFrame([novo_andamento])], ignore_index=True)
    df_and.to_csv(CAMINHO_AND, index=False)

    # =====================================================
    # FEEDBACK
    # =====================================================
    st.success(f"✅ Protocolo nº {numero_protocolo} criado com sucesso!")
    st.info("O processo já está disponível para tramitação.")
