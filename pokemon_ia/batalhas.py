"""
Tarefa 1 - Seleção dos Pokémon em cada ginásio (busca local).

Representação : lista de 24 inteiros; solucao[i] é uma máscara de bits (1..31) com os
                Pokémon que lutam no i-ésimo ginásio (bit p = Pokémon p). Nunca é 0
                (todo ginásio exige pelo menos um Pokémon).
Custo         : sum_i Dificuldade_i / sum(poder dos Pokémon da máscara)  (minutos)
                + PENALIDADE * (violações de energia)
Restrições    : cada Pokémon luta no máximo 6 vezes (energia 6, -1 por batalha) e pelo
                menos um deve terminar com energia >= 1 (usado no máximo 5 vezes).
Vizinhança    : (a) alternar um Pokémon em um ginásio (liga/desliga um bit);
                (b) substituir um Pokémon por outro no mesmo ginásio;
                (c) transferir um Pokémon de um ginásio para outro;
                (d) trocar as equipes de dois ginásios (mantém o uso de energia).
Algoritmos    : Hill Climbing (subida de encosta, ascensão máxima + reinícios aleatórios),
                Simulated Annealing e Algoritmo Genético; mais a programação dinâmica
                exata que serve de referência (ótimo global provado).
"""
import math
import random

import config
import numpy as np

NOMES = list(config.PODER)
PODERES = [config.PODER[n] for n in NOMES]
NP = len(NOMES)
ENERGIA = config.ENERGIA_INICIAL
MAX_USOS_TODOS = ENERGIA                                   # 6 batalhas no máximo
MAX_USOS_SOBREVIVENTE = ENERGIA - config.ENERGIA_MIN_FINAL  # 5 (energia final >= 1)
DIFS = [config.DIFICULDADE[k] for k in config.DIFICULDADE]  # na ordem dos ginásios
NG = len(DIFS)
PENALIDADE = 100.0   # > maior ganho possível de um uso extra de Pokémon (~58 min)

PODER_MASK = [sum(PODERES[p] for p in range(NP) if m >> p & 1) for m in range(1 << NP)]
BITS = [[p for p in range(NP) if m >> p & 1] for m in range(1 << NP)]


# AVALIACAO
def usos(sol):
    u = [0] * NP
    for m in sol:
        for p in BITS[m]:
            u[p] += 1
    return u


def penalidade_usos(u):
    exc = sum(max(0, x - MAX_USOS_TODOS) for x in u)
    exc += max(0, min(u) - MAX_USOS_SOBREVIVENTE)      # nenhum chegou com energia >= 1
    return PENALIDADE * exc


def custo_batalhas(sol):
    return sum(d / PODER_MASK[m] for d, m in zip(DIFS, sol))


def custo(sol):
    return custo_batalhas(sol) + penalidade_usos(usos(sol))


def viavel(sol):
    return penalidade_usos(usos(sol)) == 0


def energia_final(sol):
    return [ENERGIA - config.PERDA_POR_BATALHA * x for x in usos(sol)]


# movimentos de vizinhança
class Estado:
    #Solução + contadores incrementais para avaliar vizinhos em O(1).

    def __init__(self, sol):
        self.sol = list(sol)
        self.u = usos(sol)
        self.cb = custo_batalhas(sol)
        self.pen = penalidade_usos(self.u)

    @property
    def total(self):
        return self.cb + self.pen

    def avaliar(self, mudancas):
        #mudancas = [(i, nova_mascara), ...] -> (novo_total, novos_usos, novo_cb)
        u = list(self.u)
        cb = self.cb
        for i, nm in mudancas:
            om = self.sol[i]
            cb += DIFS[i] / PODER_MASK[nm] - DIFS[i] / PODER_MASK[om]
            for p in BITS[om]:
                u[p] -= 1
            for p in BITS[nm]:
                u[p] += 1
        return cb + penalidade_usos(u), u, cb

    def aplicar(self, mudancas, avaliacao):
        total, u, cb = avaliacao
        for i, nm in mudancas:
            self.sol[i] = nm
        self.u, self.cb, self.pen = u, cb, total - cb


