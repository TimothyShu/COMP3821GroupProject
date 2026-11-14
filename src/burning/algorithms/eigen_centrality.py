"""Maximum eigenvector centrality heuristic for eigengraph centrality algorithm for graph burning (owner: Adam).

Rank every vertex by its eigenvector centrality score. Burn the vertex with the highest score and 
then burn the vertex with the next highest score in the subgraph of unburned vertices. Repeat until all vertices are burned.
"""

from collections.abc import Hashable
from scipy.sparse.linalg import eigsh

import networkx as nx
import numpy as np
import scipy.linalg

from burning.algorithms.registry import register


def spread(G: nx.Graph, burned: set[Hashable]) -> set[Hashable]:
    """Unburned neighbours of the burned set, the vertices that catch fire next round."""
    spreaded: set[Hashable] = set()
    for burnt_node in burned:
        spreaded.update(G.neighbors(burnt_node))
    return spreaded - burned

def _perron_vector(G: nx.Graph, nodes: list[Hashable]) -> tuple[float, dict[Hashable, float]]:
    """Top eigenvalue and unit-norm eigenvector centrality of the connected subgraph on nodes.

    nx.eigenvector_centrality_numpy runs ARPACK from a random start vector, so tied
    vertices can swap order between runs. A dense symmetric solve has no random start:
    the same graph always gives the same vector.
    """
    n = len(nodes)
    A = nx.to_scipy_sparse_array(G, nodelist=nodes, dtype=float)
    if n <= 200:  # tiny: dense is faster than ARPACK setup
        val, vec = scipy.linalg.eigh(A.toarray(), subset_by_index=[n - 1, n - 1])
    else:  # fixed start vector (not random), so the same graph gives the same result
        val, vec = eigsh(A, k=1, which="LA", v0=np.ones(n), tol=1e-12)
    v = np.abs(vec[:, 0])
    return float(val[0]), dict(zip(nodes, v / np.linalg.norm(v)))

def sorted_vertex_eigenvector(G: nx.Graph) -> list[Hashable]:
    """Rank vertices by eigenvector centrality, preserving node order on ties.

    On a disconnected graph the top eigenvector lives on the component with the largest
    top eigenvalue, so components are ranked by that eigenvalue first, then vertices by
    their score inside the component. A lone vertex (eigenvalue 0) therefore never beats
    a vertex with an unburned neighbour.
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
            val, vec = _perron_vector(G, sorted(nodes, key=node_order.__getitem__))
            rank.update({node: (val, score) for node, score in vec.items()})

    # Ignore tiny solver noise so mathematically tied vertices use node order.
    return sorted(
        G, key=lambda v: (-round(rank[v][0], 10), -round(rank[v][1], 10), node_order[v])
    )


def mech(G: nx.Graph, bg: int) -> list[Hashable] | None:
    """Burning sequence of length bg, or None (FAILED TO BURN)."""
    X: list[Hashable] = []
    burned: set[Hashable] = set()
    TG = G.copy()
    for i in range(1, bg + 1):
        comp = max(nx.connected_components(TG), key=lambda c: nx.diameter(TG.subgraph(c)))
        ecc = nx.eccentricity(TG.subgraph(comp))
        free = [v for v in ecc if v not in X]
        if i >= min(ecc.values()) and free:  # lines 4-5: most central vertex of that component
            x = min(free, key=ecc.get)
        else:  # line 6: highest eigenvector centrality in TG
            x = next(v for v in sorted_vertex_eigenvector(TG) if v not in X)
        X.append(x)
        burned |= set(nx.single_source_shortest_path_length(G, x, cutoff=bg - i))  # ego(G, bg - i, x)
        TG = G.copy()
        TG.remove_edges_from(list(G.subgraph(burned).edges()))
    return X if len(burned) == len(G) else None

@register("eigen_centrality")
def eigen_centrality(G: nx.Graph) -> list[Hashable]:
    """Smallest guess bg for which mech succeeds (bg = n always does)."""
    for bg in range(1, len(G) + 1):
        X = mech(G, bg)
        if X:
            return X
    return []