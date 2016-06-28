import os
import json
import pprint
from functools import lru_cache
from os.path import join, exists, basename, dirname

from common import lazyproperty
from cache import PackageInfo
from history import History

class InvalidEnvironment(Exception):
    pass



class Environment(object):
    """
    Represent a conda environment and information pertaining to it.
    """
    def __init__(self, path):
        """
        Initialize an Environment object.  Many of the properties of this object
        are lazy, and are calculated on first access.
        To reflect changes in the underlying environment, a new Environment object should be created.
        :param path: (str) path to environment folder
        """
        self.path = path
        self._meta = join(path, 'conda-meta')
        if exists(path) and exists(self._meta):
            self._packages = load_all_json(self._meta)
        else:
            raise InvalidEnvironment('Unable to load environment {}'.format(path))

        self.name = basename(path)

        self.history = History(self.path)

    @lazyproperty
    def linked_packages(self):
        """
        List all packages linked into the environment.
        :return: (dict<str:PackageInfo>) package name: PackageInfo
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
        :return: (dict<str:str>) package name: channel url
        """
        result = {}
        for i in self._packages.values():
            result[i['name']] = i.get('channel', '')
        return result

    @lazyproperty
    def package_specs(self):
        """
        List all package specs in the environment.
        :return: (tuple) package names and their versions
        """
        json_objs = self._packages.values()
        specs = []
        for i in json_objs:
            p, v, b = i['name'], i['version'], i['build']
            specs.append('{}-{}-{}'.format(p, v, b))
        return tuple(specs)

    @lru_cache(maxsize=4)
    def _link_type_packages(self, link_type='all'):
        """
        Return all PackageInfo objects that are linked into the environment
        :return: (dict<str:tuple>, tuple) PackageInfo objects organized by link type
        """
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

    def __eq__(self, other):
        if not isinstance(other, Environment):
            return False

        if self.path == other.path:
            return True
        return False

    def __hash__(self):
        return hash(self.path)

    def __repr__(self):
        return 'Environment({}) @ {}'.format(self.path, hex(id(self)))

    def __str__(self):
        return 'Environment: {}\n{}'.format(self.name,
                                              pprint.pformat(self.packages(), indent=4, compact=True))


def load_all_json(path):
    """
    Load all json files in a directory.  Return dictionary with filenames mapped to json dictionaries.
    """
    root, _, files = next(os.walk(path))
    result = {}
    for f in files:
        if f.endswith('.json'):
            with open(os.path.join(root, f), 'r') as fin:
                x = json.load(fin)
            result[f] = x
    return result


def environments(path, verbose=False):
    """
    List all known environments, including root environment.
    :param path: (str) path to directory of environments
    :param verbose: (bool) show verbose output
    :return: (tuple) Environments
    """
    root, dirs, files = next(os.walk(path, topdown=True))

    # root environment added first
    envs = [Environment(dirname(root))]
    for d in dirs:
        try:
            envs.append(Environment(join(root, d)))
        except InvalidEnvironment:
            if verbose:
                print("Ignoring {}".format(join(root, d)))
            continue

    return tuple(envs)


def named_environments(path):
    """
    Returns a dictionary of all environments keyed by environment name
    :param path: path to environments directory
    :return: (dict<str:Environment>)
    """
    return {e.name: e for e in environments(path)}

