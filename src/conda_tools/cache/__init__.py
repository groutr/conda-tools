import os

from ..common import lazyproperty
from .. import _types

def init_cache(prefix: _types.PATH, name: str, mode: int=0o777) -> None:
    os.mkdir(os.path.join(prefix, name), mode)
