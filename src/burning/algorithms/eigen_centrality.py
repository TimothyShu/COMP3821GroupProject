"""Maximum eigenvector centrality heuristic for eigenvector centrality for graph burning (owner: Adam).

Rank every vertex by its eigenvector centrality score. Burn the vertex with the highest score and
then burn the vertex with the next highest score in the subgraph of unburned vertices. Repeat until all vertices are burned.
Check the burning number of the graph by running the mech function, which simulates the burning process and returns a burning sequence if successful.
"""

import math
from collections.abc import Hashable

import networkx as nx
import numpy as np
import scipy.linalg
from scipy.sparse.linalg import eigsh

from burning.algorithms.registry import register


def spread(G: nx.Graph, burned: set[Hashable]) -> set[Hashable]:
    """Unburned neighbours of the burned set, the vertices that catch fire next round."""
    spreaded: set[Hashable] = set()
    for burnt_node in burned:
        spreaded.update(G.neighbors(burnt_node))
    return spreaded - burned

def _perron_vector(G: nx.Graph, nodes: list[Hashable]) -> tuple[float, dict[Hashable, float]]:
    """Top eigenvalue and unit-norm eigenvector centrality of the connected subgraph on nodes.
    """
    n = len(nodes)
    A = nx.to_scipy_sparse_array(G, nodelist=nodes, dtype=float)
    if n <= 200: 
        val, vec = scipy.linalg.eigh(A.toarray(), subset_by_index=[n - 1, n - 1])
    else:  # Fixed start vector (not random), so the same graph gives the same result
        val, vec = eigsh(A, k=1, which="LA", v0=np.ones(n), tol=1e-12)
    v = np.abs(vec[:, 0])
    return float(val[0]), dict(zip(nodes, v / np.linalg.norm(v)))

def sorted_vertex_eigenvector(G: nx.Graph) -> list[Hashable]:
    """Rank vertices by eigenvector centrality, preserving node order on ties.
    """
    node_order = {node: i for i, node in enumerate(G)}
    rank: dict[Hashable, tuple[float, float]] = {}
    for nodes in nx.connected_components(G):
        if len(nodes) == 1:
            rank[next(iter(nodes))] = (0.0, 1.0)
        elif len(nodes) == 2:
            rank.update({node: (1.0, 1 / 2**0.5) for node in nodes})
        else:
            # Rows in G's order: set order would change the float noise between runs.
            value, vector = _perron_vector(G, sorted(nodes, key=node_order.__getitem__))
            rank.update({node: (value, score) for node, score in vector.items()})

    # Ignore tiny solver noise so mathematically tied vertices use node order.
    return sorted(
        G, key=lambda v: (-round(rank[v][0], 10), -round(rank[v][1], 10), node_order[v])
    )


def mech(G: nx.Graph, bg: int) -> list[Hashable] | None:
    """Burning sequence of length at most bg, or None (FAILED TO BURN).

    Each round only picks a vertex that is not yet on fire, so the sequence is a strict burning
    sequence. If every vertex is already on fire, G is burned and the sequence stops early.
    """
    X: list[Hashable] = []
    fire: dict[Hashable, int] = {}  # round each vertex catches fire, from the sources so far
    TG = G.copy()
    for i in range(1, bg + 1):
        unburned = {v for v in G if fire.get(v, bg + 1) > i}
        components = max(nx.connected_components(TG), key=lambda c: nx.diameter(TG.subgraph(c)))
        eccentricity = nx.eccentricity(TG.subgraph(components))
        free = [v for v in eccentricity if v in unburned]
        if i >= min(eccentricity.values()) and free:  # Retrieves most central vertex of that component
            x = min(free, key=eccentricity.get)
        else:  # Gets highest eigenvector centrality in TG
            x = next((v for v in sorted_vertex_eigenvector(TG) if v in unburned), None)
            if x is None:  # every vertex is already on fire
                break
        X.append(x)
        for v, d in nx.single_source_shortest_path_length(G, x, cutoff=bg - i).items():  # ego(G, bg - i, x)
            fire[v] = min(fire.get(v, bg + 1), i + d)
        TG.remove_edges_from(list(G.subgraph(fire).edges()))
    if len(fire) == len(G):
        return X
    else:
        return None


def diameter_lower_bound(G: nx.Graph) -> int:
    """ceil(sqrt(diam + 1)) <= b(G): a shortest path with diam + 1 vertices is isometric, and
    bg rounds burn at most 1 + 3 + ... + (2bg - 1) = bg^2 of its vertices."""
    diam = max((nx.diameter(G.subgraph(c), usebounds=True) for c in nx.connected_components(G)), default=0)
    return math.isqrt(diam) + 1  # ceil(sqrt(diam + 1))


@register("eigen_centrality")
def eigen_centrality(G: nx.Graph) -> list[Hashable]:
    """Smallest guess bg for which mech succeeds (bg = n always does).

    mech(G, bg) succeeding means b(G) <= bg, so every bg below the diameter bound fails and the
    search can start there without changing the result.
    """
    for bg in range(diameter_lower_bound(G) if len(G) else 1, len(G) + 1):
        X = mech(G, bg)
        if X:
            return X
    return []