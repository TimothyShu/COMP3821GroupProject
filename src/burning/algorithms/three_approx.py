"""Bonato & Kamali 3-approximation for graph burning (owner: Tim). arXiv:1811.04449.

Burn-Guess(G, g): scan the vertices in a fixed order; a vertex further than 2g - 2 from every
centre so far becomes a new centre. Reaching g centres means "bad guess": those g centres are
pairwise >= 2g - 1 apart, which forces b(G) >= g (paper, Lemmas 1-2). Otherwise the < g centres
are a burning sequence that finishes within (g - 1) + (2g - 2) = 3g - 3 rounds.

Binary search finds g with Burn-Guess(g - 1) bad and Burn-Guess(g) good, so
rounds <= 3g - 3 = 3(g - 1) <= 3 b(G).

The proof never uses the scan order, so any order keeps the guarantee (see hybrid_approx.py).
"""

from collections import deque
from collections.abc import Callable, Hashable, Iterable

import networkx as nx

from burning.algorithms.registry import register

Guess = Callable[[int], list[Hashable] | None]


def relax(G: nx.Graph, source: Hashable, dist: dict[Hashable, int], limit: float) -> None:
    """Add `source` as a centre: BFS that lowers dist[v] (distance to nearest centre) wherever
    the new centre is strictly closer, without going beyond distance `limit`."""
    dist[source] = 0
    queue = deque([source])
    while queue:
        u = queue.popleft()
        if dist[u] >= limit:
            continue
        for w in G[u]:
            if dist.get(w, limit + 1) > dist[u] + 1:
                dist[w] = dist[u] + 1
                queue.append(w)


def burn_guess(G: nx.Graph, g: int, order: Iterable[Hashable] | None = None) -> list[Hashable] | None:
    """Centres for guess g (in discovery order), or None for a bad guess.

    `order` is the scan order (default: G's node order).
    """
    radius = 2 * g - 2
    dist: dict[Hashable, int] = {}  # distance to nearest centre, only tracked up to radius
    centres: list[Hashable] = []
    for v in G if order is None else order:
        if v in dist:
            continue
        centres.append(v)
        if len(centres) >= g:
            return None
        relax(G, v, dist, radius)
    return centres


def search(G: nx.Graph, guess: Guess) -> tuple[list[Hashable], int]:
    """Binary search for adjacent guesses lo (bad) and lo + 1 (good).

    Returns the good guess's centres and lo, a certified lower bound on b(G).
    """
    if G.number_of_nodes() == 0:
        raise ValueError("graph has no vertices")
    # Invariant: guess `lo` is bad, guess `hi` is good. g = 1 is always bad (the first vertex
    # alone reaches g centres); g = n + 1 is always good (at most n centres exist).
    lo, hi = 1, G.number_of_nodes() + 1
    best = guess(hi)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        centres = guess(mid)
        if centres is None:
            lo = mid
        else:
            hi, best = mid, centres
    return best, lo


def three_approx_with_bound(G: nx.Graph) -> tuple[list[Hashable], int]:
    """Burning sequence plus a certified lower bound on b(G) from the last bad guess."""
    return search(G, lambda g: burn_guess(G, g))


@register("three_approx")
def three_approx(G: nx.Graph) -> list[Hashable]:
    return three_approx_with_bound(G)[0]
