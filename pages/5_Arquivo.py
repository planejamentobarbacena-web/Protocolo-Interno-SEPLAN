import streamlit as st
import pandas as pd
import os
from datetime import datetime
import tempfile
from pdf6_utils import gerar_pdf_remessa_multi_setor
from github import Github

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
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN")
REPO_NAME = st.secrets.get("REPO_NAME")
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

    # Leitura do GitHub ou criação do DataFrame vazio
    try:
        arquivo_dest = repo.get_contents(CAMINHO_DESTINACOES, ref=BRANCH)
        df_dest = pd.read_csv(pd.compat.StringIO(arquivo_dest.decoded_content.decode("utf-8")))
    except:
        df_dest = pd.DataFrame(columns=colunas)

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
        f"Registrar destinação externa de processo {id_processo}"
    )
    return novo_id

# =====================================================
# BLOQUEIO DE ACESSO
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
# CARREGAR DADOS
# =====================================================
col_proc = [
    "id_processo","numero_protocolo","data_entrada","numero_referencia",
    "setor_origem","assunto","descricao","setor_atual","status",
    "id_setor_atual","acao"
]
try:
    arquivo_proc = repo.get_contents(CAMINHO_PROC, ref=BRANCH)
    df_proc = pd.read_csv(pd.compat.StringIO(arquivo_proc.decoded_content.decode("utf-8")))
except:
    df_proc = pd.DataFrame(columns=col_proc)

col_dest = ["id_destinacao","id_processo","data_saida","protocolista","destino","observacao"]
try:
    arquivo_dest = repo.get_contents(CAMINHO_DESTINACOES, ref=BRANCH)
    df_dest = pd.read_csv(pd.compat.StringIO(arquivo_dest.decoded_content.decode("utf-8")))
except:
    df_dest = pd.DataFrame(columns=col_dest)

df_setores_destino = carregar_csv(CAMINHO_SETOR_DESTINO)

# =====================================================
# PROCESSOS JÁ DESTINADOS
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
# REMESSA DE ENVIO (PDF)
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

    df_remessa["label"] = (
        df_remessa["numero_protocolo"].astype(str) + " - " +
        df_remessa["assunto"].astype(str) + " (" +
        df_remessa["destino"].astype(str) + ")"
    )

    ids_sel = st.multiselect(
        "Selecione os processos que irão compor a remessa",
        df_remessa["id_processo"].tolist(),
        format_func=lambda x: df_remessa.loc[df_remessa["id_processo"] == x, "label"].values[0]
    )

    if ids_sel and st.button("📄 Gerar Remessa em PDF"):
        df_sel = df_remessa[df_remessa["id_processo"].isin(ids_sel)]
        processos_pdf = df_sel[[
            "destino","numero_protocolo","numero_referencia","assunto"
        ]].rename(columns={"destino":"setor_destino"}).to_dict("records")

        caminho_pdf = os.path.join(tempfile.gettempdir(), "remessa_envio_processos.pdf")
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

# FILTRAR PELOS PROCESSOS DO SETOR DE PROTOCOLO E STATUS EM TRÂMITE
ID_SETORES_PROTOCOLO = [1]  # Defina conforme seu setor de protocolo
df_disponiveis = df_proc[
    (df_proc["status"] == "Em Trâmite") &
    (df_proc["id_setor_atual"].isin(ID_SETORES_PROTOCOLO)) &
    (~df_proc["id_processo"].isin(ids_ja_destinados))
]

if df_disponiveis.empty:
    st.info("📭 Não há processos disponíveis para destinação externa.")
else:
    id_proc_sel = st.selectbox(
        "Selecione o Processo",
        df_disponiveis["id_processo"],
        format_func=lambda x: (
            f"{df_disponiveis.loc[df_disponiveis['id_processo']==x,'numero_protocolo'].values[0]} - "
            f"{df_disponiveis.loc[df_disponiveis['id_processo']==x,'assunto'].values[0]}"
        )
    )

    proc = df_disponiveis[df_disponiveis["id_processo"]==id_proc_sel].iloc[0]

    st.markdown("### 📄 Dados do Processo")
    st.write(f"**Referência:** {proc['numero_referencia']}  |  **Setor de Origem:** {proc['setor_origem']}")

    st.divider()
    st.markdown("### 📤 Envio")

    destinos_ativos = df_setores_destino[df_setores_destino["ativo"]==1]

    destino_sel = st.selectbox(
        "Selecione o Setor de Destino",
        destinos_ativos["setor_destino"]
    )

    observacao = st.text_area("Observação (opcional)")

    if st.button("📦 Registrar Tramitação"):
        data_saida = datetime.now().strftime("%d/%m/%Y %H:%M")
        novo_id = registrar_destinacao(
            id_processo=id_proc_sel,
            data_saida=data_saida,
            protocolista=usuario_logado,
            destino=destino_sel,
            observacao=observacao
        )

        df_proc.loc[
            df_proc["id_processo"]==id_proc_sel,
            ["status","acao"]
        ] = ["Arquivado","Arquivado / Destinado"]

        salvar_csv_github(
            df_proc,
            CAMINHO_PROC,
            f"Arquivar e destinar processo {id_proc_sel}"
        )

        st.success(f"✅ Processo arquivado e encaminhado ({novo_id})")

# =====================================================
# DESARQUIVAMENTO DE PROCESSOS
# =====================================================
st.divider()
st.markdown("## ♻️ Desarquivar Processo")

df_arquivados = df_proc[df_proc["status"]=="Arquivado"]

if df_arquivados.empty:
    st.info("📂 Não há processos arquivados disponíveis para desarquivamento.")
else:
    df_arquivados["label"] = (
        df_arquivados["numero_protocolo"].astype(str) + " - " + df_arquivados["assunto"].astype(str)
    )

    mapa_proc = dict(zip(df_arquivados["label"], df_arquivados["id_processo"]))

    proc_label = st.selectbox(
        "Selecione o processo arquivado",
        options=mapa_proc.keys(),
        key="desarquivar_proc"
    )

    id_proc_des = mapa_proc[proc_label]

    observacao_des = st.text_area(
        "Observação do desarquivamento",
        value="Processo desarquivado para retomada da tramitação."
    )

    if st.button("♻️ Desarquivar Processo"):
        df_proc.loc[
            df_proc["id_processo"]==id_proc_des,
            ["status","acao"]
        ] = ["Em Trâmite","Desarquivado"]

        salvar_csv_github(
            df_proc,
            CAMINHO_PROC,
            f"Desarquivar processo {id_proc_des}"
        )

        st.success("✅ Processo desarquivado com sucesso e liberado para tramitação.")
