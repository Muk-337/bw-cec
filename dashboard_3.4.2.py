import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Dashboard Expandida - Fullscreen Map", layout="wide")

# ---------------------------
# Dados de exemplo (fixos)
# ---------------------------
base_df = pd.DataFrame({
    "lat": [-14.2, 37.1, 20.6, 61.5, -33.9, 55.8],
    "lon": [-51.9, -95.7, 78.9, 105.3, 151.2, 37.6],
    "pais": ["Brasil", "EUA", "Índia", "Rússia", "Austrália", "Rússia(EU)"],
    "valor": [30, 50, 40, 20, 45, 35],
    "categoria": ["A", "B", "A", "C", "B", "C"]
})

# ---------------------------
# Helpers
# ---------------------------
def make_map(df, mode3d):
    proj = "orthographic" if mode3d else "natural earth"
    fig = px.scatter_geo(
        df,
        lat="lat",
        lon="lon",
        color="valor",
        hover_name="pais",
        projection=proj,
        color_continuous_scale="RdYlBu_r",
        size="valor",
        size_max=25,
    )
    fig.update_geos(showcountries=True, showcoastlines=True, showland=True,
                    landcolor="rgb(20,20,20)", oceancolor="rgb(10,10,30)", showocean=True)
    # Visuals: dark background
    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor="black",
        plot_bgcolor="black",
        font_color="white",
        coloraxis_colorbar=dict(title="valor"),
        height=700
    )
    return fig

def filtered_df_for_category(df, category):
    if category == "Todas":
        return df.copy()
    return df[df["categoria"] == category].copy()

# ---------------------------
# UI: Header + global controls
# ---------------------------
st.title("🌍 Dashboard Expandida — Modo Dinâmico")
st.write("Use o checkbox para alternar Mapa em Tela Cheia. Fora do modo tela cheia, a sidebar contém as funções principais (cada botão = categoria/visão).")

# fullscreen toggle (controla comportamento)
if "fullscreen" not in st.session_state:
    st.session_state.fullscreen = False

fullscreen = st.checkbox("🗺️ Mapa em tela cheia", value=st.session_state.fullscreen)
st.session_state.fullscreen = fullscreen

st.markdown("---")

# ---------------------------
# COMPORTAMENTO FORA DA TELA CHEIA
# ---------------------------
if not fullscreen:
    # Sidebar como menu principal (cada botão = categoria / função)
    st.sidebar.title("📂 Menu (fora da tela cheia)")
    menu_choice = st.sidebar.radio("Escolha uma função/categoria:",
                                   ["Mapa", "Estatísticas", "Tabela de Dados", "Categoria A", "Categoria B", "Categoria C"])

    # Quando o menu escolhe uma categoria, ajusta os dados
    category_map = {
        "Categoria A": "A",
        "Categoria B": "B",
        "Categoria C": "C"
    }

    # determina df usado
    if menu_choice in category_map:
        df = filtered_df_for_category(base_df, category_map[menu_choice])
    else:
        # Map / Estatísticas / Tabela usam tudo, exceto se o usuário quiser filtrar por selector abaixo
        df = base_df.copy()

    # Small header filters (aparecem fora da tela cheia)
    cols = st.columns([1, 2, 2])
    with cols[0]:
        st.write("Filtros rápidos")
    with cols[1]:
        cat_sel = st.selectbox("Filtro de categoria (preview)", ["Todas", "A", "B", "C"])
    with cols[2]:
        min_val = st.slider("Valor mínimo", min_value=0, max_value=100, value=0)

    if cat_sel != "Todas":
        df = df[df["categoria"] == cat_sel]
    df = df[df["valor"] >= min_val]

    st.markdown("### Conteúdo principal")
    if menu_choice == "Mapa":
        # mapa normal (não-fullscreen)
        fig = make_map(df, mode3d=False)
        st.plotly_chart(fig, use_container_width=True)
    elif menu_choice == "Estatísticas":
        st.subheader("📊 Estatísticas")
        st.write({
            "Contagem": int(df.shape[0]),
            "Média (valor)": float(df["valor"].mean()) if not df.empty else None,
            "Máximo (valor)": int(df["valor"].max()) if not df.empty else None,
            "Mínimo (valor)": int(df["valor"].min()) if not df.empty else None
        })
        st.markdown("Dados usados (preview):")
        st.dataframe(df, height=300, use_container_width=True)
    elif menu_choice == "Tabela de Dados":
        st.subheader("📑 Tabela (scroll)")
        st.dataframe(df, height=400, use_container_width=True)
    else:
        # Categoria A/B/C quick view
        st.subheader(f"🔎 Visualização: {menu_choice}")
        st.dataframe(df, height=350, use_container_width=True)

    st.markdown("---")
    st.caption("📌 Para entrar no modo tela cheia marque 'Mapa em tela cheia' no topo.")

