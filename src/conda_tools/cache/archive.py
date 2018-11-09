from os.path import realpath, normpath, join, exists
from pathlib import PurePath

import os
import hashlib
import bz2
import tempfile
import tarfile

from fnmatch import filter as fnfilter
from typing import NewType

from . import lazyproperty
from . import _types

from .exceptions import BadPathError, BadLinkError, InvalidCachePackage

PATH = _types.PATH

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

class PackageArchive(object):
    """
    A very thin wrapper around tarfile objects.

    A convenience class specifically tailored to conda archives.
    This class is intended for read-only access.
    """
    def __init__(self, path: PATH, decompress:bool=False):
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

        if isinstance(self._tarfile, tarfile.TarFile):
            self._tarfile.close()

            if self._decompressed and exists(self.path):
                os.remove(self.path)

    def _open(self, reopen:bool=False) -> None:
        """
        Open self.path on disk if not already open.

        If self.path is already open, then simply return.
        Reloading to file can be done by setting reopen=True.
        """
        _tarfile = self._tarfile
        if not reopen and isinstance(_tarfile, tarfile.TarFile) and not _tarfile.closed:
            # Checked first for lowest overhead possible
            return


        if _tarfile is None:
            self._tarfile = tarfile.open(self.path, mode='r')
        else:
            try:
                _tarfile.close()
                self._tarfile = tarfile.open(self.path, mode='r')
            except AttributeError:
                raise
            except OSError:
                raise

    def _decompress(self) -> None:
        if not self._decompressed:
            self._path = self.path
            self.path = _decompress_bz2(self._path)
            self._decompressed = True

    @lazyproperty
    def hash(self) -> str:
        h = hashlib.md5()
        blocksize = 16384

        path = getattr(self, '_path', self.path)
        with open(path, 'rb') as hin:
            for block in iter(lambda: hin.read(blocksize), b''):
                h.update(block)
        return h.hexdigest()

    def files(self) -> list:
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

def _decompress_bz2(filename: PATH, blocksize:int=900*1024) -> PATH:
    """
    Decompress .tar.bz2 to .tar on disk (for faster access)

    Use TemporaryFile to guarentee write access.
    """
    if not filename.endswith('.tar.bz2'):
        return filename

    fd, path = tempfile.mkstemp()
    with os.fdopen(fd, 'wb') as fo:
        with open(filename, 'rb') as fi:
            z = bz2.BZ2Decompressor()

            for block in iter(lambda: fi.read(blocksize), b''):
                fo.write(z.decompress(block))
    return path
