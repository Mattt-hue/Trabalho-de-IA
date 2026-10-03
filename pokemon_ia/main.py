#!/usr/bin/env python3
"""
INF1771 - Trabalho 1: Busca Heurística (Pokémon / Kanto)

  Tarefa 1  seleção dos Pokémon em cada ginásio  -> busca local (HC, SA ou GA)
  Tarefa 2  rota de menor custo 1 -> 24 ginásios -> U   -> A*

Exemplos:
  python main.py                       # tudo, com certificado de otimalidade (~1 min)
  python main.py --execucoes 30        # experimento com 30 execuções de HC/SA/GA
  python main.py --sem-certificado     # só o A* ponderado (rápido, não garante ótimo)
  python main.py --visual              # gera resultado.png e resultado.gif
  python main.py --ascii               # mapa no console
"""
import argparse
import random
import statistics as st
import time

import batalhas as B
import config
from mapa import Mapa
from rota import PontosChave, astar_ginasios, astar_grade, held_karp


def log(msg):
    print(msg, flush=True)


# ----------------------------------------------------------------- Tarefa 1
def experimento_busca_local(execucoes, algoritmos):
    """Executa cada algoritmo `execucoes` vezes. Devolve {alg: dict(estatísticas, melhor)}."""
    out = {}
    for nome in algoritmos:
        fn = B.ALGORITMOS[nome]
        res, melhor = [], None
        t0 = time.time()
        for k in range(execucoes):
            rng = random.Random(config.SEMENTE + 1000 * k + hash(nome) % 97)
            sol, c = fn(rng)
            res.append(c)
            if melhor is None or c < melhor[1]:
                melhor = (sol, c)
        out[nome] = dict(melhor=melhor, custos=res, n=execucoes, tempo=time.time() - t0,
                         media=st.mean(res), desvio=st.pstdev(res) if len(res) > 1 else 0.0)
    return out


# ----------------------------------------------------------------- Tarefa 2
def planejar_rota(pc, peso, certificar):
    log(f"\n[Tarefa 2] A* sobre (ginásio atual, conjunto visitado), peso={peso}")
    r = astar_ginasios(pc, peso=peso, limite_estados=3_000_000, tempo_max=120, log=log)
    if r is None:
        raise SystemExit("A* estourou o limite de estados; aumente --peso.")
    log(f"  A*: custo {r['custo']} | expandidos {r['expandidos']:,} | gerados {r['gerados']:,} "
        f"| {r['tempo']:.2f}s | ótimo garantido: {'sim' if r['otimo'] else 'não (peso>1)'}")
    ordem, custo, fonte = r["ordem"], r["custo"], f"A* (peso {peso})"
    otimo = None
    if certificar:
        log("  Certificando otimalidade com Held-Karp exato (numpy, ~1 min, ~0,8 GB RAM)...")
        t0 = time.time()
        copt, oopt = held_karp(pc)
        otimo = copt
        log(f"  Held-Karp: custo ótimo global = {copt} ({time.time() - t0:.0f}s)")
        if copt < custo:
            log(f"  -> A* ponderado ficou {custo - copt} min ({100 * (custo - copt) / copt:.1f}%) acima do ótimo; "
                f"usando a rota ótima.")
            ordem, custo, fonte = oopt, copt, "Held-Karp (ótimo exato)"
        else:
            log("  -> o A* já encontrou o ótimo global.")
    return dict(ordem=ordem, custo=custo, fonte=fonte, astar=r, otimo=otimo)


def percorrer(mapa, pc, ordem, mascaras):
    """Simula o agente célula a célula. Devolve caminho, custos acumulados, eventos."""
    energia = [config.ENERGIA_INICIAL] * B.NP
    caminho, acum, eventos = [], [], []
    total = 0.0
    c_rota = c_bat = 0.0
    registros = []
    for a, b in zip(ordem, ordem[1:]):
        trecho = pc.caminho(a, b)
        ini = 0 if not caminho else 1
        for p in trecho[ini:]:
            c_rota += mapa.custo[p[0]][p[1]] if caminho else config.CUSTO_ORIGEM_DESTINO
            total = c_rota + c_bat
            caminho.append(p); acum.append(total); eventos.append("")
        if 1 <= b <= len(pc.ids):
            g = b - 1
            m = mascaras[g]
            tempo = B.DIFS[g] / B.PODER_MASK[m]
            for p in B.BITS[m]:
                energia[p] -= config.PERDA_POR_BATALHA
            c_bat += tempo
            acum[-1] = c_rota + c_bat
            eventos[-1] = f"Gym {pc.nomes[b]}: {'+'.join(B.NOMES[p] for p in B.BITS[m])} ({tempo:.1f} min)"
            registros.append((len(registros) + 1, pc.nomes[b], g + 1, B.DIFS[g],
                              [B.NOMES[p] for p in B.BITS[m]], tempo, c_rota, c_bat, list(energia)))
    return dict(caminho=caminho, acum=acum, eventos=eventos, c_rota=c_rota, c_bat=c_bat,
                energia=energia, registros=registros)


