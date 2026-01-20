import streamlit as st
import pandas as pd
from utils import registrar_andamento

st.set_page_config(page_title="Tramitação de Processos", layout="wide")

# 🔐 BLOQUEIO DE ACESSO
if "usuario" not in st.session_state:
    st.warning("Acesso restrito. Faça login.")
    st.stop()

usuario = st.session_state["usuario"]
setor_usuario = st.session_state.get("setor", "Não informado")

st.title("🧭 Tramitação de Processos")

# =========================================================
# 📂 CARREGAR BASES
# =========================================================

df_proc = pd.read_csv("data/Processos.csv")
df_and = pd.read_csv("data/andamentos.csv")
df_setores = pd.read_csv("data/setores.csv")

df_and["data"] = pd.to_datetime(df_and["data"], errors="coerce")

# =========================================================
# 📌 PROCESSOS NO SETOR DO USUÁRIO
# =========================================================

ultimos_andamentos = (
    df_and.sort_values("data")
    .groupby("id_processo")
    .tail(1)
)

df_proc["setor_atual"] = df_proc["id_processo"].map(
    ultimos_andamentos.set_index("id_processo")["setor_destino"]
)

minha_mesa = df_proc[
    (df_proc["setor_atual"] == setor_usuario) &
    (df_proc["status"] != "Arquivado")
]


st.subheader(f"📌 Processos no setor {setor_usuario}")

if minha_mesa.empty:
    st.info("Nenhum processo no seu setor no momento.")
    st.stop()

# =========================================================
# 🔽 SELEÇÃO DO PROCESSO (NÚMERO + ASSUNTO)
# =========================================================

minha_mesa["label"] = (
    minha_mesa["numero_protocolo"].astype(str)
    + " - "
    + minha_mesa["assunto"].astype(str)
)

opcoes = dict(zip(minha_mesa["label"], minha_mesa["id_processo"]))

label_selecionado = st.selectbox(
    "Selecione o processo",
    options=opcoes.keys()
)

id_processo = opcoes[label_selecionado]

status_processo = df_proc.loc[
    df_proc["id_processo"] == id_processo,
    "status"
].values[0]

if status_processo == "Arquivado":
    st.error("🚫 Este processo está ARQUIVADO e não pode ser tramitado.")
    st.stop()


# =========================================================
# 📜 HISTÓRICO DO PROCESSO (ANTES DO REGISTRO)
# =========================================================

st.subheader("📜 Histórico do Processo")

hist = df_and[df_and["id_processo"] == id_processo].copy()

if hist.empty:
    st.info("Nenhum andamento registrado para este processo.")
else:
    hist["Data/Hora"] = hist["data"].dt.strftime("%d/%m/%Y %H:%M")

    hist_exibir = hist[[
        "Data/Hora",
        "acao",
        "observacao",
        "setor_origem",
        "setor_destino"
    ]].rename(columns={
        "acao": "Ação",
        "observacao": "Observação",
        "setor_origem": "Setor de Origem",
        "setor_destino": "Setor de Destino"
    })

    st.dataframe(
        hist_exibir.sort_values("Data/Hora"),
        use_container_width=True,
        hide_index=True
)


st.divider()

# =========================================================
# ✍️ REGISTRAR ANDAMENTO
# =========================================================

st.subheader("✍️ Registrar Andamento")

acao = st.selectbox(
    "Ação realizada",
    ["Análise", "Parecer", "Atualização", "Encaminhamento", "Conclusão"]
)

observacao = st.text_area("Observações / Parecer")

setores_ativos = df_setores[df_setores["ativo"] == 1]["setor"].tolist()

setor_destino = st.selectbox(
    "Setor de destino",
    options=setores_ativos
)

# último setor para origem
setor_origem = ultimos_andamentos.loc[
    ultimos_andamentos["id_processo"] == id_processo,
    "setor_destino"
].values[0]

if st.button("📤 Registrar andamento"):
    registrar_andamento(
        id_processo=id_processo,
        servidor=usuario,
        acao=acao,
        observacao=observacao,
        setor_origem=setor_origem,
        setor_destino=setor_destino
    )

    id_setor_destino = df_setores.loc[
        df_setores["setor"] == setor_destino,
        "id_setor"
    ].values[0]

    df_proc.loc[
        df_proc["id_processo"] == id_processo,
        ["acao", "setor_atual", "id_setor_atual", "status"]
    ] = [
        acao,
        setor_destino,
        id_setor_destino,
        "Em Trâmite"
    ]

    df_proc.to_csv("data/Processos.csv", index=False)

    st.success(f"✅ Andamento registrado e enviado para {setor_destino}")

