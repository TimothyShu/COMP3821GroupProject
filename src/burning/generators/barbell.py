"""Barbell graphs: two cliques joined by a path (owner: Tim)."""

import networkx as nx

from burning.generators.registry import register

MIN_CLIQUE = 3


@register("barbell")
def barbell(n: int, *, seed: int | None = None, bridge_frac: float = 0.5) -> nx.Graph:
    """Two K_c cliques joined by a path of b vertices, with 2c + b = n exactly.

    About `bridge_frac` of the vertices sit on the path. Cliques have at least 3 vertices, so
    for small n the path is shortened to fit. Deterministic, so `seed` is ignored.
    """
    if not 0 <= bridge_frac < 1:
        raise ValueError(f"bridge_frac must be in [0, 1) (got {bridge_frac})")
    if n < 2 * MIN_CLIQUE:
        raise ValueError(f"barbell needs n >= {2 * MIN_CLIQUE} (got {n})")
    clique = max(MIN_CLIQUE, (n - int(n * bridge_frac)) // 2)
    bridge = n - 2 * clique  # odd leftover vertex goes on the path
    G = nx.barbell_graph(clique, bridge)
    G.graph["family"] = "barbell"
    G.graph["params"] = {"bridge_frac": bridge_frac, "clique": clique, "bridge": bridge}
    return G
