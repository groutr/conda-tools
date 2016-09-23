import tarfile
import json
from pathlib import PurePath, PureWindowsPat
from os.path import realpath, abspath, join
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
    def __init__(self, path):
        self.path = path
        self.mode = mode
        self._tarfile = tarfile.open(path, mode='r')

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
        Extract tarfile member to destination.

        This method does some basic sanitation of the member.
        """
        self._tarfile.extractall(path=destination, members=sane_members(members))

        
def sane_members(members):
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