"""Bonato & Kamali 3-approximation for graph burning (owner: Tim). arXiv:1811.04449.

Burn-Guess(G, g): scan the vertices in a fixed order; a vertex further than 2g - 2 from every
centre so far becomes a new centre. Reaching g centres means "bad guess": those g centres are
pairwise >= 2g - 1 apart, which forces b(G) >= g (paper, Lemmas 1-2). Otherwise the < g centres
are a burning sequence that finishes within (g - 1) + (2g - 2) = 3g - 3 rounds.

Binary search finds g with Burn-Guess(g - 1) bad and Burn-Guess(g) good, so
rounds <= 3g - 3 = 3(g - 1) <= 3 b(G).
"""

from collections import deque
from collections.abc import Hashable

import networkx as nx

from burning.algorithms.registry import register


def burn_guess(G: nx.Graph, g: int) -> list[Hashable] | None:
    """Centres for guess g (in discovery order), or None for a bad guess."""
    radius = 2 * g - 2
    dist: dict[Hashable, int] = {}  # distance to nearest centre, only tracked up to radius
    centres: list[Hashable] = []
    for v in G:
        if v in dist:
            continue
        centres.append(v)
        if len(centres) >= g:
            return None
        # BFS from the new centre, only through vertices it brings strictly closer
        dist[v] = 0
        queue = deque([v])
        while queue:
            u = queue.popleft()
            if dist[u] == radius:
                continue
            for w in G[u]:
                if dist.get(w, radius + 1) > dist[u] + 1:
                    dist[w] = dist[u] + 1
                    queue.append(w)
    return centres


def three_approx_with_bound(G: nx.Graph) -> tuple[list[Hashable], int]:
    """Burning sequence plus a certified lower bound on b(G) from the last bad guess."""
    if G.number_of_nodes() == 0:
        raise ValueError("graph has no vertices")
    # Invariant: guess `lo` is bad, guess `hi` is good. g = 1 is always bad (the first vertex
    # alone reaches g centres); g = n + 1 is always good (at most n centres exist).
    lo, hi = 1, G.number_of_nodes() + 1
    best = burn_guess(G, hi)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        centres = burn_guess(G, mid)
        if centres is None:
            lo = mid
        else:
            hi, best = mid, centres
    return best, lo


@register("three_approx")
def three_approx(G: nx.Graph) -> list[Hashable]:
    return three_approx_with_bound(G)[0]
