"""Graph generators. Import each family module here so it registers itself, e.g.

    from burning.generators import spider  # noqa: F401
"""

from burning.generators.registry import GENERATORS, register
from burning.generators import centipede, spider  # noqa: F401,E402

__all__ = ["GENERATORS", "register"]
