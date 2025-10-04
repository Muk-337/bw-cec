import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Configuração da página
st.set_page_config(page_title="Dashboard Expandida", layout="wide")

# ================== HEADER ==================
st.markdown("## 📊 Dashboard Interativo Expandido")
st.info("Header: Título + Filtros")

col1, col2 = st.columns(2)
with col1:
    categoria = st.selectbox("Filtro Categoria", ["Opção A", "Opção B", "Opção C"])
with col2:
    valor = st.slider("Filtro Numérico", 0, 100, 50)

st.markdown("---")

# ================== SIDEBAR ==================
st.sidebar.title("🔧 Menu Principal")
menu = st.sidebar.radio("Escolha uma função", 
                        ["Gráfico/Mapa", "Estatísticas", "Tabela de Dados ", "SIDEFOOTER"])

# ================== BLOCO PRINCIPAL ==================
if menu == "Gráfico/Mapa":
    st.subheader("📍 Gráfico / Mapa")
    fullscreen = st.checkbox("Tela cheia do mapa?", value=False)
    
    if fullscreen:
        st.markdown("<style>body {margin: 0; padding: 0;}</style>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(70,35))
    else:        fig, ax = plt.subplots(figsize=(50,25))
    
    ax.plot([1, 2, 3, 4, 5], [10, 20, 15, 25, 30], marker="o")
    ax.set_title("Exemplo de Série Temporal")
    st.pyplot(fig)

elif menu == "Estatísticas":
    st.subheader("📊 Estatísticas")
    with st.expander("Abrir Estatísticas"):
        stats = {"Média": 42, "Máximo": 99, "Mínimo": 10}
        st.write(stats)

elif menu == "Tabela de Dados":
    st.subheader("📑 Tabela de Dados (scroll)")
    df = pd.DataFrame(np.random.randn(200, 6), columns=list("ABCDEF"))
    st.dataframe(df, use_container_width=True, height=400)  # scroll vertical

elif menu == "SIDEFOOTER":
    st.caption("📌 Footer: \n"
    "Créditos: CEC 2 TEAM: Murilo Frota, Gabriel Parisi, Pedro 01, "
    "Lucca Augusto, GuiGuilherme Ceccon, Estevão  \n"
    "Explicação: Projeto BLOOMWATCH feita pela equipe representante da segunda unidade "
    "do Colégio Espaço Cultural. \n"
    "V:3.2"
)

# ================== FOOTER ==================
st.markdown("---")
st.caption(
    "📌 Footer: \n"
    "Créditos: CEC 2 TEAM: Murilo Frota, Gabriel Parisi, Pedro 01, "
    "Lucca Augusto, GuiGuilherme Ceccon, Estevão  \n"
    "Explicação: Projeto BLOOMWATCH feita pela equipe representante da segunda unidade "
    "do Colégio Espaço Cultural."
)

