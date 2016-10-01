import tarfile
import json
import bz2
import os
from pathlib import PurePath
from os.path import realpath, normpath, join, splitext
from hashlib import md5


try:
    from collections.abc import Iterable
except ImportError:
    from collections import Iterable

from .common import lazyproperty

class BadLinkError(Exception):
    pass


class Package(object):
    """
    A very thin wrapper around tarfile objects.

    A convenience class specifically tailored to conda archives.
    This class is intended for read-only access.
    """
    def __init__(self, path, decompress=False):
        if decompress:
            self.path = _decompress_bz2(path)
        else:
            self.path = path
        self.decompressed = decompress
        self._tarfile = tarfile.open(self.path, mode='r')

    def __enter__(self):
        return self

    def __exit__ (self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self._tarfile.close()

        if self.decompressed:
            os.remove(self.path)
            
    @lazyproperty
    def hash(self):
        h = md5()
        blocksize = h.block_size

        with open(self.path, 'rb') as hin:
            h.update(hin.read(blocksize))
        return h.hexdigest()

    def files(self):
        return self._tarfile.getmembers()

    def extract(self, members, destination='.'):
        """
        Extract tarfile member to destination.  If destination is None, file is extracted into memory

        If sanitize_paths is True, then paths will be checked
        This method does some basic sanitation of the member.
        """
        if destination is None:
            for m in members:
                yield self._tarfile.extractfile(m)
        else:
            self._tarfile.extractall(path=destination, members=sane_members(members, destination))
        
def sane_members(members, destination):
    resolve = lambda path: realpath(normpath(join(destination, path)))

    destination = PurePath(destination)

    for member in members:
        mpath = PurePath(resolve(member.path))

        # Check if mpath is under destination
        if destination not in mpath.parents:
            raise BadPathError("Bad path to outside destination directory: {}".format(mpath))
        elif m.issym() or m.islnk():
            # Check link to make sure it resolves under destination
            lnkpath = PurePath(m.linkpath)
            if lnkpath.is_absolute() or lnkpath.is_reserved():
                raise BadLinkError("Bad link: {}".format(lnkpath))
            
            # resolve the link to an absolute path
            lnkpath = PurePath(resolve(lnkpath))
            if destination not in lnkpath.parents:
                raise BadLinkError("Bad link to outside destination directory: {}".format(cpath))
        
        yield member

def _decompress_bz2(filename, blocksize=900*1024):
    """
    Decompress .tar.bz2 to .tar on disk (for faster access)
    """
    if not filename.endswith('.tar.bz2'):
        return filename
    
    tar_ext = splitext(filename)[0] + ".tmp"
    with open(tar_ext, 'wb') as fo:
        with open(filename, 'rb') as fi:
            z = bz2.BZ2Decompressor()
            
            while True:
                block = fi.read(blocksize)
                if not block:
                    break
                fo.write(z.decompress(block))
    return tar_ext