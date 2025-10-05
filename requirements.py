import subprocess
import sys

# Lista de pacotes necessários
packages = [
    "streamlit",
    "pandas",
    "numpy",
    "matplotlib",
    "plotly",
    "geopandas",
    "Pillow",
    "astropy",
    "fastkml"
]

# Função para instalar pacotes via pip
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Instala todos os pacotes
for pkg in packages:
    try:
        install(pkg)
        print(f"✅ Pacote instalado: {pkg}")
    except Exception as e:
        print(f"❌ Falha ao instalar {pkg}: {e}")
