import streamlit as st
import pandas as pd
import os
from datetime import datetime
import tempfile
from github import Github

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
# GITHUB CONFIG
# =====================================================
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
BRANCH = "main"

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

def salvar_csv_github(df, caminho, mensagem):
    conteudo = df.to_csv(index=False).encode("utf-8")
    try:
        arquivo = repo.get_contents(caminho, ref=BRANCH)
        repo.update_file(
            path=arquivo.path,
            message=mensagem,
            content=conteudo,
            sha=arquivo.sha,
            branch=BRANCH
        )
    except:
        repo.create_file(
            path=caminho,
            message=mensagem,
            content=conteudo,
            branch=BRANCH
        )

# =====================================================
# FUNÇÃO BASE
# =====================================================
def carregar_csv(caminho, colunas=None):
    if not os.path.exists(caminho):
        df = pd.DataFrame(columns=colunas) if colunas else pd.DataFrame()
        df.to_csv(caminho, index=False)
    return pd.read_csv(caminho)

# =====================================================
# CONTROLE DE ACESSO (POR PERFIL)
# =====================================================
if "usuario" not in st.session_state:
    st.error("⛔ Acesso restrito. Faça login.")
    st.stop()

df_users = carregar_csv(CAMINHO_USUARIOS)

dados_usuario = df_users[df_users["usuario"] == st.session_state["usuario"]]

if dados_usuario.empty:
    st.error("Usuário não encontrado.")
    st.stop()

perfil = dados_usuario.iloc[0]["perfil"]

PERFIS_AUTORIZADOS = ["Administrador", "Secretario", "Protocolo"]

if perfil not in PERFIS_AUTORIZADOS:
    st.error("⛔ Acesso permitido apenas a Administrador, Secretário ou Protocolo.")
    st.stop()

# =====================================================
# CARGA DOS DADOS
# =====================================================
df_proc = carregar_csv(CAMINHO_PROC)
df_dest = carregar_csv(
    CAMINHO_DESTINACOES,
    ["id_destinacao", "id_processo", "data_saida", "protocolista", "destino", "observacao"]
)
df_setores_destino = carregar_csv(CAMINHO_SETOR_DESTINO)

# =====================================================
# FUNÇÃO REGISTRAR DESTINAÇÃO
# =====================================================
def registrar_destinacao(id_processo, data_saida, protocolista, destino, observacao):
    novo_id = 1 if df_dest.empty else df_dest["id_destinacao"].max() + 1

    df_dest.loc[len(df_dest)] = [
        novo_id,
        id_processo,
        data_saida,
        protocolista,
        destino,
        observacao
    ]

    salvar_csv_github(
        df_dest,
        CAMINHO_DESTINACOES,
        f"Registro destinação processo {id_processo}"
    )

    return novo_id

# =====================================================
# PROCESSOS JÁ DESTINADOS
# =====================================================
if not df_dest.empty:
    df_enc = df_proc.merge(
        df_dest[["id_processo", "destino", "data_saida"]],
        on="id_processo",
        how="inner"
    )

    st.markdown("### 📦 Processos já encaminhados externamente")

    st.dataframe(
        df_enc[[
            "numero_protocolo",
            "numero_referencia",
            "setor_origem",
            "destino",
            "data_saida"
        ]].rename(columns={
            "numero_protocolo": "Processo",
            "numero_referencia": "Referência",
            "setor_origem": "Setor Origem",
            "destino": "Setor Destino",
            "data_saida": "Data da Tramitação"
        }),
        use_container_width=True
    )

# =====================================================
# REMESSA PDF
# =====================================================
st.divider()
st.markdown("## 📄 Remessa de Envio de Processos")

if not df_dest.empty:
    df_remessa = df_proc.merge(
        df_dest[["id_processo", "destino"]],
        on="id_processo"
    )

    df_remessa["label"] = (
        df_remessa["numero_protocolo"] + " - "
        + df_remessa["assunto"] + " (" + df_remessa["destino"] + ")"
    )

    ids_sel = st.multiselect(
        "Selecione os processos",
        df_remessa["id_processo"],
        format_func=lambda x: df_remessa.loc[
            df_remessa["id_processo"] == x, "label"
        ].values[0]
    )

    if ids_sel and st.button("📄 Gerar Remessa em PDF"):
        dados_pdf = df_remessa[df_remessa["id_processo"].isin(ids_sel)][[
            "destino", "numero_protocolo", "numero_referencia", "assunto"
        ]].rename(columns={"destino": "setor_destino"}).to_dict("records")

        caminho_pdf = os.path.join(tempfile.gettempdir(), "remessa_envio.pdf")
        gerar_pdf_remessa_multi_setor(dados_pdf, caminho_pdf)

        with open(caminho_pdf, "rb") as f:
            st.download_button(
                "⬇️ Baixar Remessa",
                f,
                file_name="remessa_envio.pdf",
                mime="application/pdf"
            )

# =====================================================
# DESTINAÇÃO INDIVIDUAL
# =====================================================
st.divider()
st.markdown("## 📤 Encaminhamento Externo")

ids_ja = df_dest["id_processo"].unique() if not df_dest.empty else []

df_disp = df_proc[
    (df_proc["status"] == "Em Trâmite") &
    (~df_proc["id_processo"].isin(ids_ja))
]

if df_disp.empty:
    st.info("Nenhum processo disponível.")
    st.stop()

id_sel = st.selectbox(
    "Selecione o Processo",
    df_disp["id_processo"],
    format_func=lambda x: f"{df_disp.loc[df_disp['id_processo']==x,'numero_protocolo'].values[0]}"
)

proc = df_disp[df_disp["id_processo"] == id_sel].iloc[0]

destinos = df_setores_destino[df_setores_destino["ativo"] == 1]["setor_destino"]

destino = st.selectbox("Setor de Destino", destinos)
obs = st.text_area("Observação")

if st.button("📦 Registrar Tramitação"):
    data = datetime.now().strftime("%d/%m/%Y %H:%M")

    registrar_destinacao(
        id_sel,
        data,
        st.session_state["usuario"],
        destino,
        obs
    )

    df_proc.loc[
        df_proc["id_processo"] == id_sel,
        ["status", "acao"]
    ] = ["Arquivado", "Arquivado / Destinado"]

    salvar_csv_github(
        df_proc,
        CAMINHO_PROC,
        f"Arquivamento processo {id_sel}"
    )

    st.success(f"✅ Processo encaminhado para {destino}")

# =====================================================
# DESARQUIVAMENTO
# =====================================================
st.divider()
st.markdown("## ♻️ Desarquivar Processo")

df_arq = df_proc[df_proc["status"] == "Arquivado"]

if not df_arq.empty:
    labels = (
        df_arq["numero_protocolo"].astype(str)
        + " - "
        + df_arq["assunto"]
    )

    mapa = dict(zip(labels, df_arq["id_processo"]))

    sel = st.selectbox("Selecione o processo", mapa.keys())
    obs_des = st.text_area("Observação")

    if st.button("♻️ Desarquivar"):
        df_proc.loc[
            df_proc["id_processo"] == mapa[sel],
            ["status", "acao"]
        ] = ["Em Trâmite", "Desarquivado"]

        salvar_csv_github(
            df_proc,
            CAMINHO_PROC,
            f"Desarquivamento processo {mapa[sel]}"
        )

        st.success("✅ Processo desarquivado com sucesso.")
