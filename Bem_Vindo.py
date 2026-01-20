import streamlit as st
import pandas as pd
import os

# =====================================================
# CONFIGURAÇÃO GERAL
# =====================================================
st.set_page_config(
    page_title="Protocolo Interno",
    page_icon="📂",
    layout="wide"
)

CAMINHO_USUARIOS = "data/usuarios.csv"

# =====================================================
# AJUSTES VISUAIS (FÁCIL DE PERSONALIZAR)
# =====================================================

COR_PRINCIPAL = "#1f77b4"   # azul padrão
COR_TITULO = "#1f77b4"    
COR_TEXTO = "#334155"
FONTE_TITULO = "Inter, Arial, sans-serif"
FONTE_TEXTO = "Inter, Arial, sans-serif"

LARGURA_PAINEL = "1100px"

st.markdown(
    """
    <style>
        /* Remove espaço excessivo no topo */
        .block-container {
            padding-top: 1.5rem !important;
        }

        .titulo-central {
            text-align: center;
            font-size: 3.6rem;
            font-weight: 700;
            color: #1f77b4;
            margin-top: 0;          /* 🔧 importante */
            margin-bottom: 0.5rem;
        }

        .subtitulo-central {
            text-align: center;
            font-size: 1.1rem;
            color: #555;
            margin-bottom: 2rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# FUNÇÕES
# =====================================================
def carregar_usuarios():
    if not os.path.exists(CAMINHO_USUARIOS):
        df = pd.DataFrame(columns=["usuario", "senha", "perfil", "setor"])
        df.to_csv(CAMINHO_USUARIOS, index=False)
    return pd.read_csv(CAMINHO_USUARIOS)

def autenticar(usuario, senha):
    df = carregar_usuarios()
    user = df[(df["usuario"] == usuario) & (df["senha"] == senha)]
    if user.empty:
        return False, None
    return True, user.iloc[0]

# =====================================================
# CONTROLE DE SESSÃO
# =====================================================
if "logado" not in st.session_state:
    st.session_state.logado = False

# =====================================================
# LOGIN (ÚNICO)
# =====================================================
if not st.session_state.logado:
    st.title("🔐 Acesso Restrito")

    col1, col2 = st.columns(2)

    with col1:
        usuario = st.text_input("Usuário")

    with col2:
        senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        ok, dados = autenticar(usuario, senha)
        if ok:
            st.session_state.logado = True
            st.session_state.usuario = dados["usuario"]
            st.session_state.perfil = dados["perfil"]
            st.session_state.setor = dados["setor"]
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

    st.stop()

# =====================================================
# SIDEBAR (USUÁRIO LOGADO)
# =====================================================
st.sidebar.success(f"👤 {st.session_state.usuario}")
st.sidebar.write(f"Perfil: **{st.session_state.perfil}**")
st.sidebar.write(f"Setor: **{st.session_state.setor}**")

if st.sidebar.button("🚪 Sair"):
    st.session_state.clear()
    st.rerun()

# =====================================================
# TELA INICIAL (HOME)
# =====================================================

st.markdown('<div class="bloco-central">', unsafe_allow_html=True)
st.markdown('<div class="titulo-central">Protocolo Interno</div>', unsafe_allow_html=True)

# 🔔 AVISO DO FLUXO
st.markdown("### 🔔 Antes de realizar andamentos")

st.markdown(
    """
    <a href="https://script.google.com/macros/s/AKfycbxgG_PBpiWuGUPmH5eKQaZLKVRn4DA5pt8RvT1Jc6iH1MrNiQR23OixQ-h2eFMc761S/exec"
       target="_blank"
       style="
            display: inline-block;
            padding: 0.5rem 1rem;
            background-color: #1f77b4;
            color: white;
            text-decoration: none;
            border-radius: 0.5rem;
            font-weight: 600;
            text-align: center;
            width: 100%;
            max-width: 220px;
        ">
        📄 Consultar Fluxo
    </a>
    """,
    unsafe_allow_html=True
)

st.divider()
st.subheader("🚀 Acesso rápido aos módulos")

# =========================
# FUNÇÃO CARD
# =========================
def card_modulo(titulo, descricao, pagina):
    chave = f"btn_{pagina.replace('/', '_').replace('.py','')}"
    with st.container(border=True):
        st.markdown(f"### {titulo}")
        st.caption(descricao)
        if st.button("Acessar", key=chave, use_container_width=True):
            st.switch_page(pagina)

# =========================
# GRID DE CARDS
# =========================

col1, col2, col3 = st.columns(3)

with col1:
    card_modulo(
        "📥 Protocolo",
        "Entrada",
        "pages/1_Protocolo.py"
    )

with col2:
    card_modulo(
        "🔄 Tramitação",
        "Encaminhamento",
        "pages/2_Tramitacao.py"
    )

with col3:
    card_modulo(
        "🔍 Consulta",
        "Pesquisa",
        "pages/3_Consulta_Processos.py"
    )

col4, col5, col6 = st.columns(3)

with col4:
    card_modulo(
        "🗂️ Gestão",
        "Gestão Administrativa",
        "pages/4_Gestão.py"
    )

with col5:
    card_modulo(
        "📦 Arquivo",
        "Tramitação Externa",
        "pages/5_Arquivo.py"
    )

with col6:
    card_modulo(
        "👤 Minha Conta",
        "Dados do usuário",
        "pages/6_Minha_Conta.py"
    )

st.markdown("<br>", unsafe_allow_html=True)

with st.container():
    col_centro = st.columns([1, 2, 1])[1]  # coluna central mais larga

    with col_centro:
        card_modulo(
            "⚙️ Administração",
            "Configuração",
            "pages/7_Administrador.py"
        )


st.markdown("</div>", unsafe_allow_html=True)

