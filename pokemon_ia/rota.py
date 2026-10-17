
#Tarefa 2 - Rota: A* sobre a grade (pernas entre pontos de interesse) e
#A* sobre o espaço (ginásio atual, conjunto de ginásios visitados).

import heapq
import time
import numpy as np
from itertools import count

import config


# GRADE
def dijkstra_grade(mapa, origem):
    #Custos mínimos da célula `origem` para todas as outras (A* com h=0).
    #Custo de uma perna = soma do custo de ENTRAR em cada célula (sem a origem).
    H, W = mapa.altura, mapa.largura
    INF = float("inf")
    dist = [[INF] * W for _ in range(H)]
    pai = [[None] * W for _ in range(H)]
    r0, c0 = origem
    dist[r0][c0] = 0
    pq = [(0, r0, c0)]
    while pq:
        d, r, c = heapq.heappop(pq)
        if d > dist[r][c]:
            continue
        for rr, cc in mapa.vizinhos(r, c):
            nd = d + mapa.custo[rr][cc]
            if nd < dist[rr][cc]:
                dist[rr][cc] = nd
                pai[rr][cc] = (r, c)
                heapq.heappush(pq, (nd, rr, cc))
    return dist, pai


def astar_grade(mapa, origem, destino):
   #A* célula a célula, h = distância de Manhattan * menor custo de terreno
    #(admissível e consistente). Devolve caminho, custo, células expandidas e fronteira.
    hmin = mapa.custo_min

    def h(p):
        return (abs(p[0] - destino[0]) + abs(p[1] - destino[1])) * hmin

    g = {origem: 0}
    pai = {origem: None}
    tie = count()
    pq = [(h(origem), next(tie), origem)]
    fechado = set()
    expandidos = []
    while pq:
        f, _, p = heapq.heappop(pq)
        if p in fechado:
            continue
        fechado.add(p)
        expandidos.append(p)
        if p == destino:
            break
        for q in mapa.vizinhos(*p):
            ng = g[p] + mapa.custo[q[0]][q[1]]
            if ng < g.get(q, float("inf")):
                g[q] = ng
                pai[q] = p
                heapq.heappush(pq, (ng + h(q), next(tie), q))
    caminho = []
    p = destino
    while p is not None:
        caminho.append(p)
        p = pai[p]
    caminho.reverse()
    fronteira = [p for _, _, p in pq if p not in fechado]
    return caminho, g[destino], expandidos, set(fronteira)


# PONTOS-CHAVE
class PontosChave:
    # Origem + 24 ginásios + destino e a matriz de custos mínimos entre eles.

    def __init__(self, mapa):
        self.mapa = mapa
        self.ids = list(config.DIFICULDADE)                 # ordem 1º..24º Gym
        self.nomes = [config.ORIGEM] + self.ids + [config.DESTINO]
        self.coords = [mapa.pos[n] for n in self.nomes]
        n = len(self.nomes)
        self.D = [[0] * n for _ in range(n)]
        self._pais = []
        for i, (r, c) in enumerate(self.coords):
            dist, pai = dijkstra_grade(mapa, (r, c))
            self._pais.append(pai)
            for j, (rj, cj) in enumerate(self.coords):
                self.D[i][j] = dist[rj][cj]
        # peso simétrico (limite inferior) usado na heurística MST
        self.W = [[min(self.D[i][j], self.D[j][i]) for j in range(n)] for i in range(n)]

    def caminho(self, i, j):
        #Caminho célula a célula (inclui as duas pontas) de i até j.
        pai = self._pais[i]
        p = self.coords[j]
        out = []
        while p is not None:
            out.append(p)
            p = pai[p[0]][p[1]]
        out.reverse()
        return out


# A* NOS GINASIOS
def _mst(W, nos):
    #Custo da árvore geradora mínima (Prim) dos índices `nos` com pesos W.
    k = len(nos)
    if k <= 1:
        return 0
    INF = float("inf")
    dist = [W[nos[0]][v] for v in nos]
    usado = [False] * k
    usado[0] = True
    total = 0
    for _ in range(k - 1):
        m, mi = INF, -1
        for i in range(k):
            if not usado[i] and dist[i] < m:
                m, mi = dist[i], i
        usado[mi] = True
        total += m
        wr = W[nos[mi]]
        for i in range(k):
            if not usado[i]:
                w = wr[nos[i]]
                if w < dist[i]:
                    dist[i] = w
    return total