# ---------------------------
# COMPORTAMENTO NO MODO TELA CHEIA
# ---------------------------
else:
    # FULLSCREEN MODE: layout com duas colunas: mapa grande + sidebar flutuante (dentro do mapa area)
    # Left (main) column (grande) and Right (floating) column (estreita)
    main_col, float_col = st.columns([8, 2])

    # --- Main column: Map + overlap filters (simulado) ---
    with main_col:
        st.markdown("### 🗺️ Mapa — Modo Tela Cheia (filtros flutuantes em baixo)")
        # Map options inside fullscreen mode
        mode3d = st.radio("Visão do mapa:", ["3D (Globo)", "2D (Mapa)"], horizontal=True)
        mode3d_bool = (mode3d == "3D (Globo)")

        # Category filter inside the map (this is the map-internal filter)
        cat_inside = st.selectbox("Categoria (mapa)", ["Todas", "A", "B", "C"])
        min_val_inside = st.slider("Valor mínimo (mapa)", 0, 100, 0)

        # Build df for the map
        df_map = base_df.copy()
        if cat_inside != "Todas":
            df_map = df_map[df_map["categoria"] == cat_inside]
        df_map = df_map[df_map["valor"] >= min_val_inside]

        fig = make_map(df_map, mode3d_bool)
        st.plotly_chart(fig, use_container_width=True)

        # "Barra de filtros" visual: colocada logo abaixo do mapa na mesma coluna
        st.markdown(
            """
            <style>
            .map-filters {
                background: rgba(0,0,0,0.55);
                padding: 10px;
                border-radius: 8px;
                color: white;
                margin-top: -60px;  /* sobe pra sobrepor o mapa visualmente */
                margin-bottom: 20px;
            }
            .map-filters .stSlider, .map-filters .stSelectbox {
                color: white;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        st.markdown(f'<div class="map-filters"> 🔎 Filtros (dentro do mapa): Categoria = <b>{cat_inside}</b> • Valor mínimo = <b>{min_val_inside}</b></div>', unsafe_allow_html=True)

    # --- Floating column: flutuante dentro do modo fullscreen (simula sidebar dentro do mapa) ---
    with float_col:
        st.markdown("### ⚙️ Painel flutuante")
        # Pequenos botões para mostrar conteúdo (Estatísticas / Tabela)
        if "show_stats" not in st.session_state:
            st.session_state.show_stats = False
        if "show_table" not in st.session_state:
            st.session_state.show_table = False

        if st.button("📊 Estatísticas"):
            st.session_state.show_stats = not st.session_state.show_stats
            st.session_state.show_table = False

        if st.button("📑 Tabela"):
            st.session_state.show_table = not st.session_state.show_table
            st.session_state.show_stats = False

        st.markdown("---")
        st.markdown("🔁 Ações rápidas")
        if st.button("🔙 Sair Tela Cheia"):
            st.session_state.fullscreen = False
            st.session_state.show_stats = False
            st.session_state.show_table = False
            st.experimental_rerun()

        # Mostrar conteúdo dentro da coluna flutuante
        if st.session_state.show_stats:
            st.markdown("#### 📈 Estatísticas (do mapa atual)")
            st.write({
                "Contagem": int(df_map.shape[0]),
                "Média (valor)": float(df_map["valor"].mean()) if not df_map.empty else None,
                "Máximo (valor)": int(df_map["valor"].max()) if not df_map.empty else None,
                "Mínimo (valor)": int(df_map["valor"].min()) if not df_map.empty else None
            })
        if st.session_state.show_table:
            st.markdown("#### 📋 Tabela (do mapa atual)")
            st.dataframe(df_map, height=380, use_container_width=True)

    # Nota / instruções rápidas
    st.markdown("---")
    st.caption("Modo Tela Cheia: filtros do mapa estão abaixo do mapa; funções principais (estatísticas/tabela) estão na barra flutuante à direita. Para voltar ao layout normal, use 'Sair Tela Cheia' no painel flutuante ou desmarque o checkbox no topo.")

