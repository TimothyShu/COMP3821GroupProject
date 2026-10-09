"""Registry of graph families. See README "Generator interface" for the contract."""

from collections.abc import Callable

import networkx as nx

GENERATORS: dict[str, Callable[..., nx.Graph]] = {}


def register(name: str):
    """Decorator: add a generator to GENERATORS under `name` (also its G.graph["family"])."""

    def wrap(fn):
        if name in GENERATORS:
            raise ValueError(f"generator {name!r} registered twice")
        GENERATORS[name] = fn
        return fn

    return wrap
