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


# =====================================================================
#  Visualização no terminal (animada, com cores ANSI) e quadros em texto
# =====================================================================
import os
import shutil
import sys
import time

# cores de fundo (paleta de 256 cores) por terreno
_BG = {"M": 94, "A": 25, "F": 28, "R": 240, ".": 236}
_NOMES_TERRENO = {"M": "Montanha", "A": "Água", "F": "Floresta", "R": "Rochoso", ".": "Livre"}


def ativar_ansi():
    """Habilita sequências ANSI no console do Windows 10+ (no Linux/Mac não faz nada)."""
    if os.name == "nt":
        os.system("")


def _fronteira(mapa, expandidos):
    """Células vizinhas das expandidas que ainda não foram expandidas (= fronteira do A*)."""
    fr = set()
    for (r, c) in expandidos:
        for q in mapa.vizinhos(r, c):
            if q not in expandidos:
                fr.add(q)
    return fr


def _celula(mapa, p, pos_marc, trilha, agente, visitados, exp_antigo, exp_atual, fronteira, cor):
    r, c = p
    t = mapa.terreno[r][c]
    if p == agente:
        return "@", "1;97;48;5;21"
    if p in pos_marc:
        m = pos_marc[p]
        if m == config.ORIGEM:
            return "1", "1;30;48;5;51"
        if m == config.DESTINO:
            return "U", "1;97;48;5;201"
        if m in visitados:
            return (m, "1;30;48;5;46") if cor else ("#", "")
        return m, "1;30;48;5;255"
    if p in trilha:
        return "*", f"1;91;48;5;{_BG[t]}"
    if p in fronteira:
        return "?", "1;30;48;5;208"
    if p in exp_atual:
        return "+", "30;48;5;220"
    if p in exp_antigo:
        return "+", "38;5;180;48;5;58"
    return (" ", f"48;5;{_BG[t]}") if cor else (t, "")


def desenhar_mapa(mapa, janela, pos_marc, trilha, agente, visitados,
                  exp_antigo, exp_atual, fronteira, cor=True):
    """Devolve as linhas do mapa (recorte `janela` = r0, r1, c0, c1)."""
    r0, r1, c0, c1 = janela
    linhas = []
    for r in range(r0, r1):
        partes, atual, buf = [], None, []
        for c in range(c0, c1):
            ch, est = _celula(mapa, (r, c), pos_marc, trilha, agente, visitados,
                              exp_antigo, exp_atual, fronteira, cor)
            if cor and est != atual:
                if buf:
                    partes.append(f"\033[{atual}m" + "".join(buf))
                atual, buf = est, []
            buf.append(ch)
        if buf:
            partes.append((f"\033[{atual}m" if cor else "") + "".join(buf))
        linhas.append("".join(partes) + ("\033[0m" if cor else ""))
    return linhas


