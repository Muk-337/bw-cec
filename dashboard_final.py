# dashboard_ND3_final.py
# Requisitos (recomendado):
# pip install streamlit folium streamlit-folium pandas numpy geopandas rasterio pillow astropy folium.plugins fiona pyproj shapely

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import html
from folium.plugins import HeatMap, MarkerCluster
import geopandas as gpd
import json
from io import BytesIO, StringIO
from PIL import Image
import base64
import os
import tempfile
import warnings

# módulos opcionais (nem sempre presentes / podem requerer dependências nativas)
try:
    import rasterio
    from rasterio.plot import reshape_as_image
    from rasterio.warp import transform_bounds
    RASTERIO_AVAILABLE = True
except Exception:
    rasterio = None
    RASTERIO_AVAILABLE = False

try:
    from astropy.io import fits as pyfits
    from astropy.wcs import WCS
    ASTROPY_AVAILABLE = True
except Exception:
    pyfits = None
    WCS = None
    ASTROPY_AVAILABLE = False

# Page config: guia do navegador (page_title) e layout
st.set_page_config(page_title="FD+ND3", layout="wide")

# ------------------------
# Dados de exemplo (mantidos para desenvolvimento — você troca depois)
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
# Estilo global: centraliza conteúdo, fade-in, corrige botão de sidebar
# ------------------------
st.markdown(
    """
    <style>
    /* Remove todo espaço do topo e do container para colar conteúdo no menu */
    .main .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin: 0 !important;
    }

    /* Mantém botão de abrir/fechar sidebar visível */
    button[aria-label="Toggle sidebar"],
    button[title="Toggle sidebar"],
    button[title="Open sidebar"] {
        z-index: 9999 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------
# Funções utilitárias para leitura e conversão de formatos
# ------------------------
def read_csv_from_bytes(b: bytes):
    try:
        s = b.decode('utf-8', errors='replace')
        df = pd.read_csv(StringIO(s))
    except Exception:
        df = pd.read_csv(BytesIO(b))
    return df

def read_json_from_bytes(b: bytes):
    return json.loads(b.decode('utf-8', errors='replace'))

def try_geopandas_read(file_path):
    """Tentativa segura de ler com geopandas (suporta GeoJSON, KML/KMZ, SHP, etc)."""
    try:
        gdf = gpd.read_file(file_path)
        return gdf
    except Exception:
        try:
            with open(file_path, 'rb') as f:
                obj = json.load(f)
            if 'features' in obj:
                gdf = gpd.GeoDataFrame.from_features(obj['features'])
                return gdf
        except Exception:
            return None

def extract_points_from_gdf(gdf):
    """Retorna DataFrame com colunas lat, lon e as demais propriedades (se possível)."""
    df = pd.DataFrame()
    if gdf is None or gdf.empty:
        return df
    gdf = gdf.copy()
    if gdf.geometry.is_empty.all():
        return df
    # extrai centroid se não for Point
    if all(gdf.geometry.geom_type == 'Point'):
        coords = gdf.geometry.apply(lambda p: (p.y, p.x))
    else:
        coords = gdf.geometry.centroid.apply(lambda p: (p.y, p.x))
    df[['lat', 'lon']] = pd.DataFrame(coords.tolist(), index=gdf.index)
    props = gdf.drop(columns=['geometry'], errors='ignore')
    df = pd.concat([df.reset_index(drop=True), props.reset_index(drop=True)], axis=1)
    return df

def image_to_datauri(img_bytes, mime):
    b64 = base64.b64encode(img_bytes).decode('ascii')
    return f"data:{mime};base64,{b64}"

# ------------------------
# Função principal de criação do mapa (com cluster + heatmap + camadas)
# ------------------------
def make_folium_map(df_points,
                    polygons_gdf=None,
                    enable_points=True,
                    enable_polygons=True,
                    enable_heatmap=True,
                    show_cluster=True,
                    image_overlays=None):
    if (df_points is None) or df_points.empty:
        center = [0, 0]
    else:
        center = [df_points["lat"].mean(), df_points["lon"].mean()]

    m = folium.Map(location=center, zoom_start=3, tiles="CartoDB dark_matter", control_scale=True)

    # Pontos com MarkerCluster
    fg_points = folium.FeatureGroup(name="Pontos", show=enable_points)
    if enable_points and df_points is not None and not df_points.empty:
        if show_cluster:
            cluster = MarkerCluster(name="Cluster de Pontos")
            for _, row in df_points.iterrows():
                lat = row.get("lat")
                lon = row.get("lon")
                if pd.isna(lat) or pd.isna(lon):
                    continue
                popup_html = "<div style='max-height:220px;overflow:auto;'>"
                for c in df_points.columns:
                    if c in ("lat", "lon"):
                        continue
                    val = row.get(c)
                    popup_html += f"<b>{html.escape(str(c))}:</b> {html.escape(str(val))}<br>"
                popup_html += "</div>"
                folium.Marker(location=[lat, lon], popup=folium.Popup(popup_html, max_width=350)).add_to(cluster)
            cluster.add_to(fg_points)
        else:
            for _, row in df_points.iterrows():
                lat = row.get("lat")
                lon = row.get("lon")
                if pd.isna(lat) or pd.isna(lon):
                    continue
                popup_html = "<div style='max-height:220px;overflow:auto;'>"
                for c in df_points.columns:
                    if c in ("lat", "lon"):
                        continue
                    val = row.get(c)
                    popup_html += f"<b>{html.escape(str(c))}:</b> {html.escape(str(val))}<br>"
                popup_html += "</div>"
                folium.CircleMarker(location=[lat, lon],
                                    radius=6,
                                    fill=True,
                                    fill_color="#ff7f0e",
                                    color="#ffffff",
                                    weight=0.6,
                                    fill_opacity=0.9,
                                    popup=folium.Popup(popup_html, max_width=300)).add_to(fg_points)
    m.add_child(fg_points)

    # Polígonos GeoDataFrame
    if polygons_gdf is not None and enable_polygons and not polygons_gdf.empty:
        fg_polys = folium.FeatureGroup(name="Polígonos", show=enable_polygons)
        try:
            gj = polygons_gdf.to_json()
            folium.GeoJson(data=gj, name="Polígonos", popup=folium.GeoJsonPopup(fields=list(polygons_gdf.columns))).add_to(fg_polys)
            m.add_child(fg_polys)
        except Exception:
            folium.GeoJson(data=json.loads(polygons_gdf.to_json())).add_to(fg_polys)
            m.add_child(fg_polys)

    # Heatmap
    if enable_heatmap and df_points is not None and not df_points.empty:
        heat_data = df_points[['lat', 'lon']].dropna().values.tolist()
        if heat_data:
            fg_heat = folium.FeatureGroup(name="Heatmap", show=enable_heatmap)
            HeatMap(heat_data, radius=20, blur=12, max_zoom=6).add_to(fg_heat)
            m.add_child(fg_heat)

    # Image overlays (GeoTIFF, FITS converted to image with bounds)
    if image_overlays:
        for img_info in image_overlays:
            try:
                img = img_info.get('img')
                bounds = img_info.get('bounds')  # [[south, west], [north, east]]
                name = img_info.get('name', 'Imagem')
                buff = BytesIO()
                img.save(buff, format="PNG")
                buff.seek(0)
                img_b = buff.read()
                data_uri = image_to_datauri(img_b, "image/png")
                folium.raster_layers.ImageOverlay(url=data_uri, bounds=bounds, name=f"Imagem: {name}", opacity=0.7, interactive=True, cross_origin=False).add_to(m)
            except Exception:
                continue

    folium.LayerControl(collapsed=False).add_to(m)
    return m

# ------------------------
# Sidebar (tudo aqui: filtros, uploads, observações -> OBS visíveis no final)
# ------------------------
with st.sidebar:
    st.markdown("## 🌍 Dashboard ND3 (Final Prototype)")
    st.markdown("---")
    st.subheader("🔎 Filtros")
    CATEGORIES = ["Todas"] + sorted(base_df["categoria"].unique().tolist())
    REGIONS = ["Todas"] + sorted(base_df["regiao"].unique().tolist())

    cat_sel = st.selectbox("Categoria", CATEGORIES, index=0)
    region_sel = st.selectbox("Região", REGIONS, index=0)
    min_val = st.slider("Valor mínimo", 0, 100, 0)

    st.markdown("---")
    st.subheader("🗂️ Camadas do mapa")
    show_points = st.checkbox("Mostrar Pontos", value=True)
    show_polygons = st.checkbox("Mostrar Polígonos", value=True)
    show_heatmap = st.checkbox("Mostrar Heatmap", value=True)
    use_cluster = st.checkbox("Usar MarkerCluster", value=True)

    st.markdown("---")
    st.subheader("📁 Upload (substitui dados de exemplo)")
    st.markdown("Aceita: csv, json, geojson, kml, kmz, fits, tif, tiff, png, jpg, jpeg")
    uploaded_file = st.file_uploader(
        "Envie um arquivo",
        type=["csv","json","geojson","kml","kmz","fits","fit","tif","tiff","png","jpg","jpeg"],
        accept_multiple_files=False
    )

    st.markdown("---")
    st.subheader("📁 Upload adicional (arquivos múltiplos)")
    uploaded_files = st.file_uploader(
        "Enviar múltiplos (opcionais)",
        type=["csv","geojson","kml","kmz","tif","tiff","png","jpg","jpeg","fits"],
        accept_multiple_files=True
    )

    st.markdown("---")
    st.markdown("### 🔧 Observações técnicas (visíveis)")
    st.markdown("""
    - O dashboard aceita vários formatos e tenta extrair pontos, polígonos e imagens georreferenciadas automaticamente.  
    - GeoTIFF: depende de `rasterio` para extrair bounds/CRS. Se não estiver instalado, o arquivo será rejeitado com aviso.  
    - KML/KMZ: lidos via `geopandas` (fiona/GDAL). Em alguns sistemas, pode ser necessário instalar dependências nativas (conda/apt).  
    - FITS: usamos `astropy` para gerar preview; para georreferenciamento completo (WCS) pode ser necessário adaptar a lógica.  
    - Para grandes volumes de pontos, use cluster/tiling ou simplificação (server-side).  
    - Se quiser exportar GeoPackage ou shapefiles, posso adicionar botão de export rápido.  
    """)

    st.markdown("---")
    # --- Patch Notes (expander pronto para você escrever) ---
    with st.expander("🧩 Patch Notes", expanded=False):
        st.caption("### Versão 3.4.6 (Atual)")
        st.caption("### Versão 3.4.6 (Em Desenvolvimento)")
        st.markdown("""
        - Adição de suporte a múltiplos tipos de dados. (Chegando)
        - Adição de configurações de aparência/acessibilidade. (Chegando)
        - Adição de expanções dos menus. (Chegando)
        - Adição de menus de feedback. (Chegando)
        - Melhoria na performance do mapa. (Chegando)
        - Adição de tradução na interface. (Chegando)
        """)

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

    st.markdown("---")    
    st.caption("© 2025 - Dashboard ND3 Final Prototype")


# ------------------------
# Carregamento e detecção do arquivo enviado
# ------------------------
df_points = base_df.copy()
polygons_gdf = None
image_overlays = []

def handle_uploaded_file(ufile):
    name = ufile.name.lower()
    b = ufile.read()
    # CSV
    if name.endswith(".csv") or name.endswith(".txt"):
        try:
            df = read_csv_from_bytes(b)
            lat_col = None; lon_col = None
            for c in df.columns:
                if c.lower() in ("lat","latitude","y"): lat_col = c
                if c.lower() in ("lon","lng","longitude","x"): lon_col = c
            if lat_col and lon_col:
                df = df.rename(columns={lat_col:"lat", lon_col:"lon"})
                return {"type":"points_df", "data": df}
            else:
                return {"type":"table", "data": df}
        except Exception as e:
            return {"type":"error", "error": f"CSV read error: {e}"}

    # JSON / GeoJSON
    if name.endswith(".json") or name.endswith(".geojson"):
        try:
            obj = read_json_from_bytes(b)
            if "features" in obj:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".geojson") as tmp:
                    tmp.write(json.dumps(obj).encode("utf-8"))
                    tmp.flush()
                    gdf = try_geopandas_read(tmp.name)
                    try:
                        os.unlink(tmp.name)
                    except Exception:
                        pass
                if gdf is not None:
                    if any(gdf.geometry.geom_type=="Point"):
                        pts = extract_points_from_gdf(gdf)
                        return {"type":"points_df", "data": pts, "gdf": gdf}
                    else:
                        return {"type":"polygons_gdf", "data": gdf}
                else:
                    return {"type":"raw_geojson", "data": obj}
            else:
                return {"type":"json", "data": obj}
        except Exception as e:
            return {"type":"error", "error": f"JSON read error: {e}"}

    # KML / KMZ
    if name.endswith(".kml") or name.endswith(".kmz"):
        try:
            suffix = ".kml" if name.endswith(".kml") else ".kmz"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(b); tmp.flush()
                gdf = try_geopandas_read(tmp.name)
            try:
                os.unlink(tmp.name)
            except Exception:
                pass
            if gdf is not None:
                if any(gdf.geometry.geom_type=="Point"):
                    pts = extract_points_from_gdf(gdf)
                    return {"type":"points_df", "data": pts, "gdf": gdf}
                else:
                    return {"type":"polygons_gdf", "data": gdf}
            else:
                return {"type":"error", "error":"KML/KMZ read failed"}
        except Exception as e:
            return {"type":"error", "error": f"KML/KMZ read error: {e}"}

    # FITS
    if name.endswith(".fits") or name.endswith(".fit"):
        if not ASTROPY_AVAILABLE:
            return {"type":"error", "error":"Astropy não disponível. Instale astropy para abrir FITS."}
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".fits") as tmp:
                tmp.write(b); tmp.flush()
                hdul = pyfits.open(tmp.name)
                header = hdul[0].header
                data = hdul[0].data
                try:
                    w = WCS(header)
                    arr = data
                    if arr is None:
                        arr = hdul[1].data if len(hdul)>1 else None
                    if arr is None:
                        hdul.close()
                        try:
                            os.unlink(tmp.name)
                        except Exception:
                            pass
                        return {"type":"fits_meta", "data": dict(header)}
                    arr2 = arr.astype(float)
                    arr2 = np.nan_to_num(arr2)
                    arr2 = arr2 - arr2.min()
                    if arr2.max()>0:
                        arr2 = arr2 / arr2.max() * 255.0
                    img = Image.fromarray(arr2.astype(np.uint8))
                    hdul.close()
                    try:
                        os.unlink(tmp.name)
                    except Exception:
                        pass
                    return {"type":"fits_preview", "data": {"image":img, "header": dict(header)}}
                except Exception:
                    hdul.close()
                    try:
                        os.unlink(tmp.name)
                    except Exception:
                        pass
                    return {"type":"fits_meta", "data": dict(header)}
        except Exception as e:
            return {"type":"error", "error": f"FITS read error: {e}"}

    # TIFF / GeoTIFF
    if name.endswith(".tif") or name.endswith(".tiff"):
        if not RASTERIO_AVAILABLE:
            return {"type":"error", "error":"Rasterio não disponível. Instale rasterio para abrir GeoTIFF."}
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp:
                tmp.write(b); tmp.flush()
                src = rasterio.open(tmp.name)
                bounds = src.bounds
                crs = src.crs
                arr = src.read()
                try:
                    img_arr = reshape_as_image(arr)
                    pil = Image.fromarray(img_arr.astype('uint8'))
                except Exception:
                    band = arr[0]
                    band = np.nan_to_num(band)
                    band = band - band.min()
                    if band.max()>0:
                        band = band / band.max() * 255
                    pil = Image.fromarray(band.astype('uint8')).convert("RGB")
                try:
                    if crs is not None:
                        dst_bounds = transform_bounds(crs, "EPSG:4326", bounds.left, bounds.bottom, bounds.right, bounds.top)
                        south = dst_bounds[1]; west = dst_bounds[0]; north = dst_bounds[3]; east = dst_bounds[2]
                        bnds = [[south, west], [north, east]]
                    else:
                        bnds = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]
                except Exception:
                    bnds = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]
                src.close()
                try:
                    os.unlink(tmp.name)
                except Exception:
                    pass
                return {"type":"geotiff", "data": {"image": pil, "bounds": bnds, "crs": str(crs)}}
        except Exception as e:
            return {"type":"error", "error": f"GeoTIFF read error: {e}"}

    # imagens comuns (png/jpg/jpeg)
    if name.endswith(".png") or name.endswith(".jpg") or name.endswith(".jpeg"):
        try:
            img = Image.open(BytesIO(b)).convert("RGBA")
            return {"type":"image_preview", "data": img}
        except Exception as e:
            return {"type":"error", "error": f"Image read error: {e}"}

    return {"type":"unknown", "data": b}

# tratar arquivo principal
if 'uploaded_file' in locals() and uploaded_file is not None:
    result = handle_uploaded_file(uploaded_file)
    if result.get("type") == "points_df":
        df_points = result["data"]
        polygons_gdf = result.get("gdf", None)
    elif result.get("type") == "polygons_gdf":
        polygons_gdf = result["data"]
        dfp = extract_points_from_gdf(polygons_gdf)
        if not dfp.empty:
            df_points = dfp
    elif result.get("type") == "geotiff":
        info = result["data"]
        image_overlays.append({"img": info["image"], "bounds": info["bounds"], "name": uploaded_file.name})
    elif result.get("type") == "fits_preview":
        info = result["data"]
        image_overlays.append({"img": info["image"].convert("RGBA"), "bounds": [[-85,-180],[85,180]], "name": uploaded_file.name})
    elif result.get("type") == "image_preview":
        img = result["data"]
        image_overlays.append({"img": img, "bounds": [[-85,-180],[85,180]], "name": uploaded_file.name})
    elif result.get("type") == "table":
        df_points = result["data"]
    elif result.get("type") == "raw_geojson":
        try:
            gdf = gpd.GeoDataFrame.from_features(result["data"]["features"])
            polygons_gdf = gdf
            dfp = extract_points_from_gdf(gdf)
            if not dfp.empty:
                df_points = dfp
        except Exception:
            st.sidebar.warning("GeoJSON lido, mas não foi possível converter para GeoDataFrame.")
    elif result.get("type") == "json":
        st.sidebar.info("JSON carregado (não-geo). Verifique a aba de dados.")
    elif result.get("type") == "error":
        st.sidebar.error(result.get("error"))
    else:
        st.sidebar.info(f"Tipo retornado: {result.get('type')}")

# tratar uploads múltiplos (adicionais)
if uploaded_files:
    for f in uploaded_files:
        r = handle_uploaded_file(f)
        if r.get("type") == "points_df":
            df_points = pd.concat([df_points, r["data"]], ignore_index=True, sort=False)
        elif r.get("type") == "polygons_gdf":
            if polygons_gdf is None:
                polygons_gdf = r["data"]
            else:
                polygons_gdf = pd.concat([polygons_gdf, r["data"]])
        elif r.get("type") == "geotiff":
            info = r["data"]
            image_overlays.append({"img": info["image"], "bounds": info["bounds"], "name": f.name})
        elif r.get("type") == "fits_preview":
            info = r["data"]
            image_overlays.append({"img": info["image"].convert("RGBA"), "bounds": [[-85,-180],[85,180]], "name": f.name})
        elif r.get("type") == "image_preview":
            image_overlays.append({"img": r["data"], "bounds": [[-85,-180],[85,180]], "name": f.name})
        else:
            pass

# ------------------------
# Filtragem simples
# ------------------------
def filtered_df_simple(df, cat, min_val, region):
    d = df.copy() if df is not None else pd.DataFrame()
    if d.empty:
        return d
    if cat and cat != "Todas" and "categoria" in d.columns:
        d = d[d["categoria"] == cat]
    if region and region != "Todas" and "regiao" in d.columns:
        d = d[d["regiao"] == region]
    if min_val is not None and "valor" in d.columns:
        d = d[d["valor"] >= min_val]
    return d

df_filtered = filtered_df_simple(df_points, cat_sel, min_val, region_sel)

# ------------------------
# Conteúdo principal (título da página + mapa + estatísticas + tabela)
# ------------------------



# --- Mapa ---
st.markdown("## 🗺️ Mapa Interativo (Filtros aplicados)")
folium_map = make_folium_map(df_points=df_filtered,
                            polygons_gdf=polygons_gdf,
                            enable_points=show_points,
                            enable_polygons=show_polygons,
                            enable_heatmap=show_heatmap,
                            show_cluster=use_cluster,
                            image_overlays=image_overlays if image_overlays else None)
st_data = st_folium(folium_map, width="100%", height=700)
st.markdown("---")

# Estatísticas
st.markdown("## 📊 Estatísticas")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Contagem (linhas)", int(df_filtered.shape[0]) if not df_filtered.empty else 0)
with col2:
    st.metric("Média (valor)", float(df_filtered["valor"].mean()) if not df_filtered.empty and "valor" in df_filtered.columns else "—")
with col3:
    st.metric("Máximo (valor)", int(df_filtered["valor"].max()) if not df_filtered.empty and "valor" in df_filtered.columns else "—")
with col4:
    st.metric("Mínimo (valor)", int(df_filtered["valor"].min()) if not df_filtered.empty and "valor" in df_filtered.columns else "—")

st.markdown("---")

# Tabela + download
st.markdown("## 📋 Tabela de Dados (Filtros aplicados)")
if df_filtered is not None and not df_filtered.empty:
    st.dataframe(df_filtered.reset_index(drop=True), height=360, use_container_width=True)
    csv_bytes = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Baixar CSV dos dados filtrados", data=csv_bytes, file_name="dados_filtrados.csv", mime="text/csv")
else:
    st.info("Nenhum dado com lat/lon disponível para exibir. Se carregou um arquivo não-geográfico, verifique a aba lateral.")

# Previews de imagens carregadas
if image_overlays:
    st.markdown("---")
    st.markdown("## 🖼️ Previews / Imagens carregadas")
    for info in image_overlays:
        st.markdown(f"**{info.get('name','Imagem')}**")
        buf = BytesIO()
        info['img'].save(buf, format="PNG")
        st.image(buf.getvalue(), use_column_width=True)

# ------------------------
# Final: Observações rápidas no rodapé do conteúdo principal (redundância leve)
# ------------------------
st.markdown("---")
st.markdown("### ℹ️ Notas rápidas")
st.markdown("""
- Troque `base_df` pelos outputs reais do NDE3 quando quiser (substitua as entradas de exemplo).  
- Precisa de export para GeoPackage / shapefile / gráficos? Eu adiciono na próxima atualização.  
""")
