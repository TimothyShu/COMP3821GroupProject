"""Registry of burning algorithms. See README "Algorithm interface" for the contract."""

from collections.abc import Callable, Hashable

import networkx as nx

ALGORITHMS: dict[str, Callable[[nx.Graph], list[Hashable]]] = {}


def register(name: str):
    """Decorator: add an algorithm to ALGORITHMS under `name`."""

    def wrap(fn):
        if name in ALGORITHMS:
            raise ValueError(f"algorithm {name!r} registered twice")
        ALGORITHMS[name] = fn
        return fn

    return wrap
