import random

import networkx as nx

from burning.generators.registry import register


@register("spider")
def spider(n: int, *, seed: int | None = None, legs: int = 3) -> nx.Graph:
    """Centre vertex 0 with `legs` summing to n - 1.

    The n - 1 non-centre vertices sit in a row. `legs - 1` distinct cut points from
    1..n-2 split the row into `legs` non-empty pieces, and each piece is one leg.

    Example: n = 10, legs = 3. The row has 9 vertices. If the cut points are [6, 2],
    sorting gives [2, 6], and the gaps between 0, 2, 6 and 9 give leg lengths [2, 4, 3].
    """
    if legs < 3:
        raise ValueError("spider needs at least 3 legs")
    if n < legs + 1:
        raise ValueError(f"spider with {legs} legs needs n >= {legs + 1}")

    # Random selecting cut points from n - 1 vertices for `legs` paths.
    cuts = sorted(random.Random(seed).sample(range(1, n - 1), legs - 1))
    lengths = [b - a for a, b in zip([0, *cuts], [*cuts, n - 1])]

    G = nx.Graph()
    nxt = 1
    for length in lengths:
        nx.add_path(G, [0, *range(nxt, nxt + length)])
        nxt += length

    G = nx.convert_node_labels_to_integers(G)
    G.graph["family"] = "spider"
    G.graph["params"] = {"legs": legs}
    return G
