import json
import os
import bz2
from tarfile import (open as topen, TarFile, is_tarfile)
from os.path import (join, exists, isdir, realpath, normpath, split)
from tempfile import mkstemp
from pathlib import PurePath
from hashlib import md5

from .common import lazyproperty, lru_cache
from .config import config

class InvalidCachePackage(Exception):
    pass

class BadLinkError(Exception):
    """
    Error raised when a symbolic link is bad.

    Can also arise when the link is possibly malicious.
    """
    pass

class BadPathError(Exception):
    pass

class PackageInfo(object):
    def __init__(self, path):
        """
        Provide an interface to a cached package.

        A valid *path* should have an `info/` directory.
        """
        self.path = path
        self._info = join(path, 'info')
        if isdir(path) and isdir(self._info):
            self._index = join(self._info, 'index.json')
            self._files = join(self._info, 'files')
        else:
            raise InvalidCachePackage("{} does not exist".format(self._info))

        

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
    def index(self):
        """
        Provide access to `info/index.json`.
        """
        with open(self._index, 'r') as f:
            x = json.load(f)
        return x

    @lazyproperty
    def files(self):
        """
        Provide access to `info/files`.  A frozenset of files is returned.
        """
        with open(self._files, 'r') as f:
            x = map(str.strip, f.readlines())
        return frozenset(x)

    @lazyproperty
    def full_spec(self):
        """
        Return full spec of package.
        """
        return '{}-{}-{}'.format(self.name, self.version, self.build)

    def __iter__(self):
        """
        Return iterator over files in package
        """
        return iter(self.files)

    def __lt__(self, other):
        if isinstance(other, PackageInfo):
            return self.path < other.path

    def __eq__(self, other):
        if not isinstance(other, PackageInfo):
            return False

        return self.path == other.path

    def __hash__(self):
        return hash(self.path)

    def __repr__(self):
        return 'PackageInfo({}) @ {}'.format(self.path, hex(id(self)))

    def __str__(self):
        return self.full_spec


def packages(path, verbose=False):
    """
    Collect and return a sequence of PackageInfo instances that represent
    each extracted package in the package cache, *path*.
    """
    if not isdir(path):
        raise IOError('{} cache should be a directory path!'.format(path))

    cache = os.walk(path, topdown=True)
    root, dirs, _ = next(cache)
    for d in dirs:
        try:
            yield PackageInfo(join(root, d))
        except InvalidCachePackage:
            if verbose:
                print("Skipping {}".format(d))
            continue

def named_cache(path):
    """
    Return dictionary of cache with `(package name, package version)` mapped to cache entry.
    This is a simple convenience wrapper around :py:func:`packages`.
    """
    return {split(x.path)[1]: x for x in packages(path)}


