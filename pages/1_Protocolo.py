import streamlit as st
import pandas as pd
from datetime import datetime
import os
from utils import registrar_andamento

st.set_page_config(page_title="Registro de Protocolo", layout="wide")

# 🔐 Verificação de login
if "usuario" not in st.session_state:
    st.warning("Acesso restrito. Faça login.")
    st.stop()

usuario_logado = st.session_state["usuario"]
setor_logado = st.session_state.get("setor", "Não informado")

st.title("📄 Registro de Protocolo")
st.markdown("Preencha os dados do documento recebido para iniciar o processo.")

CAMINHO_PROC = "data/processos.csv"

# 📌 Formulário
with st.form("form_protocolo"):
    col1, col2 = st.columns(2)

    with col1:
        numero_referencia = st.text_input(
            "Número de Referência do Documento",
            placeholder="Ex: Ofício 123/2026, Processo 456/2025"
        )
        setor_origem = st.text_input(
            "Setor de Origem",
            placeholder="Ex: Secretaria de Administração"
        )

    with col2:
        assunto = st.text_input(
            "Assunto do Processo",
            placeholder="Descreva resumidamente o assunto"
        )

    descricao = st.text_area(
        "Descrição / Observações Iniciais",
        placeholder="Informações complementares sobre o documento recebido"
    )

    registrar = st.form_submit_button("📌 Registrar Protocolo")

# 🚀 Ação ao registrar
if registrar:

    ano_atual = datetime.now().year

    # 📂 Carregar processos
    if not os.path.exists(CAMINHO_PROC):
        df_proc = pd.DataFrame(columns=[
            "id_processo",
            "numero_protocolo",
            "data_entrada",
            "numero_referencia",
            "setor_origem",
            "assunto",
            "descricao",
            "status"
        ])
        novo_id = 1
        sequencial = 1
    else:
        df_proc = pd.read_csv(CAMINHO_PROC)

        # ID interno
        if df_proc.empty or df_proc["id_processo"].isna().all():
            novo_id = 1
        else:
            novo_id = int(df_proc["id_processo"].max()) + 1

        # Sequencial por ano
        df_ano = df_proc[
            df_proc["numero_protocolo"]
            .astype(str)
            .str.endswith(f"/{ano_atual}", na=False)
        ]

        if df_ano.empty:
            sequencial = 1
        else:
            df_ano["seq"] = df_ano["numero_protocolo"].str.split("/").str[0].astype(int)
            sequencial = int(df_ano["seq"].max()) + 1

    # 🔢 Número oficial
    numero_protocolo = f"{sequencial:03d}/{ano_atual}"

    # 📄 Novo processo
    novo_processo = {
        "id_processo": novo_id,
        "numero_protocolo": numero_protocolo,
        "data_entrada": datetime.now(),
        "numero_referencia": numero_referencia,
        "setor_origem": setor_origem,
        "assunto": assunto,
        "descricao": descricao,
        "acao": "Protocolo Inicial",
        "setor_atual": "Protocolo",
        "status": "Em Trâmite",
        "id_setor_atual": 1
    }

    df_proc = pd.concat([df_proc, pd.DataFrame([novo_processo])], ignore_index=True)
    df_proc.to_csv(CAMINHO_PROC, index=False)

    # 🧭 Registrar andamento inicial
    registrar_andamento(
        id_processo=novo_id,
        servidor=usuario_logado,
        acao="Entrada de Protocolo",
        observacao=descricao,
        setor_origem=setor_origem,
        setor_destino=setor_logado
    )

    # ✅ Mensagem final
    st.success(f"✅ Protocolo nº {numero_protocolo} criado com sucesso!")
    st.info("O processo já está disponível para tramitação.")

