# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
from fastkml import kml
from PIL import Image
import geopandas as gpd
from astropy.io import fits
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="NASA Data Explorer Ultimate", layout="wide")
st.title("🌌 NASA Data Explorer + Dashboard 3D")

uploaded_file = st.file_uploader(
    "Carregue um arquivo (CSV, JSON, GeoJSON, KML, FITS, PNG, JPG)", 
    type=["csv", "json", "geojson", "kml", "fits", "png", "jpg", "jpeg"]
)

df = None  # DataFrame

if uploaded_file:
    ext = uploaded_file.name.lower().split(".")[-1]

    # CSV
    if ext == "csv":
        df = pd.read_csv(uploaded_file, low_memory=False)
        st.success("✅ CSV carregado!")

    # JSON
    elif ext == "json":
        data = json.load(uploaded_file)
        try:
            df = pd.json_normalize(data)
            st.success("✅ JSON carregado como tabela!")
        except Exception:
            st.write("Conteúdo JSON bruto:")
            st.json(data)

    # GEOJSON
    elif ext == "geojson":
        gdf = gpd.read_file(uploaded_file)
        df = pd.DataFrame(gdf.drop(columns="geometry"))
        st.map(gdf)
        st.success("✅ GeoJSON carregado e exibido no mapa!")

    # KML
    elif ext == "kml":
        k = kml.KML()
        k.from_string(uploaded_file.read())
        features = list(k.features())
        placemarks = []
        def extract_features(feats):
            for f in feats:
                if hasattr(f, "features"):
                    yield from extract_features(f.features())
                else:
                    yield f
        for f in extract_features(features):
            if f.geometry:
                coords = list(f.geometry.coords)
                for lon, lat, *_ in coords:
                    placemarks.append({"name": f.name, "latitude": lat, "longitude": lon})
        df = pd.DataFrame(placemarks)
        st.success("✅ KML convertido em tabela (lat/lon)!")

    # FITS
    elif ext == "fits":
        hdul = fits.open(uploaded_file)
        st.write("📂 HDUs disponíveis:", [hdu.name for hdu in hdul])

        if isinstance(hdul[1], fits.BinTableHDU):  
            df = pd.DataFrame(np.array(hdul[1].data).byteswap().newbyteorder())
            st.success("✅ FITS carregado como tabela!")
        else:
            data = hdul[0].data
            if data is not None:
                st.image(data, caption="Imagem FITS", clamp=True)
                st.info("ℹ️ FITS exibido como imagem.")
            else:
                st.warning("⚠️ FITS sem dados de imagem/tabela.")
        hdul.close()

    # IMAGENS
    elif ext in ["png", "jpg", "jpeg"]:
        img = Image.open(uploaded_file)
        st.image(img, caption=uploaded_file.name, use_column_width=True)
        st.info("ℹ️ Arquivo de imagem exibido.")

    # ---- Se houver DataFrame tabular ----
    if df is not None and not df.empty:
        st.subheader("📊 Dados carregados")
        st.write("Dimensões:", df.shape)
        st.dataframe(df.head(10))

        # Filtros
        st.subheader("🔎 Filtros")
        colunas = df.columns.tolist()
        col_filtro = st.multiselect("Escolha colunas para filtrar", colunas)
        subset = df.copy()
        for col in col_filtro:
            valores = st.multiselect(f"Valores para {col}", df[col].dropna().unique())
            if valores:
                subset = subset[subset[col].isin(valores)]

        st.write("📂 Subconjunto filtrado", subset.shape)
        st.dataframe(subset.head(20))

        # Gráficos
        st.subheader("📈 Visualizações")
        tipo_plot = st.radio("Escolha:", ["Série Temporal", "Dispersão Geográfica", "Globo 3D"])

        if tipo_plot == "Série Temporal":
            col_data = st.selectbox("Coluna de data", colunas)
            col_valor = st.selectbox("Coluna de valor", colunas)
            if st.button("Gerar série temporal"):
                df2 = subset.copy()
                df2[col_data] = pd.to_datetime(df2[col_data], errors="coerce")
                df2 = df2.dropna(subset=[col_data, col_valor])
                df2 = df2.set_index(col_data)
                fig, ax = plt.subplots(figsize=(10,4))
                ax.plot(df2.index, df2[col_valor], marker="o")
                st.pyplot(fig)

        if tipo_plot == "Dispersão Geográfica":
            lat_col = st.selectbox("Coluna de latitude", colunas)
            lon_col = st.selectbox("Coluna de longitude", colunas)
            if st.button("Gerar mapa"):
                fig, ax = plt.subplots(figsize=(6,6))
                ax.scatter(subset[lon_col], subset[lat_col], s=20, alpha=0.7)
                st.pyplot(fig)

        if tipo_plot == "Globo 3D":
            lat_col = st.selectbox("Coluna de latitude", colunas)
            lon_col = st.selectbox("Coluna de longitude", colunas)
            valor_col = st.selectbox("Coluna de valor (tamanho/cor)", colunas)
            if st.button("Gerar globo 3D"):
                lats = subset[lat_col].astype(float).tolist()
                lons = subset[lon_col].astype(float).tolist()
                valores = subset[valor_col].astype(float).tolist()
                fig = go.Figure()
                fig.add_trace(go.Scattergeo(
                    lon=lons, lat=lats,
                    text=[f"{lat},{lon}: {v}" for lat, lon, v in zip(lats, lons, valores)],
                    mode="markers",
                    marker=dict(
                        size=[max(5, v/2) for v in valores],
                        color=valores,
                        colorscale="RdYlBu_r",
                        cmin=min(valores),
                        cmax=max(valores),
                        line=dict(width=0)
                    )
                ))
                fig.update_geos(
                    projection_type="orthographic",
                    showcountries=True, showcoastlines=True, showland=True,
                    landcolor="rgb(20,20,20)",
                    oceancolor="rgb(10,10,30)",
                    showocean=True,
                )
                fig.update_layout(
                    title="🌍 Globo Interativo",
                    paper_bgcolor="black",
                    geo=dict(bgcolor="black"),
                    font=dict(color="white")
                )
                st.plotly_chart(fig, use_container_width=True)

else:
    st.info("➡️ Carregue um arquivo para começar.")
