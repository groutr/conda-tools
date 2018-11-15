import bz2
from json import loads
from os.path import join
from urllib.request import urlopen

from typing import Generator, Sequence

class RepoPackage:
    PACKAGE_FIELDS = (
    'build', 'build_number', 'date', 'depends', 'requires',
    'license', 'license_family', 'md5', 'size', 'version', 'name', 'sha256'
    )
    __slots__ = ('filename',) + PACKAGE_FIELDS

    def __init__(self, filename:str, info:dict):
        self.filename = filename

        for field in self.PACKAGE_FIELDS:
            setattr(self, field, info.get(field))

    def __hash__(self):
        return hash(self.sha256)

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            return self.sha256 == other.sha256
        return NotImplemented

    def __repr__(self):
        return 'RepoPackage({})'.format(self.filename)

    def __str__(self):
        return '{} {} {}'.format(self.name, self.version, self.build)


def repo_packages(d:dict) -> set:
    return set(RepoPackage(*info) for info in d.items())

class Repository:
    def __init__(self, url:str, data:dict):
        self.url = url
        self.info = data['info']
        self.packages = data['packages']

    def __repr__(self):
        return 'Repository({})'.format(self.url)

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return self.url == other.url and self.packages == other.packages
        return NotImplemented

    def fetch_urls(self, pkgs:Sequence) -> Generator:
        base_url = self.url
        for p in pkgs:
            if p in self.packages:
                yield join(base_url, p.filename), p.sha256


def get_repo(url:str, platform:str=None) -> Repository:
    if platform is not None:
        ch_url = join(url, platform)
    else:
        ch_url = url

    x = urlopen(join(ch_url, 'repodata.json.bz2'))
    x = bz2.decompress(x.read())

    repo_json = loads(x.decode('utf8'))
    return Repository(ch_url, repo_json)