def mov_aleatorio(est, rng):
    #Um movimento aleatório válido (lista de mudanças) ou None.
    x = rng.random()
    if x < 0.45:
        i, p = rng.randrange(NG), rng.randrange(NP)
        nm = est.sol[i] ^ (1 << p)
        return [(i, nm)] if nm else None
    if x < 0.60:                                  # substituir p por q no mesmo ginásio
        i, p, q = rng.randrange(NG), rng.randrange(NP), rng.randrange(NP)
        m = est.sol[i]
        if p == q or not (m >> p & 1) or (m >> q & 1):
            return None
        return [(i, m ^ (1 << p) ^ (1 << q))]
    i, j = rng.randrange(NG), rng.randrange(NG)
    if i == j:
        return None
    if x < 0.80:                                  # trocar as máscaras de dois ginásios
        if est.sol[i] == est.sol[j]:
            return None
        return [(i, est.sol[j]), (j, est.sol[i])]
    ps = BITS[est.sol[i]]
    p = rng.choice(ps)
    if est.sol[j] >> p & 1:
        return None
    ni = est.sol[i] ^ (1 << p)
    if ni == 0:
        return None
    return [(i, ni), (j, est.sol[j] | (1 << p))]


def todos_movimentos(est):
    for i in range(NG):
        for p in range(NP):
            nm = est.sol[i] ^ (1 << p)
            if nm:
                yield [(i, nm)]
        m = est.sol[i]
        for p in BITS[m]:
            for q in range(NP):
                if not m >> q & 1:
                    yield [(i, m ^ (1 << p) ^ (1 << q))]
    for i in range(NG):                               # trocar máscaras de dois ginásios
        for j in range(i + 1, NG):
            if est.sol[i] != est.sol[j]:
                yield [(i, est.sol[j]), (j, est.sol[i])]
    for i in range(NG):
        mi = est.sol[i]
        if len(BITS[mi]) < 2:
            continue
        for p in BITS[mi]:
            for j in range(NG):
                if j != i and not est.sol[j] >> p & 1:
                    yield [(i, mi ^ (1 << p)), (j, est.sol[j] | (1 << p))]


def solucao_aleatoria(rng):
    return [rng.randint(1, (1 << NP) - 1) for _ in range(NG)]


# HILL CLIMBING
def hill_climbing(rng, reinicios=20, sol_inicial=None, cb=None):
    #Subida de encosta de ascensão máxima com reinícios aleatórios.
    #cb (opcional) recebe um texto de progresso; não altera o resultado.
    melhor = None
    for r in range(reinicios):
        est = Estado(sol_inicial if (sol_inicial and r == 0) else solucao_aleatoria(rng))
        passo = 0
        while True:
            melhor_mov, melhor_av = None, None
            for mv in todos_movimentos(est):
                av = est.avaliar(mv)
                if av[0] < est.total - 1e-9 and (melhor_av is None or av[0] < melhor_av[0]):
                    melhor_mov, melhor_av = mv, av
            if melhor_mov is None:
                break
            est.aplicar(melhor_mov, melhor_av)
            passo += 1
            if cb:
                mb = min(est.total, melhor.total) if melhor else est.total
                cb(f"HC | reinício {r + 1:>2}/{reinicios} | passo {passo:>3} | "
                   f"custo atual {est.total:9.3f} | melhor {mb:9.3f}")
        if melhor is None or est.total < melhor.total:
            melhor = est
    return melhor.sol, melhor.total


# SIMULATED ANNEALING
def simulated_annealing(rng, iteracoes=400000, t0=20.0, tf=0.005, sol_inicial=None, cb=None):
    est = Estado(sol_inicial or solucao_aleatoria(rng))
    melhor, melhor_c = list(est.sol), est.total
    alfa = (tf / t0) ** (1.0 / iteracoes)
    T = t0
    for it in range(iteracoes):
        if cb and it % 4000 == 0:
            cb(f"SA | iteração {it:>6}/{iteracoes} | T {T:8.4f} | "
               f"custo atual {est.total:9.3f} | melhor {melhor_c:9.3f}")
        mv = mov_aleatorio(est, rng)
        if mv is not None:
            av = est.avaliar(mv)
            delta = av[0] - est.total
            if delta <= 0 or rng.random() < math.exp(-delta / T):
                est.aplicar(mv, av)
                if est.total < melhor_c - 1e-12:
                    melhor, melhor_c = list(est.sol), est.total
        T *= alfa
    return melhor, melhor_c


