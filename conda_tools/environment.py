from __future__ import print_function

import os
import json
import pprint
from operator import itemgetter
from os.path import join, isdir, basename, dirname

from .common import lazyproperty, lru_cache, intern_keys
from .cache import PackageInfo, Pool as PkgPool
from .history import History
from .compat import dvalues, ditems, reduce
from .constants import cast_link_type, LINK_TYPE
from .foreign import groupby

class InvalidEnvironment(Exception):
    pass


class DictionaryPool(object):
    """
    Store only unique dictionaries.

    Optional string interning can be enabled to as an extra memory optimization.
    """
    def __init__(self, intern_keys=False):
        self._pool = {}
        self._intern_keys = intern_keys

    def register(self, d):
        d_id = id(d)
        _pool = self._pool

        try:
            return _pool[d_id]
        except KeyError:
            # maybe a dict with same content in pool.
            for _d in dvalues(_pool):
                if d == _d:
                    return _d
            
            if self._intern_keys:
                d = intern_keys(d)
            self._pool[d_id] = d
            return d

    def clear(self):
        self._cache.clear()
            
Pool = DictionaryPool(intern_keys=True)

class Environment(object):
    def __init__(self, path):
        """
        Initialize an Environment object.  Many of the properties of this object
        are lazy, and are calculated on first access.
        To reflect changes in the underlying environment, a new Environment object should be created.
        """
        if not is_conda_env(path):
            raise InvalidEnvironment('Unable to load environment {}'.format(path))

        self._packages = {}
        self.path = path
        self._meta = join(path, 'conda-meta')
        self.name = basename(path)

        self.history = History(self.path)

    def _read_package_json(self):
        if not self._packages:
            self._packages = _load_all_json(self._meta)

    def activated(self):
        """
        Returns true if this environment instance is active.
        For non-root environments, this means that CONDA_PREFIX is defined in the environment. O(1)
        For root environments, PATH is search (O(n)).
        """
        conda_prefix = os.environ.get('CONDA_PREFIX', None)
        if conda_prefix is None:
            # we might be in the root environment.
            return self.path in os.environ['path'].split(os.pathsep)
        elif conda_prefix == self.path:
            return True
        return False

    def groupby(self, key):
        """
        Group packages by key.
        """
        self._read_package_json()
        return groupby(key, dvalues(self._packages))

    @lazyproperty
    def linked_packages(self):
        """
        List all packages linked into the environment.
        """
        package_info = {}
        for pi in dvalues(self._link_type_packages(link_type='all')):
            for p in pi:
                package_info[p.name] = p
        return package_info

    def get_field(self, field):
        self._read_package_json()
        return {i['name']: i.get(field) for i in dvalues(self._packages)}

    @lazyproperty
    def package_channels(self):
        """
        Mapping of packages to their channel sources.
        """
        self._read_package_json()
        result = {}
        for i in dvalues(self._packages):
            result[i['name']] = i.get('channel', '')
        return result

    @lazyproperty
    def package_specs(self):
        """
        List all package specs in the environment.
        """
        self._read_package_json()
        json_objs = dvalues(self._packages)
        specs = []
        for i in json_objs:
            p, v, b = i['name'], i['version'], i['build']
            specs.append('{}-{}-{}'.format(p, v, b))
        return tuple(specs)

    @property
    def hard_linked(self):
        return self._link_type_packages(LINK_TYPE.hardlink)
    
    @property
    def soft_linked(self):
        return self._link_type_packages(LINK_TYPE.softlink)

    @property
    def copy_linked(self):
        return self._link_type_packages(LINK_TYPE.copy)

    @property
    def packages(self):
        return tuple(reduce(tuple.__add__, dvalues(self._link_type_packages('all'))))

    @lru_cache(maxsize=4)
    def _link_type_packages(self, link_type='all'):
        """
        Return all PackageInfo objects that are linked into the environment.
        
        If *link_type=all*, then the dictionary returned is keyed by the type of linking
        """
        def _compat_link_type(link_type):
            if isinstance(link_type, int):
                return LINK_TYPE(link_type)
            else:
                return getattr(LINK_TYPE, link_type)
                
        self._read_package_json()

        result = {LINK_TYPE.hardlink: [], 
                  LINK_TYPE.softlink: [], 
                  LINK_TYPE.copy: []}
        for i in dvalues(self._packages):
            link = i.get('link')
            if link:
                ltype, lsource = cast_link_type(link['type']), link['source']
            else:
                ltype, lsource = LINK_TYPE.hardlink, self.path

            pkg_info = PkgPool.register(PackageInfo(lsource))
            result[ltype].append(pkg_info)

        if link_type == 'all':
            return {k: tuple(v) for k, v in ditems(result)}
        else:
            return tuple(result[link_type])

    def __lt__(self, other):
        if isinstance(other, Environment):
            return self.path < other.path

    def __eq__(self, other):
        if not isinstance(other, Environment):
            return False

        return self.path == other.path

    def __hash__(self):
        return hash(self.path)

    def __repr__(self):
        return 'Environment({}) @ {}'.format(self.path, hex(id(self)))

    def __str__(self):
        return 'Environment: {}'.format(self.name)


def update_values(d):
    """
    Map values in d forward across variations of file format

    Ex. link/type changed from string to enum in recent version of conda

    There should be a more elegant solution.  This is pretty hacked.
    """
    
    #update link/type values
    try:
        val = d['link']['type']
        d['link']['type'] = LINK_TYPE[val]
    except KeyError:
        pass

    return d


def _load_all_json(path):
    """
    Load all json files in a directory.  Return dictionary with filenames mapped to json dictionaries.
    """
    root, _, files = next(os.walk(path))
    result = {}
    for f in files:
        if f.endswith('.json'):
            result[f] = update_values(_load_json(join(root, f)))
    return result

def _load_json(path):
    with open(path, 'r') as fin:
        x = Pool.register(json.load(fin))
    return x

def is_conda_env(path):
    return isdir(path) and isdir(join(path, 'conda-meta'))

def environments(path, verbose=False):
    """
    Yield all environments under path.  If path is an environment, only path will be yielded.
    Otherwise, any subdirectories of path that are environments will be yielded.

    Returns a sequence of Environment objects created from *path*.
    """
    try:
        yield Environment(path)
    except InvalidEnvironment:
        root, dirs, files = next(os.walk(path, topdown=True))
        for d in dirs:
            try:
                yield Environment(join(root, d))
            except InvalidEnvironment:
                if verbose:
                    print("Ignoring {}".format(join(root, d)))
                continue


def named_environments(path):
    """
    Returns a dictionary of all environments keyed by environment name
    """
    return {e.name: e for e in environments(path)}

def active_environment():
    """
    Return the active environment.
    """
    try:
        prefix = os.environ['CONDA_PREFIX']
        return Environment(prefix)
    except KeyError:
        raise InvalidEnvironment("No environment seems to be currently active")