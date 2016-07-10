"""
Utility functions that map information from caches onto environments
"""

import os

from .config import config
from .cache import PackageInfo
from .environment import environments


def _linked_environments(package, environments):
    """"
    Determine where package is linked to which environments

    This function is wrapped by :py:func:`linked_environments` to provide a consistent API.
    Please call :py:func:`linked_environments` instead.
    """
    linked_envs = (env for env in environments if package in set(env.linked_packages.values()))
    return tuple(linked_envs)


def linked_environments(packages, environments):
    """
    Return a dictionary that maps each package in *packages* to all of its linked environments
    """
    result = {p: linked_environments(p, environments) for p in packages}
    return result


def unlinked_packages(packages, environments):
    """
    Return a tuple of all packages that are not linked into any environments

    These packages should be safe to remove.
    """
    linked = all_linked_environments(packages, environments)
    return tuple(pkg for pkg, env in linked.items() if not env)





