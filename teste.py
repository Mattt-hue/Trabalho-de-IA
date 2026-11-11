"""
Teste sem interface: imita o ciclo do gmap.py com o planejador em Python.
uso: python teste_py.py [semente] [max_acoes]
"""
import sys, random
from pyswip import Prolog
from planejador import decidir

semente = int(sys.argv[1]) if len(sys.argv) > 1 else 1
max_acoes = int(sys.argv[2]) if len(sys.argv) > 2 else 3000

prolog = Prolog()
prolog.consult('main.pl')
list(prolog.query("set_random(seed(%d))" % semente))
list(prolog.query("reset_game"))
ouro0 = len(list(prolog.query("tile(_,_,'O')")))
list(prolog.query("atualiza_obs, verifica_player"))

acoes = 0
while acoes < max_acoes:
    if str(list(prolog.query("posicao(_,_,D)"))[0]['D']) == 'morto':
        break
    a = decidir(prolog)
    if a == 'parar':
        break
    list(prolog.query(a))
    list(prolog.query("atualiza_obs, verifica_player"))
    acoes += 1

pontos = list(prolog.query("pontuacao(P)"))[0]['P']
energia = list(prolog.query("energia(E)"))[0]['E']
ouro = ouro0 - len(list(prolog.query("tile(_,_,'O')")))
morto = str(list(prolog.query("posicao(_,_,D)"))[0]['D']) == 'morto'
print("seed=%d acoes=%d pontos=%s energia=%s ouro=%d/%d %s" %
      (semente, acoes, pontos, energia, ouro, ouro0, 'morto' if morto else 'vivo'))