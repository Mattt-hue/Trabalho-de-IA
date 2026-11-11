"""
Teste sem interface: imita o ciclo do gmap.py com o planejador em Python.
uso: python teste_py.py [semente] [max_acoes] [--ver [segundos_por_acao]]
  --ver  mostra o agente jogando no terminal (ex.: --ver 0.2)
"""
import sys, time, random
from pyswip import Prolog
from planejador import decidir
from visualiza import desenha

args = sys.argv[1:]
ver = '--ver' in args
atraso = 0.2
if ver:
    i = args.index('--ver')
    if i + 1 < len(args):
        atraso = float(args[i + 1])
        del args[i + 1]
    del args[i]
semente = int(args[0]) if len(args) > 0 else 1
max_acoes = int(args[1]) if len(args) > 1 else 3000

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
    if ver:
        desenha(prolog, a, acoes, limpar=atraso > 0)
        time.sleep(atraso)

pontos = list(prolog.query("pontuacao(P)"))[0]['P']
energia = list(prolog.query("energia(E)"))[0]['E']
ouro = ouro0 - len(list(prolog.query("tile(_,_,'O')")))
morto = str(list(prolog.query("posicao(_,_,D)"))[0]['D']) == 'morto'
print("seed=%d acoes=%d pontos=%s energia=%s ouro=%d/%d %s" %
      (semente, acoes, pontos, energia, ouro, ouro0, 'morto' if morto else 'vivo'))