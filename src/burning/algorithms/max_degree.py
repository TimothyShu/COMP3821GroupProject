"""Max-degree greedy heuristic for graph burning (owner: Antyabha).

Rank every vertex by its degree in G once, before any round runs. Each round follows the
model in simulate.py: fire first spreads to every neighbour of a burned vertex, then the
next source is the highest-ranked vertex that is still eligible. Ties go to the vertex
that comes first in G's node order, so the output is deterministic.
Stop when every vertex is burned.
"""

from collections.abc import Hashable

import networkx as nx

from burning.algorithms.registry import register


def sorted_vertex_degree(G: nx.Graph) -> list[Hashable]:
    """Vertices of G, highest degree first. Ties keep G's node order (sorted is stable)."""
    return sorted(G.nodes(), key=G.degree, reverse=True)


def spread(G: nx.Graph, burned: set[Hashable]) -> set[Hashable]:
    """Vertices burned in current round: unburned neighbours of `burned`. Does not modify `burned`."""
    # Only last round's new vertices can
    # reach anything unburned, so passing just those would make the whole run O(n + m).
    spreaded: set[Hashable] = set()
    for burnt_node in burned:
        spreaded.update(G.neighbors(burnt_node))
    return spreaded - burned


def next_source(ranked: list[Hashable], burned: set[Hashable]) -> Hashable | None:
    """First vertex in `ranked` not in `burned`, or None if every vertex is burned.
    """
    return next((v for v in ranked if v not in burned), None)


@register("max_degree")
def max_degree(G: nx.Graph) -> list[Hashable]:
    """Burning sequence for G, sources in ignition order. Does not modify G."""
    ranked = sorted_vertex_degree(G)
    burned: set[Hashable] = set()
    sequence: list[Hashable] = []
    while len(burned) < G.number_of_nodes():
        burned.update(spread(G, burned))  # step 1: fire spreads (nothing burns yet in round 1)
        source = next_source(ranked, burned)  # step 2: light a source if any vertex is left
        if source is not None:
            burned.add(source)
            sequence.append(source)
    return sequence
