import json
import os
from os.path import join, exists

from .common import lazyproperty, lru_cache
from .config import config

class InvalidCachePackage(Exception):
    pass
    
class PackageInfo(object):
    def __init__(self, path):
        """
        Provide an interface to a cached package.

        A valid *path* should have an `info/` directory. 
        """
        self.path = path
        self._info = join(path, 'info')
        if exists(path) and exists(self._info):
            self._index = join(self._info, 'index.json')
            self._files = join(self._info, 'files')
        else:
            raise InvalidCachePackage("{} does not exist".format(self._info))
    
    @lru_cache(maxsize=16)
    def __getattr__(self, name):
        """
        Provide attribute access into PackageInfo.index

        If an attribute is not resolvable, return `None`.  
        Returning `None` makes possible comprehensions like for collecting a field across many instances.
        """
        if name in self.__dict__:
            return self.__dict__[name]
        elif name in self.index:
            return self.index[name]

    @lazyproperty
    def index(self):
        """
        Provide access to `info/index.json`.
        """
        with open(self._index, 'r') as f:
            x = json.load(f)
        return x

    @lazyproperty
    def files(self):
        """
        Provide access to `info/files`.  A frozenset of files is returned.
        """
        with open(self._files, 'r') as f:
            x = map(str.strip, f.readlines())
        return frozenset(x)

    @lazyproperty
    def full_spec(self):
        """
        Return full spec of package.
        """
        return '{}-{}-{}'.format(self.name, self.version, self.build)

    def __lt__(self, other):
        if isinstance(other, PackageInfo):
            return self.path < other.path

    def __eq__(self, other):
        if not isinstance(other, PackageInfo):
            return False

        return self.path == other.path

    def __hash__(self):
        return hash(self.path)

    def __repr__(self):
        return 'PackageInfo({}) @ {}'.format(self.path, hex(id(self)))

    def __str__(self):
        return self.full_spec


def packages(path, verbose=False):
    """
    Collect and return a sequence of PackageInfo instances that represent
    each extracted package in the package cache, *path*.
    """
    if not exists(path):
        raise IOError('{} cache does not exist!'.format(path))

    result = []
    cache = os.walk(path, topdown=True)
    root, dirs, files = next(cache)
    for d in dirs:
        try:
            result.append(PackageInfo(join(root, d)))
        except InvalidCachePackage:
            if verbose:
                print("Skipping {}".format(d))
            continue
    return tuple(result)

def named_cache(path):
    """
    Return dictionary of cache with `(package name, package version)` mapped to cache entry.
    This is a simple convenience wrapper around :py:func:`packages`.
    """
    return {(i.name, i.version): i for i in packages(path)}

