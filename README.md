# INF1771 – Trabalho 1: Busca Heurística (Pokémon / Kanto)

## Como rodar
```
pip install numpy matplotlib pillow
python main.py                    # tudo + certificado de otimalidade da rota (~1-2 min, ~0,8 GB RAM)
python main.py --execucoes 30     # experimento HC/SA/GA com 30 execuções cada
python main.py --sem-certificado  # só o A* ponderado (segundos)
python main.py --visual           # gera resultado.png e resultado.gif
python main.py --ascii            # mapa no console
```
Arquivos: `config.py` (custos de terreno, dificuldades, poderes, energia), `mapa.txt` (mapa 42x150,
editável), `mapa.py`, `rota.py` (A*), `batalhas.py` (busca local), `visual.py`, `main.py`.

## Tarefa 1 – Batalhas (busca local)
* **Representação:** 24 máscaras de bits (1..31); bit p = Pokémon p luta naquele ginásio.
* **Custo:** Σ dificuldade_i / Σ poder + 100 · (violações de energia). Restrições: cada Pokémon luta ≤ 6 vezes
  e pelo menos um luta ≤ 5 vezes (chega com energia ≥ 1). A penalidade (100) é maior que o maior ganho
  possível de um uso extra (~58 min), então o ótimo penalizado é viável.
* **Vizinhança:** alternar Pokémon, substituir Pokémon, transferir Pokémon entre ginásios, trocar equipes entre ginásios.
* **Algoritmos:** Hill Climbing (ascensão máxima + 20 reinícios), Simulated Annealing, Algoritmo Genético.
* **Referência exata:** DP sobre (ginásio, uso dos 5 Pokémon) – 7^5 estados – prova o ótimo global das batalhas.

## Tarefa 2 – Rota (A*)
* **Estado:** (ponto atual, conjunto de ginásios visitados) – o conjunto é uma máscara de 24 bits.
* **Ações:** ir pelo caminho mínimo da grade até um ginásio não visitado; com todos visitados, ir a U.
* **Custo:** 1 (origem) + soma do custo de terreno de cada célula entrada (M=200, A=30, F=15, R=5, .=1).
  Pernas calculadas na grade 4-conexa; o A* célula a célula (h = Manhattan × menor custo) é usado na visualização.
* **Heurística:** h = menor aresta do ponto atual a um ginásio livre + MST dos ginásios livres + menor aresta de um
  ginásio livre ao destino. Admissível e consistente.
* **Otimalidade:** com peso 1 o A* é ótimo, mas em Python não termina para 24 ginásios (>600 mil expansões, sem fim).
  Por isso: A* ponderado (peso 2) dá solução rápida (custo 1253, 266 expansões) e a **otimalidade é certificada
  por Held-Karp exato** (custo 1210).

## Independência dos problemas
O tempo de um ginásio depende só da dificuldade e dos Pokémon escolhidos, não da ordem de visita.
Logo C_total ótimo = rota ótima + batalhas ótimas.

## Visualização do processo no terminal

```
python main.py --terminal                  # tudo ao vivo, de ponta a ponta
python main.py --terminal --execucoes 3    # mais curto (menos execuções da busca local)
python main.py --terminal --velocidade 3   # animação mais rápida (0.5 = mais lenta)
python main.py --quadros                   # grava passo_a_passo.txt (texto puro, p/ relatório)
```

`--terminal` mostra TODAS as tentativas até o resultado final, em ordem:

1. **Tarefa 1 (busca local)**: cada execução de Hill Climbing (com seus 20 reinícios), Simulated
   Annealing (iterações, temperatura) e Algoritmo Genético (gerações, melhor e média da população) é
   mostrada ao vivo, com o custo caindo; ao fim de cada execução fica uma linha com o custo final.
2. **Tarefa 2, tentativa 1**: A* EXATO (peso 1) por 8 s, mostrando estados expandidos, fronteira e
   profundidade; ele não termina (por isso o A* ponderado).
3. **Tarefa 2, tentativa 2**: A* PONDERADO (peso 2), com cada expansão e a rota parcial.
4. **Held-Karp** (certificado de otimalidade): barra de progresso por camada; mostra a melhoria
   1253 -> 1210 e adota a rota ótima.
5. **Animação do mapa**: para cada perna, o A* na grade expandindo (`+` expandido, `?` fronteira), o
   agente `@` andando (`*`), batalhas, energia e custos acumulados.
6. **Resultado final** completo.

Dicas: terminal em tela cheia (ideal >= 155 colunas x 52 linhas; se for menor, o mapa é recortado e
acompanha o agente). No Windows use o Windows Terminal ou PowerShell 7. Para o relatório, grave a
tela (Win+G) ou use `--quadros` (um quadro por perna, UTF-8).
