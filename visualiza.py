"""
Visualizacao em texto do agente jogando (para usar junto do teste1.py).

Mostra dois paineis lado a lado:
  - MAPA REAL (so para depuracao: o agente NAO usa isso para decidir)
  - CONHECIMENTO DO AGENTE (o que ele percebeu e inferiu)
"""
import os

SETA = {'norte': '^', 'leste': '>', 'sul': 'v', 'oeste': '<'}
TAMANHO = 12


def _conjunto(prolog, consulta, vx='X', vy='Y'):
    return {(s[vx], s[vy]) for s in prolog.query(consulta)}


def desenha(prolog, acao, n, limpar=True):
    pos = list(prolog.query("posicao(X,Y,D)"))[0]
    x, y, d = pos['X'], pos['Y'], str(pos['D'])
    energia = list(prolog.query("energia(E)"))[0]['E']
    pontos = list(prolog.query("pontuacao(P)"))[0]['P']
    ouro = list(prolog.query("ouro_coletado(N)"))[0]['N']

    reais = {}
    for s in prolog.query("tile(X,Y,Z)"):
        z = str(s['Z'])
        if z:
            reais[(s['X'], s['Y'])] = z
    visitadas = _conjunto(prolog, "percepcao_vista(X,Y,_)")
    seguras = {tuple(c) for c in list(prolog.query("seguras(L)"))[0]['L']}
    inimigos = _conjunto(prolog, "bloqueada(X,Y)")
    teles = _conjunto(prolog, "tele(X,Y)")
    itens = _conjunto(prolog, "u_visto(X,Y)")

    def celula_real(cx, cy):
        if (cx, cy) == (x, y):
            return 'X' if d == 'morto' else SETA.get(d, '?')
        return reais.get((cx, cy), '.')

    def celula_agente(cx, cy):
        if (cx, cy) == (x, y):
            return 'X' if d == 'morto' else SETA.get(d, '?')
        if (cx, cy) in inimigos:
            return '#'
        if (cx, cy) in teles:
            return 't'
        if (cx, cy) in itens:
            return 'U'
        if (cx, cy) in visitadas:
            return '.'
        if (cx, cy) in seguras:
            return 's'
        return '?'

    linhas = []
    if limpar:
        linhas.append("\033[H\033[2J")
    linhas.append("acao #%d: %-15s energia=%s pontos=%s ouro=%d/3"
                  % (n, acao, energia, pontos, ouro))
    linhas.append("")
    linhas.append("   MAPA REAL (so depuracao)          CONHECIMENTO DO AGENTE")
    topo = "    " + " ".join("%2d" % c for c in range(1, TAMANHO + 1))
    linhas.append(topo + "     " + topo)
    for cy in range(TAMANHO, 0, -1):
        a = " ".join("%2s" % celula_real(cx, cy) for cx in range(1, TAMANHO + 1))
        b = " ".join("%2s" % celula_agente(cx, cy) for cx in range(1, TAMANHO + 1))
        linhas.append("%2d  %s     %2d  %s" % (cy, a, cy, b))
    linhas.append("")
    linhas.append("Real: P=poco d/D=inimigo T=teletransp. O=ouro U=energia  ^>v<=agente")
    linhas.append("Agente: .=visitada s=segura(nao visitada) ?=desconhecida "
                  "#=inimigo t=teleporte U=energia")
    print("\n".join(linhas), flush=True)