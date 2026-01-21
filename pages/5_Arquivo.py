import streamlit as st
import pandas as pd
import os
from datetime import datetime
import tempfile
import subprocess

from pdf6_utils import gerar_pdf_remessa_multi_setor

# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================
st.set_page_config(
    page_title="Arquivamento e Destinação",
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
REPO_PATH = "."
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN")

def commit_git(mensagem):
    if not GITHUB_TOKEN:
        return
    try:
        subprocess.run(["git", "add", "data/*.csv"], check=True)
        subprocess.run(
            ["git", "commit", "-m", mensagem],
            check=True
        )
        subprocess.run(["git", "push"], check=True)
    except Exception:
        pass

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

    df_dest = carregar_csv(CAMINHO_DESTINACOES, colunas)
    novo_id = 1 if df_dest.empty else df_dest["id_destinacao"].max() + 1

    df_dest.loc[len(df_dest)] = [
        novo_id,
        id_processo,
        data_saida,
        protocolista,
        destino,
        observacao
    ]

    df_dest.to_csv(CAMINHO_DESTINACOES, index=False)
    commit_git("Registrar destinação externa de processo")
    return novo_id

# =====================================================
# CONTROLE DE ACESSO POR PERFIL
# =====================================================
if "usuario" not in st.session_state:
    st.error("⛔ Acesso restrito. Faça login.")
    st.stop()

df_users = carregar_csv(CAMINHO_USUARIOS)

usuario_logado = st.session_state["usuario"]
perfil_usuario = df_users.loc[
    df_users["usuario"] == usuario_logado, "perfil"
].values[0]

if perfil_usuario not in ["Administrador", "Secretario", "Protocolo"]:
    st.error("⛔ Acesso permitido apenas a Administrador, Secretário ou Protocolo.")
    st.stop()

# =====================================================
# CARGA DE DADOS
# =====================================================
df_proc = carregar_csv(CAMINHO_PROC)
df_dest = carregar_csv(CAMINHO_DESTINACOES)
df_setores_destino = carregar_csv(CAMINHO_SETOR_DESTINO)

# =====================================================
# PROCESSOS JÁ ENCAMINHADOS
# =====================================================
if not df_dest.empty:
    df_encaminhados = df_proc.merge(
        df_dest[["id_processo", "destino", "data_saida"]],
        on="id_processo",
        how="inner"
    )

    st.markdown("### 📦 Processos já encaminhados externamente")

    st.dataframe(
        df_encaminhados[[
            "numero_protocolo",
            "numero_referencia",
            "setor_origem",
            "destino",
            "data_saida"
        ]]
        .rename(columns={
            "numero_protocolo": "Processo",
            "numero_referencia": "Referência",
            "setor_origem": "Setor Origem",
            "destino": "Setor Destino",
            "data_saida": "Data da Tramitação"
        }),
        use_container_width=True
    )

# =====================================================
# REMESSA DE ENVIO
# =====================================================
st.divider()
st.markdown("## 📄 Remessa de Envio de Processos")

if df_dest.empty:
    st.info("📭 Não há processos destinados para gerar remessa.")
else:
    df_remessa = df_proc.merge(
        df_dest[["id_processo", "destino"]],
        on="id_processo",
        how="inner"
    )

    # 🔒 CORREÇÃO DEFINITIVA DO ERRO
    df_remessa["label"] = (
        df_remessa["numero_protocolo"].astype(str).fillna("") + " - " +
        df_remessa["assunto"].astype(str).fillna("") + " (" +
        df_remessa["destino"].astype(str).fillna("") + ")"
    )

    ids_sel = st.multiselect(
        "Selecione os processos que irão compor a remessa",
        df_remessa["id_processo"].tolist(),
        format_func=lambda x: df_remessa.loc[
            df_remessa["id_processo"] == x, "label"
        ].values[0]
    )

    if ids_sel and st.button("📄 Gerar Remessa em PDF"):
        df_sel = df_remessa[df_remessa["id_processo"].isin(ids_sel)]

        processos_pdf = df_sel[[
            "destino",
            "numero_protocolo",
            "numero_referencia",
            "assunto"
        ]].rename(columns={"destino": "setor_destino"}).to_dict("records")

        caminho_pdf = os.path.join(
            tempfile.gettempdir(),
            "remessa_envio_processos.pdf"
        )

        gerar_pdf_remessa_multi_setor(processos_pdf, caminho_pdf)

        with open(caminho_pdf, "rb") as f:
            st.download_button(
                "⬇️ Baixar Remessa de Envio",
                f,
                file_name="remessa_envio_processos.pdf",
                mime="application/pdf"
            )

# =====================================================
# DESTINAÇÃO INDIVIDUAL
# =====================================================
st.divider()
st.markdown("## 📤 Encaminhamento Externo")

ids_ja_destinados = df_dest["id_processo"].unique() if not df_dest.empty else []

df_disponiveis = df_proc[
    (df_proc["status"] == "Em Trâmite") &
    (~df_proc["id_processo"].isin(ids_ja_destinados))
]

if df_disponiveis.empty:
    st.info("📭 Não há processos disponíveis.")
else:
    id_proc_sel = st.selectbox(
        "Selecione o Processo",
        df_disponiveis["id_processo"],
        format_func=lambda x: (
            f"{df_disponiveis.loc[df_disponiveis['id_processo'] == x, 'numero_protocolo'].values[0]}"
            f" - {df_disponiveis.loc[df_disponiveis['id_processo'] == x, 'assunto'].values[0]}"
        )
    )

    destinos_ativos = df_setores_destino[df_setores_destino["ativo"] == 1]

    destino_sel = st.selectbox(
        "Setor de Destino",
        destinos_ativos["setor_destino"]
    )

    observacao = st.text_area("Observação (opcional)")

    if st.button("📦 Registrar Tramitação"):
        novo_id = registrar_destinacao(
            id_proc_sel,
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            usuario_logado,
            destino_sel,
            observacao
        )

        df_proc.loc[
            df_proc["id_processo"] == id_proc_sel,
            ["status", "acao"]
        ] = ["Arquivado", "Arquivado / Destinado"]

        df_proc.to_csv(CAMINHO_PROC, index=False)
        commit_git("Arquivar e destinar processo externo")

        st.success(f"✅ Processo arquivado e encaminhado ({novo_id})")
