from os.path import join, exists, isdir
import json
from functools import lru_cache
import pathlib
import typing
from sys import intern


from . import lazyproperty
from . import _types
from .exceptions import InvalidCachePackage

import tarfile


class PackagePool(object):
    """
    Common pool for sharing PackageInfo objects.
    """
    def __init__(self):
        self._pool = {}

    def register(self, pkg_obj):
        obj_hash = hash(pkg_obj)
        try:
            return self._pool[obj_hash]
        except KeyError:
            self._pool[obj_hash] = pkg_obj
            return pkg_obj

    def update(self, pkg_obj):
        self._pool[hash(pkg_obj)] = pkg_obj

    def clear(self):
        self._pool.clear()

Pool = PackagePool()

class Package:
    def __init__(self, path: _types.PATH):
        """
        Provide an interface to a cached package.

        A valid *path* should have an `info/` directory.
        """
        self.path = pathlib.Path(path)
        self._info = self.path/'info'

        self._index = self._info/'index.json'
        if not self._index.is_file():
            raise InvalidCachePackage("{} does not exist".format(self._index))

        self.binary_prefix = None
        self.text_prefix = None

    @lru_cache(maxsize=16)
    def __getattr__(self, name):
        """
        Provide attribute access into PackageInfo.index

        If an attribute is not resolvable, return `None`.
        Returning `None` makes possible comprehensions like for collecting a field across many instances.
        """
        if name in self.__dict__:
            return self.__dict__[name]
        elif name in self.index:
            return self.index[name]

    @lazyproperty
    def has_prefix(self):
        """
        Parse and return info/has_prefix
        """
        prefixed = {}
        binary_prefix = None
        text_prefix = None

        with (self._info/'has_prefix').open(mode='r') as f:
            for pf in f:
                prefix, ftype, fname = pf.split()
                if ftype == 'binary':
                    binary_prefix = prefix
                elif ftype == 'text':
                    text_prefix = prefix
                prefixed[fname] = ftype

        if binary_prefix:
            binary_prefix = intern(binary_prefix)
        if text_prefix:
            text_prefix = intern(text_prefix)
        self.binary_prefix = binary_prefix
        self.text_prefix = text_prefix
        return prefixed

    @lazyproperty
    def paths(self) -> typing.Mapping:
        """
        Return contents of info/paths.json
        """
        try:
            with (self._info/'paths.json').open(mode='r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    @lazyproperty
    def no_link(self) -> typing.AbstractSet:
        """
        Return contents of no_link
        """
        try:
            with (self._info/'no_link').open(mode='r') as f:
                return frozenset(x.strip() for x in f)
        except FileNotFoundError:
            return frozenset()

    @lazyproperty
    def index(self):
        """
        Provide access to `info/index.json`.
        """
        with self._index.open(mode='r') as f:
            return json.load(f)

    @lazyproperty
    def files(self) -> typing.AbstractSet:
        """
        Provide access to `info/files`.  A frozenset of files is returned.
        """
        with (self._info/'files').open(mode='r') as f:
            return frozenset(x.strip() for x in f)

    @lazyproperty
    def full_spec(self) -> str:
        """
        Return full spec of package.
        """
        return '{}-{}-{}'.format(self.name, self.version, self.build)

    def __iter__(self) -> typing.Iterator:
        """
        Return iterator over files in package
        """
        return iter(self.files)

    def __lt__(self, other):
        if other.__class__ == self.__class__:
            return self.path < other.path
        return NotImplemented

    def __eq__(self, other) -> bool:
        if other.__class__ is self.__class__:
            return self.path == other.path
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.path)

    def __repr__(self) -> str:
        return 'PackageInfo({}) @ {}'.format(self.path, hex(id(self)))

    def __str__(self) -> str:
        return self.full_spec
