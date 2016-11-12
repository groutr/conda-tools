"""
Utility functions that map information from caches onto environments
"""

import os
import hashlib

from .cache import correlated_cache
from .config import config



def _linked_environments(package, environments):
    """"
    Determine what package is linked to which environments

    This function is wrapped by :py:func:`linked_environments` to provide a consistent API.
    Please call :py:func:`linked_environments` instead.
    """
    linked_envs = (env for env in environments if package in set(env.linked_packages.values()))
    return tuple(linked_envs)


def linked_environments(packages, environments):
    """
    Return a dictionary that maps each package in *packages* to all of its linked environments
    """
    result = {p: _linked_environments(p, environments) for p in packages}
    return result


def unlinked_packages(packages, environments):
    """
    Return a tuple of all packages that are not linked into any environments

    These packages should be safe to remove.
    """
    linked = linked_environments(packages, environments)
    return tuple(pkg for pkg, env in linked.items() if not env)


def verify_hashes(packages, archives, hash_alg='md5'):
    """
    Loop through all given package objects and compare the hashes with hashes in package archive.

    Any hash that is supported by Python's hashlib can be used for comparison.

    In the interest of speed, files are iterated in the order they appear in the archive.?
    If they are large packages, they should be opened decompressed.

    packages and archives are assumed to zippable.
    Return a tuple of file hashes that do match.
    """
    def chunked(seq, size=1024):
        for block in iter(lambda: seq.read(size), b''):
            if block:
                yield block


    if hash_alg not in hashlib.algorithms_available:
        raise ValueError("{} hash algorithm not available in hashlib.".format(hash_alg))

    _new_hasher = lambda: hashlib.new(hash_alg)
    for pk, ar in zip(packages, archives):
        for tarinfo in ar:
            th, fh = _new_hasher(), _new_hasher()
            tfile = next(ar.extract(tarinfo, destination=None))
            
            fpath = os.path.join(pk.path, tarinfo.path)
            if not os.path.exists(fpath):
                return False

            for x in chunked(tfile):
                th.update(x)

            with open(fpath, 'rb') as fi:
                for x in chunked(fi):
                    fh.update(x)

            if th.digest() == fh.digest():
                continue
            else:
                print("Mismathed hash: {}".format(tarinfo.path))
                return False
    return True
             

            


    