# --------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mapa", default="mapa.txt")
    ap.add_argument("--algoritmo", choices=["hc", "sa", "ga"], default="hc",
                    help="busca local usada no plano final de batalhas (padrão: hc)")
    ap.add_argument("--execucoes", type=int, default=10, help="execuções por algoritmo no experimento")
    ap.add_argument("--peso", type=float, default=2.0,
                    help="peso do A* (f = g + peso*h). 1.0 = A* exato, mas impraticável em Python p/ 24 ginásios")
    ap.add_argument("--sem-certificado", action="store_true", help="não roda o Held-Karp exato")
    ap.add_argument("--visual", action="store_true", help="gera resultado.png e resultado.gif")
    ap.add_argument("--ascii", action="store_true", help="imprime o mapa com o caminho no console")
    args = ap.parse_args()

    mapa = Mapa(args.mapa)
    log(f"Mapa {mapa.altura}x{mapa.largura} | origem {mapa.pos[config.ORIGEM]} | destino {mapa.pos[config.DESTINO]}")
    pc = PontosChave(mapa)

    # ---- Tarefa 1: busca local
    log(f"\n[Tarefa 1] Busca local ({args.execucoes} execuções por algoritmo)")
    exp = experimento_busca_local(args.execucoes, ["hc", "sa", "ga"])
    sol_opt, c_opt = B.otimo_exato()
    log(f"  {'alg':<4}{'melhor':>10}{'execuções':>11}{'média':>10}{'desvio':>9}{'tempo(s)':>10}")
    for nome, e in exp.items():
        log(f"  {nome:<4}{e['melhor'][1]:>10.3f}{e['n']:>11}{e['media']:>10.3f}{e['desvio']:>9.3f}{e['tempo']:>10.1f}")
    log(f"  referência (DP exata, ótimo global das batalhas): {c_opt:.3f}")
    mascaras, c_bat_busca = exp[args.algoritmo]["melhor"]
    assert B.viavel(mascaras)
    log(f"  plano usado: melhor execução de '{args.algoritmo}' = {c_bat_busca:.3f} min "
        f"({'= ótimo global' if abs(c_bat_busca - c_opt) < 1e-6 else f'+{c_bat_busca - c_opt:.3f} sobre o ótimo'})")

    # ---- Tarefa 2: rota
    rota = planejar_rota(pc, args.peso, not args.sem_certificado)
    ordem = rota["ordem"]

    # ---- execução
    sim = percorrer(mapa, pc, ordem, mascaras)
    total = sim["c_rota"] + sim["c_bat"]
    assert abs(sim["c_rota"] - rota["custo"]) < 1e-6, (sim["c_rota"], rota["custo"])

    log("\n================ RESULTADO FINAL ================")
    log("Ordem de visita e Pokémon usados em cada batalha:")
    log(f"  {'#':>2} {'Gym':>3} {'nº':>3} {'dific':>6}  {'Pokémon':<42}{'tempo':>8}{'rota acum.':>12}{'bat. acum.':>12}")
    for n, marc, gid, dif, pk, t, cr, cb, _ in sim["registros"]:
        log(f"  {n:>2} {marc:>3} {gid:>3} {dif:>6}  {', '.join(pk):<42}{t:>8.2f}{cr:>12.0f}{cb:>12.2f}")
    log("\nEnergia final dos Pokémon:")
    for nome, e in zip(B.NOMES, sim["energia"]):
        log(f"  {nome:<12} {e}  {'(hibernando)' if e <= 0 else ''}")
    log(f"\nCusto das batalhas : {sim['c_bat']:.2f} min")
    log(f"Custo da rota      : {sim['c_rota']:.0f} min  [{rota['fonte']}]")
    log(f"CUSTO TOTAL        : {total:.2f} min")
    log(f"A*: {rota['astar']['expandidos']:,} estados expandidos, {rota['astar']['gerados']:,} gerados")
    log("\nGarantia de otimalidade:")
    if rota["otimo"] is not None:
        log(f"  Rota: custo {rota['custo']} == ótimo global certificado por Held-Karp ({rota['otimo']}): "
            f"{'ÓTIMA' if rota['custo'] == rota['otimo'] else 'não ótima'}.")
    else:
        log("  Rota: não certificada (use sem --sem-certificado); A* com peso>1 só garante custo <= peso*ótimo.")
    log(f"  Batalhas: {sim['c_bat']:.3f} vs DP exata {c_opt:.3f} -> "
        f"{'ÓTIMO GLOBAL' if abs(sim['c_bat'] - c_opt) < 1e-6 else 'sub-ótimo'}.")
    log("  Rota e batalhas são independentes (o tempo de um ginásio só depende dos Pokémon e da "
        "dificuldade, não da ordem),\n  logo C_total ótimo = rota ótima + batalhas ótimas.")

    if args.ascii:
        log("\n" + mapa_ascii_wrapper(mapa, sim["caminho"]))

    if args.visual:
        log("\nGerando visualização (A* célula a célula em cada perna)...")
        import visual
        exp_cel, fro_cel = set(), set()
        for a, b in zip(ordem, ordem[1:]):
            _, c, ex, fr = astar_grade(mapa, pc.coords[a], pc.coords[b])
            exp_cel.update(ex); fro_cel.update(fr)
        fro_cel -= exp_cel
        ordem_visita = [pc.nomes[i] for i in ordem[1:-1]]
        resumo = (f"Rota {sim['c_rota']:.0f} + batalhas {sim['c_bat']:.1f} = {total:.1f} min   |   "
                  f"A* (ginásios): {rota['astar']['expandidos']:,} estados expandidos   |   "
                  f"A* (células): {len(exp_cel):,} expandidas")
        visual.salvar_imagem(mapa, sim["caminho"], exp_cel, fro_cel, ordem_visita, resumo, "resultado.png")
        visual.salvar_gif(mapa, sim["caminho"], sim["acum"], sim["eventos"], exp_cel, fro_cel,
                          ordem_visita, "resultado.gif")
        log("  resultado.png e resultado.gif gerados.")


def mapa_ascii_wrapper(mapa, caminho):
    import visual
    return visual.mapa_ascii(mapa, caminho=caminho)


if __name__ == "__main__":
    main()
