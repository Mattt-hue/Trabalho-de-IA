"""Leitura do mapa (arquivo texto) e custos de terreno."""
import config


class Mapa:
    def __init__(self, caminho="mapa.txt"):
        with open(caminho, encoding="utf-8") as f:
            linhas = [l.rstrip("\n") for l in f if l.strip()]
        self.altura = len(linhas)
        self.largura = max(len(l) for l in linhas)
        linhas = [l.ljust(self.largura, ".") for l in linhas]

        marcadores = set(config.DIFICULDADE) | {config.ORIGEM, config.DESTINO}
        self.terreno = []            # letra de terreno de cada célula
        self.pos = {}                # marcador -> (linha, coluna)
        for r, l in enumerate(linhas):
            row = []
            for c, ch in enumerate(l):
                if ch in marcadores:
                    self.pos[ch] = (r, c)
                    row.append(None)         # resolvido depois
                elif ch in config.CUSTO_TERRENO:
                    row.append(ch)
                else:
                    raise ValueError(f"Caractere desconhecido {ch!r} em ({r},{c})")
            self.terreno.append(row)

        faltando = marcadores - set(self.pos)
        if faltando:
            raise ValueError(f"Marcadores ausentes no mapa: {sorted(faltando)}")

        # terreno sob os marcadores
        for m, (r, c) in self.pos.items():
            if m in (config.ORIGEM, config.DESTINO):
                self.terreno[r][c] = "."
            elif config.TERRENO_SOB_GINASIO != "auto":
                self.terreno[r][c] = config.TERRENO_SOB_GINASIO
        for m, (r, c) in self.pos.items():
            if self.terreno[r][c] is None:
                viz = [self.terreno[rr][cc] for rr, cc in self.vizinhos_brutos(r, c)
                       if self.terreno[rr][cc] is not None]
                cont = {}
                for t in viz:
                    cont[t] = cont.get(t, 0) + 1
                melhor = max(cont, key=lambda t: (cont[t], -config.CUSTO_TERRENO[t]))
                self.terreno[r][c] = melhor

        self.custo = [[config.CUSTO_TERRENO[t] for t in row] for row in self.terreno]
        for m in (config.ORIGEM, config.DESTINO):
            r, c = self.pos[m]
            self.custo[r][c] = config.CUSTO_ORIGEM_DESTINO

    def vizinhos_brutos(self, r, c):
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < self.altura and 0 <= cc < self.largura:
                yield rr, cc

    # só movimentos verticais/horizontais (sem diagonal)
    def vizinhos(self, r, c):
        return self.vizinhos_brutos(r, c)

    @property
    def custo_min(self):
        return min(config.CUSTO_TERRENO.values())
