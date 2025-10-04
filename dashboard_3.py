import matplotlib.pyplot as plt

# Criar esboço da dashboard estilo wireframe
fig, ax = plt.subplots(figsize=(8, 6))

# Header
ax.add_patch(plt.Rectangle((0, 5.5), 8, 0.5, fill=None, edgecolor="black"))
ax.text(4, 5.75, "Header: Título + Filtros", ha="center", va="center")

# Sidebar
ax.add_patch(plt.Rectangle((0, 0), 1.5, 5.5, fill=None, edgecolor="black"))
ax.text(0.75, 5.2, "Sidebar\n(botões)", ha="center", va="top")

# Área principal (dividida em blocos que podem ser "poluídos")
ax.add_patch(plt.Rectangle((1.5, 3.5), 6.5, 2, fill=None, edgecolor="black"))
ax.text(4.75, 4.5, "Bloco 1: Gráfico/Mapa", ha="center", va="center")

ax.add_patch(plt.Rectangle((1.5, 1.5), 6.5, 2, fill=None, edgecolor="black"))
ax.text(4.75, 2.5, "Bloco 2: Estatísticas", ha="center", va="center")

ax.add_patch(plt.Rectangle((1.5, 0), 6.5, 1.5, fill=None, edgecolor="black"))
ax.text(4.75, 0.75, "Footer: Créditos/Explicação", ha="center", va="center")

# Estilo geral
ax.set_xlim(0, 8)
ax.set_ylim(0, 6)
ax.axis("off")
plt.show()