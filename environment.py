import os
import json
import pprint
from functools import lru_cache
from os.path import join, exists, basename

from cache import PackageInfo

class InvalidEnvironment(Exception):
    pass

@lru_cache()
class Environment(object):
    def __init__(self, path):
        self.path = path
        self._meta = join(path, 'conda-meta')
        if exists(path) and exists(self._meta):
            self._packages = load_all_json(self._meta)
        else:
            raise InvalidEnvironment('Unable to load environment {}'.format(path))

        # Load PackageInfo objects
        self.package_info = {}
        for i in self._packages.values():
            name = i['name']
            try:
                link_source = i.get('link').get('source')
            except AttributeError:
                link_source = 'root'
            self.package_info[name] = PackageInfo(link_source)
        self.name = basename(path)

    def packages(self):
        """
        Return a tuple of tuples (package, package version)
        """
        json_objs = self._packages.values()
        packages, versions = [], []
        for i in json_objs:
            packages.append(i['name'])
            versions.append(i['version'])

        return tuple(zip(packages, versions))

    def __eq__(self, other):
        if not isinstance(Environment, other):
            return False

        if self.path == other.path:
            return True
        return False

    def __hash__(self):
        return hash(self.path)

    def __repr__(self):
        return 'Environment({})'.format(self.path)

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
    root, dirs, files = next(os.walk(path, topdown=True))

    # root environment added first
    envs = [Environment(os.path.dirname(root))]
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
    :return: dict
    """
    return {e.name: e for e in environments(path)}

