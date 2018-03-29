from __future__ import print_function

import bz2
from json import loads
from os.path import join


from .compat import ditems, urlopen


PACKAGE_FIELDS = (
    'build', 'build_number', 'date', 'date', 'depends', 'requires',
    'license', 'license_family', 'md5', 'size', 'version', 'name'
)

class RepoPackage(object):
    __slots__ = ('filename',) + PACKAGE_FIELDS    
    def __init__(self, filename, info):
        self.filename = filename

        for field in PACKAGE_FIELDS:
            setattr(self, field, info.get(field))

        if hasattr(self, 'sha256'):
            self.hashfield = self.sha256
        else:
            self.hashfield = self.md5

    def __hash__(self):
        return hash(self.hashfield)

    def __eq__(self):
        return self.hashfield

    def __repr__(self):
        return 'RepoPackage({})'.format(self.filename)

    def __str__(self):
        return '{} {} {}'.format(self.name, self.version, self.build)


def repo_packages(d):
    return set(RepoPackage(*info) for info in ditems(d))

class Repository(object):
    def __init__(self, url, data):
        self.url = url
        self.subdir = data['info']['subdir']
        self.packages = repo_packages(data['packages'])

    def __repr__(self):
        return 'Repository({})'.format(self.url)

    def __eq__(self, other):
        try:
            return (self.url == other.url) and (self.packages == other.packages)
        except:
            return False

    def fetch_urls(self, pkgs):
        base_url = self.url
        for p in pkgs:
            if p in self.packages:
                yield base_url + p.filename, p.md5

def get_repo(url, platform=None):
    if platform is not None:
        ch_url = join(url, platform)
    else:
        ch_url = url

    x = urlopen(join(ch_url, 'repodata.json.bz2'))
    x = bz2.decompress(x.read())
    
    repo_json = loads(x.decode('utf8'))
    return Repository(ch_url, repo_json)

