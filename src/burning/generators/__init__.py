"""Graph generators. Import each family module here so it registers itself, e.g.

    from burning.generators import spider  # noqa: F401
"""

from burning.generators import (  # noqa: F401
    barbell,
    centipede,
    cluster,
    dary_tree,
    path,
    grid,
    scale_free,
    small_world,
    spider,
    star,
)
from burning.generators.registry import GENERATORS, register

__all__ = ["GENERATORS", "register"]
