# dashboard_3.py
# Requisitos:
# pip install streamlit folium streamlit-folium pandas numpy

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import html

st.set_page_config(page_title="Dashboard 2D - Projeto Exemplo", layout="wide")

# ------------------------
# Dados de exemplo
# ------------------------
base_df = pd.DataFrame({
    "pais": ["Brasil", "EUA", "Índia", "Rússia", "Austrália", "Canadá"],
    "lat": [-14.2350, 37.0902, 20.5937, 61.5240, -33.8688, 56.1304],
    "lon": [-51.9253, -95.7129, 78.9629, 105.3188, 151.2093, -106.3468],
    "valor": [30, 50, 40, 20, 45, 28],
    "categoria": ["A", "B", "A", "C", "B", "A"]
})

region_map = {
    "Brasil": "América do Sul",
    "EUA": "América do Norte",
    "Canadá": "América do Norte",
    "Índia": "Ásia",
    "Rússia": "Europa/Ásia",
    "Austrália": "Oceania"
}
base_df["regiao"] = base_df["pais"].map(region_map).fillna("Outros")

# ------------------------
# Funções auxiliares
# ------------------------
def filtered_df(df, cat, min_val, region):
    d = df.copy()
    if cat and cat != "Todas":
        d = d[d["categoria"] == cat]
    if region and region != "Todas":
        d = d[d["regiao"] == region]
    if min_val is not None:
        d = d[d["valor"] >= min_val]
    return d

def make_folium_map(df):
    if df.empty:
        center = [0, 0]
    else:
        center = [df["lat"].mean(), df["lon"].mean()]
    m = folium.Map(location=center, zoom_start=2, tiles="CartoDB dark_matter", control_scale=True)
    for _, row in df.iterrows():
        popup_html = f"<b>{html.escape(row['pais'])}</b><br>Valor: {row['valor']}<br>Categoria: {row['categoria']}<br>Região: {row['regiao']}"
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=max(5, 4 + (row["valor"] / 15.0)),
            fill=True,
            fill_color="#ff7f0e",
            fill_opacity=0.9,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)
    return m

# ------------------------
# Sidebar
# ------------------------
with st.sidebar:
    st.markdown("## 🌍 Dashboard 2D - Projeto Exemplo")
    st.markdown("---")

    st.subheader("🔎 Filtros")
    CATEGORIES = ["Todas"] + sorted(base_df["categoria"].unique().tolist())
    REGIONS = ["Todas"] + sorted(base_df["regiao"].unique().tolist())

    cat_sel = st.selectbox("Categoria", CATEGORIES, index=0)
    region_sel = st.selectbox("Região", REGIONS, index=0)
    min_val = st.slider("Valor mínimo", 0, 100, 0)

    st.markdown("---")
    st.subheader("🧾 Créditos")
    st.markdown("_(CEC - 2 TEAM: Murilo; Gabriel; Estevão; Guilherme; Lucca; Pedro.)_")

    st.subheader("💡 Sobre o Projeto")
    st.markdown("_(Projeto baseado no desafio BloomFlower: An Earth Observation Application for Global Flowering Phenology, Desenvolvido pela a equipe representante do Colégio Espaço Cultural para o Hackateen 2025)_")

    st.subheader("🕹️ Como Usar")
    st.markdown("""
    1. Use os filtros acima para selecionar categoria, região e valor mínimo.  
    2. Role a área principal para ver o mapa, estatísticas e tabela.  
    3. Tudo muda automaticamente conforme os filtros.  
    """)

st.sidebar.markdown("#---")
    # --- Patch Notes (expander pronto) ---
    with st.expander("🧩 Patch Notes", expanded=False):
        st.caption("### Versão 3.4.6 (Atual)")
        st.caption("### Versão 3.4.7 (Em Desenvolvimento)")
        st.markdown("""
        - Adição de suporte a múltiplos tipos de dados. (Chegando)
        - Adição de configurações de aparência/acessibilidade. (Chegando)
        - Adição de expanções dos menus. (Chegando)
        - Adição de menus de feedback. (Chegando)
        - Melhoria na performance do mapa. (Chegando)
        - Adição de tradução na interface. (Chegando)
        """)
        
    st.markdown("---")
    st.caption("© 2025 - Dashboard Final Prototype (V:3.4.4")

# ------------------------
# Estilo — remove padding e aplica fade-in
# ------------------------
st.markdown("""
<style>
.main .block-container {
    padding-top: 0rem !important;
    padding-bottom: 0 !important;
    margin-top: 0 !important;
    animation: fadein 0.8s ease-in;
}
@keyframes fadein {
    from {opacity: 0; transform: translateY(15px);}
    to {opacity: 1; transform: translateY(0);}
}
header[data-testid=\"stHeader\"] {
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ------------------------
# Corpo principal
# ------------------------
df = filtered_df(base_df, cat_sel, min_val, region_sel)

# --- Mapa ---
st.markdown("## 🗺️ Mapa Interativo (Filtros aplicados)")
folium_map = make_folium_map(df)
st_folium(folium_map, width="100%", height=680)
st.markdown("---")

# --- Estatísticas ---
st.markdown("## 📊 Estatísticas")
st.write({
    "Contagem": int(df.shape[0]),
    "Média (valor)": float(df["valor"].mean()) if not df.empty else None,
    "Máximo (valor)": int(df["valor"].max()) if not df.empty else None,
    "Mínimo (valor)": int(df["valor"].min()) if not df.empty else None,
})
st.markdown("---")

# --- Tabela ---
st.markdown("## 📋 Tabela de Dados (Filtros aplicados)")
st.dataframe(df, height=600, use_container_width=True)