def _janela(mapa, centro, reservadas):
    """Recorte do mapa que cabe no terminal, centrado no agente (mapa inteiro se couber)."""
    cols, lins = shutil.get_terminal_size((160, 60))
    W = min(mapa.largura, max(20, cols - 1))
    H = min(mapa.altura, max(8, lins - reservadas - 1))
    r, c = centro
    r0 = min(max(0, r - H // 2), mapa.altura - H)
    c0 = min(max(0, c - W // 2), mapa.largura - W)
    return r0, r0 + H, c0, c0 + W


def _legenda(cor):
    if not cor:
        return ("Legenda: @ agente | * caminho | ? fronteira | + expandido | # ginásio vencido | "
                "1 origem | U destino | M A F R . = terreno")
    def b(cod, txt):
        return f"\033[{cod}m{txt}\033[0m"
    return ("Legenda: " + b("1;97;48;5;21", "@") + " agente  " + b("1;91;48;5;236", "*") + " caminho  "
            + b("1;30;48;5;208", "?") + " fronteira  " + b("30;48;5;220", "+") + " expandido (perna atual)  "
            + b("38;5;180;48;5;58", "+") + " expandido (pernas anteriores)  "
            + b("1;30;48;5;255", "G") + " ginásio  " + b("1;30;48;5;46", "G") + " vencido  "
            + b("1;30;48;5;51", "1") + " origem  " + b("1;97;48;5;201", "U") + " destino")


def _rodape(sim, idx, pk_nomes, perna, total_pernas, fase, extra, n_exp, n_fro):
    """Linhas de status: custos acumulados e energia dos Pokémon."""
    if idx < 0:
        cr = cb = 0.0
        en = [config.ENERGIA_INICIAL] * len(pk_nomes)
    else:
        cr, cb, en = sim["acum_rota"][idx], sim["acum_bat"][idx], sim["energia_k"][idx]
    energia = "  ".join(f"{n}:{e}" for n, e in zip(pk_nomes, en))
    return [
        f"Perna {perna}/{total_pernas} | {fase} | A*(células): {n_exp} expandidas, {n_fro} na fronteira",
        f"Custo da rota: {cr:7.0f} min | Custo das batalhas: {cb:8.2f} min | CUSTO TOTAL: {cr + cb:9.2f} min",
        f"Energia -> {energia}",
        extra or " ",
    ]


def animar_terminal(mapa, pc, ordem, sim, astar_grade, pk_nomes, velocidade=1.0):
    """Anima no console: A* expandindo (fronteira/visitados), agente andando, custos e batalhas."""
    ativar_ansi()
    pos_marc = {p: m for m, p in mapa.pos.items()}
    caminho, fins = sim["caminho"], sim["fim_perna"]
    n_pernas = len(ordem) - 1
    dt = 0.035 / max(velocidade, 1e-6)
    out = sys.stdout
    trilha, visitados, exp_antigo = set(), set(), set()

    def quadro(agente, exp_atual, fronteira, idx_custo, perna, fase, extra=""):
        rod = _rodape(sim, idx_custo, pk_nomes, perna, n_pernas, fase, extra,
                      f"{len(exp_atual):,}", f"{len(fronteira):,}")
        cab = ["INF1771 - Trabalho 1 | Busca heurística A* - Pokémon/Kanto", _legenda(True)]
        jan = _janela(mapa, agente, len(cab) + len(rod))
        mp = desenhar_mapa(mapa, jan, pos_marc, trilha, agente, visitados,
                           exp_antigo, exp_atual, fronteira, True)
        txt = "\033[H" + "".join(l + "\033[K\n" for l in cab + mp + rod) + "\033[J"
        out.write(txt)
        out.flush()

    out.write("\033[2J\033[?25l")
    try:
        ini = 0
        for k, (a, b) in enumerate(zip(ordem, ordem[1:])):
            origem_c, destino_c = pc.coords[a], pc.coords[b]
            nome_b = pc.nomes[b]
            _, _, expandidos, _ = astar_grade(mapa, origem_c, destino_c)
            idx_pre = ini - 1
            titulo = f"A* {pc.nomes[a]} -> {nome_b}"
            # 1) A* na grade: expansão progressiva (fronteira x visitados)
            n = len(expandidos)
            passos = min(16, max(2, n // 25))
            for j in range(1, passos + 1):
                ex = set(expandidos[: max(1, n * j // passos)])
                quadro(origem_c, ex, _fronteira(mapa, ex), idx_pre, k + 1,
                       f"{titulo}: expandindo", "A* procurando o menor caminho entre os dois pontos...")
                time.sleep(dt * 2)
            ex_final = set(expandidos)
            fr_final = _fronteira(mapa, ex_final)
            # 2) agente percorre o caminho encontrado
            idxs = list(range(ini, fins[k] + 1))
            passo = max(1, len(idxs) // 45)
            for i in idxs[::passo] + ([idxs[-1]] if (len(idxs) - 1) % passo else []):
                for j in range(ini, i + 1):
                    trilha.add(caminho[j])
                quadro(caminho[i], ex_final, fr_final, idx_pre, k + 1, f"{titulo}: caminhando")
                # custo da rota acumulado enquanto anda (batalhas só após vencer o ginásio)
                time.sleep(dt)
            trilha.update(caminho[ini: fins[k] + 1])
            exp_antigo |= ex_final
            # 3) batalha (se o destino da perna é um ginásio)
            evento = sim["eventos"][fins[k]]
            if evento:
                visitados.add(nome_b)
                quadro(caminho[fins[k]], set(), set(), fins[k], k + 1, f"{titulo}: BATALHA",
                       "** " + evento + " **")
                time.sleep(0.9 / max(velocidade, 1e-6))
            ini = fins[k] + 1
        quadro(caminho[-1], set(), set(), len(caminho) - 1, n_pernas, "CHEGOU AO DESTINO (U)",
               "Fim da jornada: rota concluída e todos os ginásios vencidos.")
    finally:
        out.write("\033[0m\033[?25h\n")
        out.flush()


def quadros_texto(mapa, pc, ordem, sim, astar_grade, pk_nomes, arquivo):
    """Grava em `arquivo` (UTF-8) um quadro em texto puro por perna: mapa completo com a
    fronteira/expandidos do A*, o caminho já percorrido, custos e energia. Bom para o relatório."""
    pos_marc = {p: m for m, p in mapa.pos.items()}
    caminho, fins = sim["caminho"], sim["fim_perna"]
    n_pernas = len(ordem) - 1
    trilha, visitados = set(), set()
    jan = (0, mapa.altura, 0, mapa.largura)
    with open(arquivo, "w", encoding="utf-8") as f:
        f.write("INF1771 - Trabalho 1 - passo a passo do agente\n" + _legenda(False) + "\n\n")
        ini = 0
        for k, (a, b) in enumerate(zip(ordem, ordem[1:])):
            nome_b = pc.nomes[b]
            _, _, expandidos, _ = astar_grade(mapa, pc.coords[a], pc.coords[b])
            ex = set(expandidos)
            fr = _fronteira(mapa, ex)
            trilha.update(caminho[ini: fins[k] + 1])
            evento = sim["eventos"][fins[k]]
            if evento:
                visitados.add(nome_b)
            mp = desenhar_mapa(mapa, jan, pos_marc, trilha, caminho[fins[k]], visitados,
                               set(), ex, fr, cor=False)
            rod = _rodape(sim, fins[k], pk_nomes, k + 1, n_pernas,
                          f"A* {pc.nomes[a]} -> {nome_b} concluída", evento, f"{len(ex):,}", f"{len(fr):,}")
            f.write("=" * mapa.largura + "\n" + "\n".join(mp) + "\n" + "\n".join(rod) + "\n\n")
            ini = fins[k] + 1
