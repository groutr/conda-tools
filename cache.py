import json
import os
from functools import lru_cache
from os.path import join, exists

from config import config

class InvalidCachePackage(Exception):
    pass

@lru_cache()
class PackageInfo(object):
    def __init__(self, path):
        self.path = path
        self._info = join(path, 'info')
        if path == 'root' or exists(path) and exists(self._info):
            self._index = join(self._info, 'index.json')
            self._files = join(self._info, 'files')
        else:
            raise InvalidCachePackage("{} does not exist".format(self._info))

    @lru_cache(maxsize=1)
    def index(self):
        with open(self._index, 'r') as f:
            x = json.load(f)
        return x

    @property
    def name(self):
        return self.index()['name']

    @property
    def version(self):
        return self.index()['version']

    @lru_cache(maxsize=1)
    def files(self):
        with open(self._files, 'r') as f:
            x = map(str.strip, f.readlines())
        return set(x)

    def __eq__(self, other):
        if not isinstance(PackageInfo, other):
            return False

        if self.path == other.path:
            return True
        return False

    def __hash__(self):
        return hash(self.path)

    def __repr__(self):
        return 'PackageInfo({})'.format(self.path)

    def __str__(self):
        return '{}::{}'.format(self.name, self.version)


def load_cache(path, verbose=False):
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
    Return dictionary of cache with (package name, package version) mapped to cache entry.
    :param path: path to pkg cache
    :return: dict
    """
    return {(i.name, i.version): i for i in load_cache(path)}

