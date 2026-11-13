"""Burning-aware farthest-first heuristic for graph burning (owner: Nathaniel).

Based on the farthest-first selection principle of Garcia-Diaz et al.
Each round, choose the unburned vertex farthest from its nearest
previously selected source. Ties follow the graph's node order.

Unlike the paper's BFF algorithm, this variant only ignites unburned
vertices and does not claim the paper's approximation guarantee.
"""

from collections.abc import Hashable

import networkx as nx

from burning.algorithms.registry import register


@register("farthest_first")
def farthest_first(G: nx.Graph) -> list[Hashable]:
    """Return ignition sources selected by burning-aware farthest-first.

    The first vertex in G is selected initially. In later rounds, fire
    spreads before the next source is chosen. The input is unchanged.
    """
    if G.number_of_nodes() == 0:
        raise ValueError("graph has no vertices")
    if not nx.is_connected(G):
        raise ValueError("farthest_first requires a connected graph")

    nodes = list(G)
    first = nodes[0]

    sequence: list[Hashable] = [first]
    burned: set[Hashable] = {first}
    frontier: set[Hashable] = {first}

    # Distance from each vertex to its nearest selected source.
    nearest = dict(nx.single_source_shortest_path_length(G, first))

    while len(burned) < G.number_of_nodes():
        # Step 1: spread fire from the previous round's new vertices.
        new = set()
        for u in frontier:
            new.update(v for v in G[u] if v not in burned)

        burned.update(new)
        frontier = new

        if len(burned) == G.number_of_nodes():
            break

        # Step 2: select the farthest unburned vertex.
        # Python's max preserves the first vertex on a tie.
        source = max(
            (v for v in nodes if v not in burned),
            key=lambda v: nearest[v],
        )

        sequence.append(source)
        burned.add(source)
        frontier.add(source)

        # Update distances to the nearest selected source.
        distances = nx.single_source_shortest_path_length(G, source)
        for v, distance in distances.items():
            nearest[v] = min(nearest[v], distance)

    return sequence
