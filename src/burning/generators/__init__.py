"""Graph generators. Import each family module here so it registers itself, e.g.

    from burning.generators import spider  # noqa: F401
"""

from burning.generators import (  # noqa: F401
    barbell,
    centipede,
    dary_tree,
    path,
    small_world,
    spider,
    star,
)
from burning.generators.registry import GENERATORS, register

__all__ = ["GENERATORS", "register"]