# ALGORITMO GENETICO
def algoritmo_genetico(rng, populacao=80, geracoes=400, p_cruz=0.9, p_mut=0.03, elite=2, cb=None):
    pop = [solucao_aleatoria(rng) for _ in range(populacao)]
    fit = [custo(s) for s in pop]

    def torneio(k=3):
        c = rng.sample(range(populacao), k)
        return pop[min(c, key=lambda i: fit[i])]

    for g in range(geracoes):
        if cb and g % 4 == 0:
            cb(f"GA | geração {g:>3}/{geracoes} | melhor {min(fit):9.3f} | "
               f"média da população {sum(fit) / len(fit):9.3f}")
        ordem = sorted(range(populacao), key=lambda i: fit[i])
        nova = [list(pop[i]) for i in ordem[:elite]]
        while len(nova) < populacao:
            a, b = torneio(), torneio()
            if rng.random() < p_cruz:                       # cruzamento uniforme
                filho = [x if rng.random() < 0.5 else y for x, y in zip(a, b)]
            else:
                filho = list(a)
            for i in range(NG):                              # mutação: alterna um bit
                if rng.random() < p_mut:
                    nm = filho[i] ^ (1 << rng.randrange(NP))
                    if nm:
                        filho[i] = nm
            nova.append(filho)
        pop = nova
        fit = [custo(s) for s in pop]
    i = min(range(populacao), key=lambda i: fit[i])
    return pop[i], fit[i]


ALGORITMOS = {"hc": hill_climbing, "sa": simulated_annealing, "ga": algoritmo_genetico}


# REFERENCIA: OTIMO EXATO (DP)
def otimo_exato():
    #Programação dinâmica sobre (ginásio, vetor de usos dos 5 Pokémon). 7^5 estados.
    #Dá o ótimo GLOBAL do problema de batalhas (usado para avaliar a busca local).
    
    base = MAX_USOS_TODOS + 1
    NS = base ** NP
    idx = np.arange(NS)
    U = [(idx // base ** p) % base for p in range(NP)]
    inc = [sum(base ** p for p in BITS[m]) for m in range(1 << NP)]
    ok = [np.all([U[p] < MAX_USOS_TODOS for p in BITS[m]], axis=0) if m else None
          for m in range(1 << NP)]
    dp = np.full(NS, np.inf)
    dp[0] = 0.0
    pais, escolhas = [], []
    for g in range(NG):
        novo = np.full(NS, np.inf)
        pai = np.zeros(NS, dtype=np.int32)
        esc = np.zeros(NS, dtype=np.int8)
        for m in range(1, 1 << NP):
            src = np.nonzero(ok[m] & np.isfinite(dp))[0]
            dst = src + inc[m]
            cand = dp[src] + DIFS[g] / PODER_MASK[m]
            melhor = cand < novo[dst]
            novo[dst[melhor]] = cand[melhor]
            pai[dst[melhor]] = src[melhor]
            esc[dst[melhor]] = m
        dp = novo
        pais.append(pai)
        escolhas.append(esc)
    sobrevive = np.zeros(NS, dtype=bool)
    for p in range(NP):
        sobrevive |= U[p] <= MAX_USOS_SOBREVIVENTE
    final = np.where(sobrevive, dp, np.inf)
    s = int(final.argmin())
    custo_opt = float(final[s])
    sol = [0] * NG
    for g in range(NG - 1, -1, -1):
        sol[g] = int(escolhas[g][s])
        s = int(pais[g][s])
    return sol, custo_opt


def descrever(sol):
    return [[NOMES[p] for p in BITS[m]] for m in sol]
