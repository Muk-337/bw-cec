import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import fastkml as fk
import plotly as pt

footer = "Créditos: CEC 2 TEAM: Murilo Frota, Gabriel Parisi, Pedro 01, "
"Lucca Augusto, GuiGuilherme Ceccon, Estevão  \n"
"Explicação: Projeto BLOOMWATCH feita pela equipe representante da segunda unidade "
"do Colégio Espaço Cultural. \n"

"V:3.2 \n"

# Configuração da página
st.set_page_config(page_title="Dashboard Prototype", layout="wide")

# ================== HEADER ==================
st.markdown("## 📊 Dashboard Expandida (Wireframe Style)")
st.info("Header: aqui entram Título + Filtros")
col1, col2 = st.columns(2)
with col1:
    st.selectbox("Filtro Categoria", ["Opção A", "Opção B", "Opção C", "Opção extra baseada em filtros"])
with col2:
    st.slider("Filtro Numérico", 0, 100, 50)

st.markdown("---")

# ================== SIDEBAR ==================
st.sidebar.title("🔧 Sidebar")
st.sidebar.button("Botão 1")
st.sidebar.button("Botão 2")
st.sidebar.button("Botão 3")





# ================== BLOCO 1 ==================
st.subheader("📍 Bloco 1: Gráfico / Mapa")
with st.expander("Abrir Gráfico/Mapa"):
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3, 4], [10, 20, 15, 30], marker="o")
    ax.set_title("Exemplo de Série Temporal")
    st.pyplot(fig)

# ================== BLOCO 2 ==================
st.subheader("📊 Bloco 2: Estatísticas")
with st.expander("Abrir Estatísticas"):
    stats = {"Média": 42, "Máximo": 99, "Mínimo": 10}
    st.write(stats)

# ================== BLOCO 3 (Tabela Scrollável) ==================
st.subheader("📑 Bloco 3: Tabela de Dados (scroll)")
df = pd.DataFrame(np.random.randn(200, 6), columns=list("ABCDEF"))
st.dataframe(df, use_container_width=True, height=400)  # scroll automático

# ================= SIDEFOOTER ===============
st.subheader("FOOTER")
st.caption("📌 Footer: \n"
    "Créditos: CEC 2 TEAM: Murilo Frota, Gabriel Parisi, Pedro 01, "
    "Lucca Augusto, GuiGuilherme Ceccon, Estevão  \n"
    "Explicação: Projeto BLOOMWATCH feita pela equipe representante da segunda unidade "
    "do Colégio Espaço Cultural. \n"

    "V:3.2 \n"
)

# ================== FOOTER ==================
st.markdown("---")
st.caption(
    "📌 Footer: \n"
    "Créditos: CEC 2 TEAM: Murilo Frota, Gabriel Parisi, Pedro 01, "
    "Lucca Augusto, GuiGuilherme Ceccon, Estevão  \n"
    "Explicação: Projeto BLOOMWATCH feita pela equipe representante da segunda unidade "
    "do Colégio Espaço Cultural. \n"
    "V:3.2"

)