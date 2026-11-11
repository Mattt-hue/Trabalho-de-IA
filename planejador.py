"""
Planejamento de rotas (A*) do agente Pitfall.

O Prolog (agente.pl) infere quais casas sao seguras e escolhe os objetivos.
Este modulo so planeja sobre essa informacao: nunca ve o mapa real.
"""
import heapq

DIRS = ['norte', 'leste', 'sul', 'oeste']          # sentido horario
DELTA = {'norte': (0, 1), 'leste': (1, 0), 'sul': (0, -1), 'oeste': (-1, 0)}
TAMANHO = 12


def planejar(pos, direcao, seguras, alvos):
    """
    A* sobre estados (x, y, direcao). Cada acao (andar / virar) custa 1.
    Anda apenas por casas em `seguras`; as casas em `alvos` tambem podem ser
    pisadas (o objetivo pode ser uma casa arriscada).
    Heuristica: menor distancia de Manhattan ate algum alvo (admissivel).
    Retorna a lista de acoes ate o alvo mais proximo, ou None se nao ha rota.
    """
    livres = {tuple(c) for c in seguras}
    alvos = {tuple(a) for a in alvos}
    if not alvos:
        return None

    def h(x, y):
        return min(abs(x - ax) + abs(y - ay) for ax, ay in alvos)

    inicio = (pos[0], pos[1], direcao)
    contador = 0
    fila = [(h(pos[0], pos[1]), 0, contador, inicio)]
    custo = {inicio: 0}
    pai = {}                                        # estado -> (estado anterior, acao)

    while fila:
        _, g, _, est = heapq.heappop(fila)
        if g > custo[est]:
            continue
        x, y, d = est
        if (x, y) in alvos:
            return _reconstroi(pai, est)
        i = DIRS.index(d)
        vizinhos = [
            ((x, y, DIRS[(i + 1) % 4]), 'virar_direita'),
            ((x, y, DIRS[(i - 1) % 4]), 'virar_esquerda'),
        ]
        nx, ny = x + DELTA[d][0], y + DELTA[d][1]
        if 1 <= nx <= TAMANHO and 1 <= ny <= TAMANHO \
                and ((nx, ny) in livres or (nx, ny) in alvos):
            vizinhos.append(((nx, ny, d), 'andar'))
        for novo, acao in vizinhos:
            ng = g + 1
            if ng < custo.get(novo, float('inf')):
                custo[novo] = ng
                pai[novo] = (est, acao)
                contador += 1
                heapq.heappush(fila, (ng + h(novo[0], novo[1]), ng, contador, novo))
    return None


def _reconstroi(pai, est):
    acoes = []
    while est in pai:
        est, acao = pai[est]
        acoes.append(acao)
    acoes.reverse()
    return acoes


def decidir(prolog):
    """
    Um passo do ciclo percepcao-decisao-acao. Retorna o nome da acao.
    1) o Prolog atualiza o conhecimento e diz o que quer (alvo/3);
    2) o Python planeja a rota e devolve a primeira acao dela.
    """
    list(prolog.query("atualiza_conhecimento"))
    x, y, d = [(s['X'], s['Y'], str(s['D'])) for s in prolog.query("posicao(X,Y,D)")][0]
    seguras = list(prolog.query("seguras(L)"))[0]['L']

    for prioridade in range(1, 9):
        sols = list(prolog.query("alvo(%d,T,D)" % prioridade))
        if not sols:
            continue
        tipo, dados = str(sols[0]['T']), sols[0]['D']
        if tipo == 'acao':
            return str(dados)
        if tipo == 'ir_risco':               # grupos [risco, casas], menor risco primeiro
            grupos = [casas for _, casas in dados]
        else:
            grupos = [dados]
        plano = None
        for alvos in grupos:
            plano = planejar((x, y), d, seguras, alvos)
            if plano:
                break
        if plano:
            acao = plano[0]
            if acao == 'andar':
                dx, dy = DELTA[d]
                list(prolog.query("registra_intencao(%d,%d)" % (x + dx, y + dy)))
            return acao
    return 'parar'