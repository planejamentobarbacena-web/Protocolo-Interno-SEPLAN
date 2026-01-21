import streamlit as st
import pandas as pd
from io import StringIO
from github import Github
from datetime import datetime
import pytz  # <- import para fuso horário

st.set_page_config(page_title="Tramitação de Processos", layout="wide")

# =====================================================
# FUNÇÃO HORÁRIO BRASÍLIA
# =====================================================
def agora_brasilia():
    fuso = pytz.timezone("America/Sao_Paulo")
    return datetime.now(fuso)

# 🔐 BLOQUEIO DE ACESSO
if "usuario" not in st.session_state:
    st.warning("Acesso restrito. Faça login.")
    st.stop()

usuario = st.session_state["usuario"]
setor_usuario = st.session_state.get("setor", "Não informado")

st.title("🧭 Tramitação de Processos")

# =========================================================
# GITHUB CONFIG
# =========================================================
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

# =========================================================
# CAMINHOS
# =========================================================
CAMINHO_PROC = "data/processos.csv"
CAMINHO_AND = "data/andamentos.csv"
CAMINHO_SET = "data/setores.csv"

# =========================================================
# CARREGAR BASES
# =========================================================
try:
    arquivo_proc = repo.get_contents(CAMINHO_PROC, ref=BRANCH)
    df_proc = pd.read_csv(StringIO(arquivo_proc.decoded_content.decode("utf-8")))
except:
    df_proc = pd.DataFrame()

try:
    arquivo_and = repo.get_contents(CAMINHO_AND, ref=BRANCH)
    df_and = pd.read_csv(StringIO(arquivo_and.decoded_content.decode("utf-8")))
except:
    df_and = pd.DataFrame(columns=[
        "id_andamento","id_processo","data","servidor","perfil",
        "acao","observacao","setor_origem","setor_destino"
    ])

try:
    arquivo_set = repo.get_contents(CAMINHO_SET, ref=BRANCH)
    df_setores = pd.read_csv(StringIO(arquivo_set.decoded_content.decode("utf-8")))
except:
    df_setores = pd.DataFrame(columns=["id_setor","setor","ativo"])

# =========================================================
# CONVERSÃO DATA/HORA PARA BRASÍLIA
# =========================================================
df_and["data"] = pd.to_datetime(df_and["data"], errors="coerce").dt.tz_localize('UTC').dt.tz_convert('America/Sao_Paulo')

# =========================================================
# PROCESSOS NO SETOR DO USUÁRIO
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
# SELEÇÃO DO PROCESSO
# =========================================================
minha_mesa["label"] = (
    minha_mesa["numero_protocolo"].astype(str)
    + " - "
    + minha_mesa["assunto"].astype(str)
)
opcoes = dict(zip(minha_mesa["label"], minha_mesa["id_processo"]))

label_selecionado = st.selectbox("Selecione o processo", options=opcoes.keys())
id_processo = opcoes[label_selecionado]

status_processo = df_proc.loc[
    df_proc["id_processo"] == id_processo, "status"
].values[0]

if status_processo == "Arquivado":
    st.error("🚫 Este processo está ARQUIVADO e não pode ser tramitado.")
    st.stop()

# =========================================================
# HISTÓRICO
# =========================================================
st.subheader("📜 Histórico do Processo")
hist = df_and[df_and["id_processo"] == id_processo].copy()

if hist.empty:
    st.info("Nenhum andamento registrado para este processo.")
else:
    hist["Data/Hora"] = hist["data"].dt.strftime("%d/%m/%Y %H:%M")  # <- formato dd/mm/aaaa
    hist_exibir = hist[[
        "Data/Hora","acao","observacao","setor_origem","setor_destino"
    ]].rename(columns={
        "acao":"Ação",
        "observacao":"Observação",
        "setor_origem":"Setor de Origem",
        "setor_destino":"Setor de Destino"
    })
    st.dataframe(hist_exibir.sort_values("Data/Hora"), use_container_width=True, hide_index=True)

st.divider()

# =========================================================
# REGISTRAR ANDAMENTO
# =========================================================
st.subheader("✍️ Registrar Andamento")

acao = st.selectbox(
    "Ação realizada",
    ["Análise","Parecer","Atualização","Encaminhamento","Conclusão"]
)

observacao = st.text_area("Observações / Parecer")

setores_ativos = df_setores[df_setores["ativo"]==1]["setor"].tolist()
setor_destino = st.selectbox("Setor de destino", options=setores_ativos)

setor_origem = ultimos_andamentos.loc[
    ultimos_andamentos["id_processo"]==id_processo,"setor_destino"
].values[0]

if st.button("📤 Registrar andamento"):

    # Novo id_andamento
    novo_and_id = 1 if df_and.empty else int(df_and["id_andamento"].max()) + 1

    novo_andamento = {
        "id_andamento": novo_and_id,
        "id_processo": id_processo,
        "data": agora_brasilia().strftime("%Y-%m-%d %H:%M:%S"),  # <- horário Brasília
        "servidor": usuario,
        "perfil": st.session_state.get("perfil","Servidor"),
        "acao": acao,
        "observacao": observacao,
        "setor_origem": setor_origem,
        "setor_destino": setor_destino
    }

    df_and = pd.concat([df_and, pd.DataFrame([novo_andamento])], ignore_index=True)
    salvar_csv_github(df_and, CAMINHO_AND, f"Andamento {novo_and_id} do processo {id_processo}")

    # Atualiza processos
    id_setor_destino = df_setores.loc[df_setores["setor"]==setor_destino,"id_setor"].values[0]
    df_proc.loc[
        df_proc["id_processo"]==id_processo,
        ["acao","setor_atual","id_setor_atual","status"]
    ] = [acao,setor_destino,id_setor_destino,"Em Trâmite"]
    salvar_csv_github(df_proc, CAMINHO_PROC, f"Atualização do processo {id_processo}")

    st.success(f"✅ Andamento registrado e enviado para {setor_destino}")
