"""Co-evolutionary synthesis of a proof-carrying controller.

A genome is a PAIR of symbolic trees: (controller u, Lyapunov proof V), evolved
together so the search prefers controllers that are easy to PROVE stable.

Fitness IS the verifier: every genome is scored by the actual certificate
margins (worst positivity slack, worst decrease slack, and the analytic origin
conditions) on a coarse grid. Once a genome clears all of them it is "certifiable"
and the objective switches to minimizing formula size -- so the search returns
the SHORTEST law+proof it can. Champions are re-confirmed at full resolution.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from proofforge.expr import C, F, Node, crossover, mutate, rand_tree
from proofforge.verifier import verify


@dataclass
class Genome:
    u: Node
    V: Node
    score: float = -1e18
    viol: float = 1e9
    size: int = 0
    certified: bool = False


def seed_genomes(plant) -> list[tuple[Node, Node]]:
    """Structurally useful (controller, Lyapunov) starting pairs."""
    g = plant.g_over_l

    def lin_u(k0, k1, k2):
        return Node("-", (Node("-", (Node("neg", (Node("*", (C(k0), F(2))),)),
                                     Node("*", (C(k1), F(0))))),
                          Node("*", (C(k2), F(1)))))

    def quad_V(a, b, c):
        return Node("+", (Node("+", (Node("*", (C(a), Node("square", (F(0),)))),
                                     Node("*", (C(b), Node("square", (F(1),)))))),
                          Node("*", (C(c), Node("*", (F(0), F(1)))))))

    return [
        (lin_u(g, 1.5 * g, 8.0), quad_V(2 * g, 1.0, 1.0)),
        (lin_u(g, 2 * g, 10.0), quad_V(2 * g, 1.0, 1.0)),
        (lin_u(0.0, 2.5 * g, 10.0), quad_V(2 * g, 1.0, 0.5)),
        (lin_u(g, 3 * g, 12.0), quad_V(3 * g, 1.0, 1.0)),
        (lin_u(g, 1.5 * g, 6.0), quad_V(1.5 * g, 0.5, 0.5)),
    ]


def _consts(root: Node) -> list:
    out, stack = [], [root]
    while stack:
        nd = stack.pop()
        if nd.op == "const":
            out.append(nd)
        stack.extend(nd.children)
    return out


def _perturb_seed(u, V, rng, amt=0.5):
    u, V = u.copy(), V.copy()
    for tree in (u, V):
        for nd in _consts(tree):
            nd.value *= (1.0 + float(rng.normal(0, amt)))
    return u, V


def fitness(u: Node, V: Node, plant, *, length_penalty=0.003, n_grid=71):
    """Score a genome by the verifier's OWN margins. Higher is better.

    Not-yet-certifiable genomes are ranked by how close their worst margin is to
    zero (push it positive); certifiable genomes jump to a high plateau where the
    only remaining pressure is to shrink the formula.
    """
    try:
        rep = verify(u, V, plant, n_theta=n_grid, n_omega=n_grid)
    except Exception:
        return -1e12, 1e9
    ps, ds = rep["worst_pos_slack"], rep["worst_dec_slack"]
    op, od = rep["origin_pos_def"], rep["origin_decreasing"]
    worst = min(ps, ds)
    # If it looks certifiable on the coarse grid, CONFIRM at full resolution so a
    # candidate cannot reach the "done" plateau by exploiting a coarse grid that
    # steps over a thin violation. This keeps the search's notion of "certified"
    # identical to the final verifier's.
    if (worst > 0) and op and od:
        rep = verify(u, V, plant)
        ps, ds = rep["worst_pos_slack"], rep["worst_dec_slack"]
        op, od = rep["origin_pos_def"], rep["origin_decreasing"]
        worst = min(ps, ds)
    origin_pen = (0.0 if op else 1.0) + (0.0 if od else 1.0)
    size = u.size() + V.size()
    ok = (worst > 0) and op and od
    if ok:
        return 100.0 - length_penalty * size, 0.0
    return min(worst, 0.0) - origin_pen - 0.001 * size, origin_pen + max(0.0, -worst)


def _hillclimb_consts(gen: Genome, plant, rng, iters=25):
    best = gen
    for _ in range(iters):
        u2, V2 = best.u.copy(), best.V.copy()
        for tree in (u2, V2):
            for node in _consts(tree):
                if rng.random() < 0.5:
                    node.value += float(rng.normal(0, 0.4))
        sc, vi = fitness(u2, V2, plant)
        if sc > best.score:
            best = Genome(u2, V2, sc, vi, u2.size() + V2.size())
    return best


def _tournament(pop, rng, k=4):
    picks = [pop[int(i)] for i in rng.integers(0, len(pop), size=k)]
    return max(picks, key=lambda z: z.score)


def synthesize(plant, *, seed=0, pop=180, generations=45, max_depth=5, verbose=True):
    rng = np.random.default_rng(seed)

    def make(u, V):
        sc, vi = fitness(u, V, plant)
        return Genome(u, V, sc, vi, u.size() + V.size())

    population: list[Genome] = []
    for (u, V) in seed_genomes(plant):
        pu, pV = _perturb_seed(u, V, rng)
        population.append(make(pu, pV))
    while len(population) < pop:
        base = population[int(rng.integers(0, len(population)))]
        population.append(make(mutate(base.u, rng, max_depth),
                               mutate(base.V, rng, max_depth)))

    hall = max(population, key=lambda z: z.score)
    champion = None
    first_cert_gen = None
    history = []

    for gen in range(generations):
        population.sort(key=lambda z: z.score, reverse=True)
        children = [Genome(e.u.copy(), e.V.copy(), e.score, e.viol, e.size)
                    for e in population[: max(2, pop // 10)]]
        while len(children) < pop:
            a = _tournament(population, rng)
            b = _tournament(population, rng)
            u1, u2 = crossover(a.u, b.u, rng)
            v1, v2 = crossover(a.V, b.V, rng)
            if rng.random() < 0.6:
                u1 = mutate(u1, rng, max_depth)
            if rng.random() < 0.6:
                v1 = mutate(v1, rng, max_depth)
            children.append(make(u1, v1))
            if len(children) < pop:
                children.append(make(u2, v2))
        population = children

        population.sort(key=lambda z: z.score, reverse=True)
        population[0] = _hillclimb_consts(population[0], plant, rng)

        best = max(population, key=lambda z: z.score)
        if best.score > hall.score:
            hall = best

        for cand in sorted(population, key=lambda z: z.score, reverse=True)[:6]:
            if cand.viol > 0:
                continue
            rep = verify(cand.u, cand.V, plant)         # full-resolution confirm
            if rep["certified"]:
                if champion is None or cand.size < champion.size:
                    champion = Genome(cand.u.copy(), cand.V.copy(), cand.score,
                                      0.0, cand.size, True)
                if first_cert_gen is None:
                    first_cert_gen = gen

        csize = champion.size if champion else None
        history.append({"gen": gen, "best_score": hall.score,
                        "champion_size": csize})
        if verbose:
            tag = f"champion_size={csize}" if csize else "no certified yet"
            print(f"gen {gen:02d}  best_score={hall.score:.3f}  {tag}")

        # Early stop: once certified, allow a few generations to shrink, then finish.
        if champion is not None and first_cert_gen is not None and gen >= first_cert_gen + 5:
            break

    return {"champion": champion, "hall": hall, "history": history,
            "first_cert_gen": first_cert_gen}


if __name__ == "__main__":
    from proofforge.plant import Plant
    p = Plant(g_over_l=10.0, damping=0.0)
    res = synthesize(p, seed=1, pop=160, generations=30)
    ch = res["champion"]
    print("first certified at generation:", res["first_cert_gen"])
    if ch:
        print("SHORTEST certified controller u =", ch.u.to_math())
        print("SHORTEST certified proof      V =", ch.V.to_math())
        print("total size (nodes):", ch.size)
        rep = verify(ch.u, ch.V, p)
        print("re-verify certified:", rep["certified"],
              "| RoA frac:", round(rep["roa_area_fraction"], 3))