def astar_ginasios(pc, peso=1.0, limite_estados=None, tempo_max=None, log=None, cb=None, cb_cada=1):
    """
    Estado   : (atual, mascara)  -> `atual` = índice do ponto onde o agente está
               (0 = origem, 1..24 = ginásios, 25 = destino); `mascara` = bits dos
               ginásios já visitados (distingue conjuntos visitados diferentes).
    Ações    : ir (pelo caminho de menor custo na grade) até um ginásio ainda não
               visitado; com os 24 visitados, ir ao destino U.
    Custo g  : custo da origem (1) + soma dos custos de terreno das pernas.
    Heurística h(atual, mascara) = (menor aresta de `atual` a um ginásio livre)
               + MST(ginásios livres) + (menor aresta de um ginásio livre ao destino).
               Admissível: o caminho restante é um caminho hamiltoniano nos livres,
               ligado a `atual` e a U por uma aresta cada; um caminho hamiltoniano
               custa >= MST. Consistente (prova: MST(L) <= MST(L-g) + aresta mínima de g).
    Com peso=1 o A* devolve rota ÓTIMA.
    """
    D, W = pc.D, pc.W
    NG = len(pc.ids)
    CHEIA = (1 << NG) - 1
    DEST = NG + 1
    tie = count()

    cache_mst = {}      # mascara -> (MST dos não visitados, menor aresta até o destino)

    def h(atual, mask):
        if mask == CHEIA:
            return D[atual][DEST]
        livres = [i + 1 for i in range(NG) if not (mask >> i) & 1]
        if mask not in cache_mst:
            cache_mst[mask] = (_mst(W, livres), min(W[u][DEST] for u in livres))
        mst, ult = cache_mst[mask]
        Wa = W[atual]
        return min(Wa[u] for u in livres) + mst + ult

    inicio = (0, 0)
    g0 = config.CUSTO_ORIGEM_DESTINO
    gbest = {inicio: g0}
    pai = {inicio: None}
    pq = [(peso * h(0, 0) + g0, 0, next(tie), g0, inicio)]
    fechado = set()
    expandidos = 0
    gerados = 1
    t0 = time.time()
    ordem_expansao = []     # (atual, mascara) em ordem, para visualização
    while pq:
        f, _, _, g, est = heapq.heappop(pq)
        if est in fechado or g > gbest[est]:
            continue
        atual, mask = est
        if atual == DEST:                          # estado-objetivo
            caminho = []
            e = est
            while e is not None:
                caminho.append(e[0])
                e = pai[e]
            caminho.reverse()
            # custo recalculado pela própria rota (robusto a reaberturas com peso > 1)
            g = g0 + sum(D[a][b] for a, b in zip(caminho, caminho[1:]))
            return dict(ordem=caminho, custo=g, expandidos=expandidos, gerados=gerados,
                        tempo=time.time() - t0, otimo=(peso == 1.0),
                        ordem_expansao=ordem_expansao)
        fechado.add(est)
        expandidos += 1
        if len(ordem_expansao) < 200000:
            ordem_expansao.append(est)
        if cb and expandidos % cb_cada == 0:          # progresso ao vivo (visualização)
            cam, e = [], est
            while e is not None:
                cam.append(e[0])
                e = pai[e]
            cam.reverse()
            cb(dict(expandidos=expandidos, abertos=len(pq), f=f, g=g, rota=cam,
                    prof=bin(mask).count("1")))
        if log and expandidos % 200000 == 0:
            log(f"   ... {expandidos:,} expandidos, {len(pq):,} na fronteira, f={f:.1f}")
        if limite_estados and expandidos > limite_estados:
            return None
        if tempo_max and (expandidos & 1023) == 0 and time.time() - t0 > tempo_max:
            return None
        if mask == CHEIA:
            sucs = [(DEST, mask)]
        else:
            sucs = [(i + 1, mask | (1 << i)) for i in range(NG) if not (mask >> i) & 1]
        for s in sucs:
            ng = g + D[atual][s[0]]
            if ng < gbest.get(s, float("inf")):
                fechado.discard(s)          # reabre: com peso > 1 h pode ser inconsistente
                gbest[s] = ng
                pai[s] = est
                gerados += 1
                popc = bin(s[1]).count("1")
                heapq.heappush(pq, (ng + peso * h(*s), -popc, next(tie), ng, s))
    return None


# CERTIFICADO DE OTIMALIDADE
def held_karp(pc, log=None, cb=None):
    # Programação dinâmica exata (Held-Karp) sobre (último ginásio, conjunto visitado).
    # Usa numpy e ~0,8 GB de RAM (tabela 2^24 x 24 em int16). Serve para CERTIFICAR
    # o ótimo global da rota: o A* com heurística admissível ponderada (peso>1) é rápido
    # mas não garante otimalidade; o A* exato (peso=1) em Python é impraticável para 24 ginásios.
    # Devolve (custo_otimo, ordem) com ordem = índices de pontos [0, g..., 25].
    
    
    NG = len(pc.ids)
    DEST = NG + 1
    D = np.array(pc.D, dtype=np.int32)
    FULL = 1 << NG
    INF = 30000
    dp = np.full((FULL, NG), INF, dtype=np.int16)
    for j in range(NG):
        dp[1 << j, j] = D[0, j + 1] + config.CUSTO_ORIGEM_DESTINO
    # popcount de todas as máscaras
    pop = np.zeros(FULL, dtype=np.uint8)
    for b in range(NG):
        pop[1 << b:1 << (b + 1)] = pop[:1 << b] + 1
    Dg = D[1:NG + 1, 1:NG + 1].astype(np.int32)       # custo gym i -> gym j
    for k in range(2, NG + 1):
        camada = np.nonzero(pop == k)[0].astype(np.int64)
        for j in range(NG):
            ms = camada[(camada >> j) & 1 == 1]
            prev = ms ^ (1 << j)
            blocos = max(1, len(ms) // 400000 + 1)
            for blk in np.array_split(np.arange(len(ms)), blocos):
                if len(blk) == 0:
                    continue
                v = dp[prev[blk]].astype(np.int32) + Dg[:, j][None, :]
                dp[ms[blk], j] = np.minimum(v.min(axis=1), INF).astype(np.int16)
        if log:
            log(f"   Held-Karp: camada {k}/{NG}")
        if cb:
            cb(k, NG, len(camada))
    ultimo = dp[FULL - 1].astype(np.int32) + D[1:NG + 1, DEST]
    j = int(ultimo.argmin())
    custo = int(ultimo[j])
    # reconstrução
    ordem = [DEST, j + 1]
    mask = FULL - 1
    while True:
        prev = mask ^ (1 << j)
        if prev == 0:
            break
        v = dp[prev].astype(np.int32) + Dg[:, j]
        v[[i for i in range(NG) if not (prev >> i) & 1]] = INF * 2
        i = int(v.argmin())
        ordem.append(i + 1)
        mask, j = prev, i
    ordem.append(0)
    ordem.reverse()
    return custo, ordem