class PackageArchive(object):
    """
    A very thin wrapper around tarfile objects.

    A convenience class specifically tailored to conda archives.
    This class is intended for read-only access.
    """
    def __init__(self, path, decompress=False):
        """
        Represent a package archive in the global package cache.

        Setting decompress=True can result in significant performance gains,
        especially if working with many files inside the archive.
        Performance gains can be as much as 10000%.

        """
        self._decompressed = False
        self._tarfile = None

        if exists(path):
            self.path = path
        else:
            raise InvalidCachePackage("{} does not exist.".format(path))

        if decompress:
            self._decompress()


    def __del__(self):
        self.close()

    def __enter__(self):
        self._open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """
        Close an open archive and clean up possible temporary file.
        """

        if isinstance(self._tarfile, TarFile):
            self._tarfile.close()

            if self._decompressed and exists(self.path):
                os.remove(self.path)

    def _open(self, reopen=False):
        """
        Open self.path on disk if not already open.

        If self.path is already open, then simply return.
        Reloading to file can be done by setting reopen=True.
        """
        _tarfile = self._tarfile
        if not reopen and isinstance(_tarfile, TarFile) and not _tarfile.closed:
            # Checked first for lowest overhead possible
            return
        

        if _tarfile is None:
            self._tarfile = topen(self.path, mode='r')
        else:
            try:
                _tarfile.close()
                self._tarfile = topen(self.path, mode='r')
            except AttributeError:
                raise
            except OSError:
                raise

    def _decompress(self):
        if not self._decompressed:
            self._path = self.path
            self.path = _decompress_bz2(self._path)
            self._decompressed = True

    @lazyproperty
    def hash(self):
        h = md5()
        blocksize = 16384

        path = getattr(self, '_path', self.path)
        with open(path, 'rb') as hin:
            for block in iter(lambda: hin.read(blocksize), b''):
                h.update(block)
        return h.hexdigest()

    def files(self):
        self._open()
        return self._tarfile.getmembers()

    def recipe(self):
        """
        Return the members that pertain to the info/recipe directory
        """
        return tuple(x for x in self.info() if x.path.startswith('info/recipe/'))

    def info(self):
        """
        Return TarInfo objects for info/* directory
        """
        return tuple(x for x in self.files() if x.path.startswith('info/'))

    def __iter__(self):
        self._open()
        return iter(self._tarfile)

    def get_member(self, pattern):
        """
        Return the member(s) that match with pattern, otherwise None.
        """
        _files = {m.path: m for m in self.files()}
        return tuple(_files[m] for m in fnfilter(_files.keys(), pattern))

    def extract(self, members, destination='.'):
        """
        Extract tarfile member to destination.  If destination is None, file is extracted into memory

        If sanitize_paths is True, then paths will be checked
        This method does some basic sanitation of the member.
        """
        self._open()
        if not isinstance(members, (set, list, tuple)):
            members = (members,)

        if destination is None:
            for m in members:
                yield self._tarfile.extractfile(m)
        else:
            self._tarfile.extractall(path=destination, members=sane_members(members, destination))

    def __repr__(self):
        return 'PackageArchive({}) @ {}'.format(self.path, hex(id(self)))

    def __str__(self):
        return self.path


def sane_members(members, destination):
    resolve = lambda path: realpath(normpath(join(destination, path)))

    destination = PurePath(destination)

    for member in members:
        mpath = PurePath(resolve(member.path))

        # Check if mpath is under destination
        if destination not in mpath.parents:
            raise BadPathError("Bad path to outside destination directory: {}".format(mpath))
        elif member.issym() or member.islnk():
            # Check link to make sure it resolves under destination
            lnkpath = PurePath(member.linkpath)
            if lnkpath.is_absolute() or lnkpath.is_reserved():
                raise BadLinkError("Bad link: {}".format(lnkpath))

            # resolve the link to an absolute path
            lnkpath = PurePath(resolve(lnkpath))
            if destination not in lnkpath.parents:
                raise BadLinkError("Bad link to outside destination directory: {}".format(lnkpath))

        yield member

def _decompress_bz2(filename, blocksize=900*1024):
    """
    Decompress .tar.bz2 to .tar on disk (for faster access)

    Use TemporaryFile to guarentee write access.
    """
    if not filename.endswith('.tar.bz2'):
        return filename

    fd, path = mkstemp()
    with os.fdopen(fd, 'wb') as fo:
        with open(filename, 'rb') as fi:
            z = bz2.BZ2Decompressor()

            for block in iter(lambda: fi.read(blocksize), b''):
                fo.write(z.decompress(block))
    return path

def archives(path):
    """
    Return a tuple of package archives
    """
    if not isdir(path):
        raise IOError('{} cache should be a directory path!'.format(path))

    cache = os.walk(path, topdown=True)
    root, _, files = next(cache)
    for f in files:
        try:
            if f.endswith('.tar.bz2'):
                yield PackageArchive(join(root, f))
        except InvalidCachePackage:
            continue

def named_archives(path):
    return {split(x.path)[1]: x for x in archives(path)}

def correlated_cache(path):
    dirs = named_cache(path)
    ar = named_archives(path)
    result = {}
    for d, obj in dirs.items():
        try:
            result[d] = (obj, ar[d+'.tar.bz2'])
        except KeyError:
            continue
    return result
