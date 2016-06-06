import json
import os
from functools import lru_cache

class InvalidCachePackage(Exception):
    pass

@lru_cache()
class PackageInfo(object):
    def __init__(self, path):
        self.path = path
        self._info = os.path.join(path, 'info')
        if os.path.exists(path) and os.path.exists(self._info):
            self._index = os.path.join(self._info, 'index.json')
            self._files = os.path.join(self._info, 'files')
        else:
            raise InvalidCachePackage("{} does not exist".format(self._info))

    @lru_cache(maxsize=1)
    def index(self):
        with open(self._index, 'r') as f:
            x = json.load(f)
        return x

    @lru_cache(maxsize=1)
    def files(self):
        with open(self._files, 'r') as f:
            x = map(str.strip, f.readlines())
        return set(x)

    def __repr__(self):
        return 'PackageInfo({})'.format(self.path)

    def __str__(self):
        return '{}::{}'.format(self.index()['name'], self.index()['version'])


def load_cache(path, verbose=False):
    if not os.path.exists(path):
        raise IOError('{} cache does not exist!'.format(path))

    result = []
    cache = os.walk(path, topdown=True)
    root, dirs, files = next(cache)
    for d in dirs:
        try:
            result.append(PackageInfo(os.path.join(root, d)))
        except InvalidCachePackage:
            if verbose:
                print("Skipping {}".format(d))
    return tuple(result)


def named_cache(path):
    """
    Return dictionary of cache with (package name, package version) mapped to cache entry.
    :param path: path to pkg cache
    :return: dict
    """
    return {(i.index()['name'], i.index()['version']): i
            for i in load_cache(path)}
