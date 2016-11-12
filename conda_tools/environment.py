import os
import json
import pprint
from os.path import join, isdir, basename, dirname
from functools import reduce

from .common import lazyproperty, lru_cache
from .cache import PackageInfo
from .history import History

class InvalidEnvironment(Exception):
    pass

class Environment(object):
    def __init__(self, path):
        """
        Initialize an Environment object.  Many of the properties of this object
        are lazy, and are calculated on first access.
        To reflect changes in the underlying environment, a new Environment object should be created.
        """
        self.path = path
        self._meta = join(path, 'conda-meta')
        if isdir(path) and isdir(self._meta):
            self._packages = {}
        else:
            raise InvalidEnvironment('Unable to load environment {}'.format(path))

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


    @lazyproperty
    def linked_packages(self):
        """
        List all packages linked into the environment.
        """
        package_info = {}
        for pi in self._link_type_packages(link_type='all').values():
            for p in pi:
                package_info[p.name] = p
        return package_info

    @lazyproperty
    def package_channels(self):
        """
        Mapping of packages to their channel sources.
        """
        self._read_package_json()
        result = {}
        for i in self._packages.values():
            result[i['name']] = i.get('channel', '')
        return result

    @lazyproperty
    def package_specs(self):
        """
        List all package specs in the environment.
        """
        self._read_package_json()
        json_objs = self._packages.values()
        specs = []
        for i in json_objs:
            p, v, b = i['name'], i['version'], i['build']
            specs.append('{}-{}-{}'.format(p, v, b))
        return tuple(specs)

    @property
    def hard_linked(self):
        return self._link_type_packages('hard-link')
    
    @property
    def soft_linked(self):
        return self._link_type_packages('soft-link')

    @property
    def copy_linked(self):
        return self._link_type_packages('copy')

    @property
    def packages(self):
        return tuple(reduce(tuple.__add__, self._link_type_packages('all').values()))

    @lru_cache(maxsize=4)
    def _link_type_packages(self, link_type='all'):
        """
        Return all PackageInfo objects that are linked into the environment.
        
        If *link_type=all*, then the dictionary returned is keyed by the type of linking
        """
        self._read_package_json()
        if link_type not in {'hard-link', 'soft-link', 'copy', 'all'}:
            raise ValueError('link_type must be hard-link, soft-link, copy, or all')

        result = {'hard-link': [], 'soft-link': [], 'copy': []}
        for i in self._packages.values():
            link = i.get('link')
            if link:
                ltype, lsource = link['type'], link['source']
            else:
                ltype, lsource = 'hard-link', self.path
            result[ltype].append(PackageInfo(lsource))

        if link_type == 'all':
            return {k: tuple(v) for k, v in result.items()}
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

def _load_all_json(path):
    """
    Load all json files in a directory.  Return dictionary with filenames mapped to json dictionaries.
    """
    root, _, files = next(os.walk(path))
    result = {}
    for f in files:
        if f.endswith('.json'):
            result[f] = _load_json(join(root, f))
    return result

def _load_json(path):
    with open(path, 'r') as fin:
        x = json.load(fin)
    return x

def environments(path, verbose=False):
    """
    List all known environments, including root environment.

    Returns a sequence of Environment objects created from *path* plus the root environment.
    """
    root, dirs, files = next(os.walk(path, topdown=True))

    # root environment added first
    yield Environment(dirname(root))
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

def active_environment(path):
    """
    Return the active environment.
    """
    for x in environments(path):
        if x.activated():
            return x
