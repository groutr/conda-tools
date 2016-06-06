import json
import os
from functools import lru_cache


@lru_cache()
class PackageInfo(object):
    def __init__(self, path):
        self.path = path
        if os.path.exists(path):
            self._info = os.path.join(path, 'info')
            self._index = os.path.join(self._info, 'index.json')
            self._files = os.path.join(self._info, 'files')

    @lru_cache(maxsize=1)
    def index(self):
        with open(self._index, 'r') as f:
            x = json.load(f)
        return x

    @lru_cache(maxsize=1)
    def files(self):
        with open(self._files, 'r') as f:
            x = map(str.strip, f.readlines())
        return list(x)

    def __repr__(self):
        return 'PackageInfo({})'.format(self.path)

    def __str__(self):
        return '{}::{}'.format(self.index()['name'], self.index()['version'])


def load_cache(path):
    if not os.path.exists(path):
        raise IOError('{} cache does not exist!'.format(path))

    result = []
    cache = os.walk(path, topdown=True)
    root, dirs, files = next(cache)
    for d in dirs:
        result.append(PackageInfo(os.path.join(root, d)))
    return tuple(result)
