import os
import json
import pprint
from functools import lru_cache

from cache import PackageInfo

@lru_cache()
class Environment(object):
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        if os.path.exists(path):
            self._meta = os.path.join(path, 'conda-meta')
            self._packages = load_all_json(self._meta)

            # Load PackageInfo objects
            self.package_info = {}
            for i in self._packages.values():
                name = i['name']
                link_source = i.get('link').get('source')
                self.package_info[name] = PackageInfo(link_source)

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

