import streamlit as st
import pandas as pd
import os
from datetime import datetime
import tempfile

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
# CAMINHOS DOS ARQUIVOS
# =====================================================
CAMINHO_PROC = "data/processos.csv"
CAMINHO_DESTINACOES = "data/destinacoes.csv"
CAMINHO_SETOR_DESTINO = "data/setores_destinos.csv"

# =====================================================
# CONTROLE DE ACESSO
# =====================================================
USUARIOS_AUTORIZADOS = ["admin", "secretario", "ana"]
ID_SETORES_PROTOCOLO = [1, 2]

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
    return novo_id


# =====================================================
# BLOQUEIO DE ACESSO
# =====================================================
if "usuario" not in st.session_state or st.session_state["usuario"] not in USUARIOS_AUTORIZADOS:
    st.error("⛔ Acesso restrito ao Protocolo, Secretário ou Administrador.")
    st.stop()

# =====================================================
# CARREGAMENTO DOS DADOS
# =====================================================
df_proc = carregar_csv(CAMINHO_PROC)
df_dest = carregar_csv(CAMINHO_DESTINACOES)
df_setores_destino = carregar_csv(CAMINHO_SETOR_DESTINO)

# =====================================================
# PROCESSOS JÁ DESTINADOS (CONSULTA)
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
        })
        .reset_index(drop=True),
        use_container_width=True
    )

# =====================================================
# REMESSA DE ENVIO (MULTI-SELEÇÃO)
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
        df_remessa["numero_protocolo"] + " - " +
        df_remessa["assunto"] + " (" +
        df_remessa["destino"] + ")"
    )

    ids_sel = st.multiselect(
        "Selecione os processos que irão compor a remessa",
        df_remessa["id_processo"],
        format_func=lambda x: df_remessa.loc[
            df_remessa["id_processo"] == x, "label"
        ].values[0]
        placeholder="Selecione um ou mais processos..."
    )

    if ids_sel:
        df_sel = df_remessa[df_remessa["id_processo"].isin(ids_sel)]

        if st.button("📄 Gerar Remessa em PDF"):
            processos_pdf = df_sel[[
                "destino",
                "numero_protocolo",
                "numero_referencia",
                "assunto"
            ]].rename(columns={
                "destino": "setor_destino"
            }).to_dict("records")

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
    (df_proc["id_setor_atual"].isin(ID_SETORES_PROTOCOLO)) &
    (df_proc["status"] == "Em Trâmite") &
    (~df_proc["id_processo"].isin(ids_ja_destinados))
]

if df_disponiveis.empty:
    st.info("📭 Não há processos disponíveis para nova tramitação.")
    st.stop()

id_proc_sel = st.selectbox(
    "Selecione o Processo para Tramitação",
    df_disponiveis["id_processo"],
    format_func=lambda x: (
        f"{df_disponiveis.loc[df_disponiveis['id_processo'] == x, 'numero_protocolo'].values[0]}"
        f" - {df_disponiveis.loc[df_disponiveis['id_processo'] == x, 'assunto'].values[0]}"
    )
)

proc = df_disponiveis[df_disponiveis["id_processo"] == id_proc_sel].iloc[0]

st.markdown("### 📄 Dados do Processo")
st.write(
    f"**Referência:** {proc['numero_referencia']}  |  "
    f"**Setor de Origem:** {proc['setor_origem']}"
)

st.divider()
st.markdown("### 📤 Envio")

destinos_ativos = df_setores_destino[df_setores_destino["ativo"] == 1]

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
        protocolista=st.session_state["usuario"],
        destino=destino_sel,
        observacao=observacao
    )

    df_proc.loc[
        df_proc["id_processo"] == id_proc_sel,
        ["status", "acao"]
    ] = ["Arquivado", "Arquivado / Destinado"]

    df_proc.to_csv(CAMINHO_PROC, index=False)

    st.success(
        f"✅ Processo arquivado e encaminhado para {destino_sel} "
        f"(Registro nº {novo_id})"
    )
# =====================================================
# 🔓 DESARQUIVAMENTO DE PROCESSOS
# =====================================================
st.divider()
st.markdown("## ♻️ Desarquivar Processo")

df_arquivados = df_proc[df_proc["status"] == "Arquivado"]

if df_arquivados.empty:
    st.info("📂 Não há processos arquivados disponíveis para desarquivamento.")
else:
    df_arquivados["label"] = (
        df_arquivados["numero_protocolo"].astype(str)
        + " - "
        + df_arquivados["assunto"].astype(str)
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
            df_proc["id_processo"] == id_proc_des,
            ["status", "acao"]
        ] = ["Em Trâmite", "Desarquivado"]

        df_proc.to_csv(CAMINHO_PROC, index=False)

        st.success("✅ Processo desarquivado com sucesso e liberado para tramitação.")


