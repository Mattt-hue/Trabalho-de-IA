"""Visualização: imagem final, GIF do agente andando e mapa ASCII no console."""
import config

CORES = {"M": "#8B5A2B", "A": "#4F8FE8", "F": "#4CAF50", "R": "#8D8D8D", ".": "#EDEDED"}


def mapa_ascii(mapa, caminho=None, expandidos=None, fronteira=None, agente=None):
    """Console: '@' agente, '*' caminho final, '+' expandido, '?' fronteira,
    marcadores de ginásio/origem/destino e letras do terreno nas demais células."""
    caminho = set(caminho or [])
    expandidos = set(expandidos or [])
    fronteira = set(fronteira or [])
    pos_marc = {p: m for m, p in mapa.pos.items()}
    linhas = []
    for r in range(mapa.altura):
        s = []
        for c in range(mapa.largura):
            p = (r, c)
            if agente == p:
                s.append("@")
            elif p in pos_marc:
                s.append(pos_marc[p])
            elif p in caminho:
                s.append("*")
            elif p in fronteira:
                s.append("?")
            elif p in expandidos:
                s.append("+")
            else:
                s.append(mapa.terreno[r][c])
        linhas.append("".join(s))
    return "\n".join(linhas)


def _base(mapa, ax, expandidos, fronteira, ordem_nomes, pos):
    import numpy as np
    from matplotlib.colors import to_rgb
    img = np.zeros((mapa.altura, mapa.largura, 3))
    for r in range(mapa.altura):
        for c in range(mapa.largura):
            img[r, c] = to_rgb(CORES[mapa.terreno[r][c]])
    for (r, c) in expandidos:
        img[r, c] = 0.8 * img[r, c] + 0.2 * np.array(to_rgb("#FFD600"))
    for (r, c) in fronteira:
        img[r, c] = 0.6 * img[r, c] + 0.4 * np.array(to_rgb("#FF9800"))
    ax.imshow(img, interpolation="nearest")
    for m, (r, c) in pos.items():
        if m == config.ORIGEM:
            txt, cor = "0", "#00A000"
        elif m == config.DESTINO:
            txt, cor = "U", "#B00020"
        else:
            txt, cor = str(ordem_nomes.get(m, m)), "#222222"
        ax.text(c, r, txt, ha="center", va="center", fontsize=6.5, fontweight="bold",
                color="white", bbox=dict(boxstyle="circle,pad=0.15", fc=cor, ec="white", lw=0.5))
    ax.set_xticks([]); ax.set_yticks([])


def salvar_imagem(mapa, caminho_celulas, expandidos, fronteira, ordem_visita, resumo, arquivo):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ordem_nomes = {m: i + 1 for i, m in enumerate(ordem_visita)}   # número da visita em cada ginásio
    fig, ax = plt.subplots(figsize=(16, 6.4))
    _base(mapa, ax, expandidos, fronteira, ordem_nomes, mapa.pos)
    ys = [p[0] for p in caminho_celulas]; xs = [p[1] for p in caminho_celulas]
    ax.plot(xs, ys, color="#D50000", lw=1.6, alpha=0.9)
    ax.set_title(resumo + "\n(0 = origem, U = destino, números = ordem de visita dos ginásios)", fontsize=10)
    from matplotlib.patches import Patch
    leg = [Patch(color=CORES[k], label=n) for k, n in
           (("M", "Montanha (200)"), ("A", "Água (30)"), ("F", "Floresta (15)"),
            ("R", "Rochoso (5)"), (".", "Livre (1)"))]
    leg += [Patch(color="#FFE600", label="Células expandidas (A*)"),
            Patch(color="#FF9800", label="Fronteira (A*)"),
            Patch(color="#D50000", label="Caminho final")]
    ax.legend(handles=leg, loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=8, fontsize=8)
    fig.tight_layout()
    fig.savefig(arquivo, dpi=130)
    plt.close(fig)


def salvar_gif(mapa, caminho_celulas, passos_custo, eventos, expandidos, fronteira,
               ordem_visita, arquivo, max_frames=160):
    """passos_custo[k] = custo acumulado (rota + batalhas) ao chegar na célula k;
    eventos[k] = texto do ginásio vencido naquela célula (ou '')."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter
    ordem_nomes = {m: i + 1 for i, m in enumerate(ordem_visita)}
    fig, ax = plt.subplots(figsize=(13, 5.4))
    _base(mapa, ax, expandidos, fronteira, ordem_nomes, mapa.pos)
    linha, = ax.plot([], [], color="#D50000", lw=1.6)
    agente, = ax.plot([], [], "o", color="#0D47A1", ms=8, mec="white")
    texto = ax.set_title("")
    n = len(caminho_celulas)
    passo = max(1, n // max_frames)
    quadros = list(range(0, n, passo)) + [n - 1]

    def atualizar(k):
        xs = [p[1] for p in caminho_celulas[:k + 1]]; ys = [p[0] for p in caminho_celulas[:k + 1]]
        linha.set_data(xs, ys)
        agente.set_data([xs[-1]], [ys[-1]])
        ev = next((eventos[j] for j in range(max(0, k - passo + 1), k + 1) if eventos[j]), "")
        texto.set_text(f"passo {k}/{n - 1}   custo acumulado: {passos_custo[k]:.1f} min   {ev}")
        return linha, agente, texto

    anim = FuncAnimation(fig, atualizar, frames=quadros, interval=60, blit=False)
    anim.save(arquivo, writer=PillowWriter(fps=15))
    plt.close(fig)
