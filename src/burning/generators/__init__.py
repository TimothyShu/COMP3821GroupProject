"""Graph generators. Import each family module here so it registers itself, e.g.

    from burning.generators import spider  # noqa: F401
"""

from burning.generators import barbell, dary_tree, small_world  # noqa: F401
from burning.generators.registry import GENERATORS, register

__all__ = ["GENERATORS", "register"]
