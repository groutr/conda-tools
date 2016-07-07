"""
Utility functions that map information from caches onto environments
"""

import os

from config import config
from cache import PackageInfo
from environment import environments


def linked_environments(package, environments):
    """"
    Determine where package is linked to which environments
    :param package: PackageInfo
    :param environments: sequence of Environment
    :return: tuple(Environment)
    """
    linked_envs = (env for env in environments if package in set(env.linked_packages.values()))
    return tuple(linked_envs)


def all_linked_environments(packages, environments):
    """
    Return data structure that maps each package to all of its linked environments
    :param packages: sequence of PackageInfo
    :param environments: sequence of Environment
    :return: dict<PackageInfo:tuple(Environment)>
    """
    result = {p: linked_environments(p, environments) for p in packages}
    return result


def unlinked_packages(packages, environments):
    """
    Return a tuple of all packages that are not linked into any environments

    These packages should be safe to remove.
    :param packages: sequence of PackageInfo
    :param environments: sequeces of Environment
    :return:
    """
    linked = all_linked_environments(packages, environments)
    return tuple(pkg for pkg, env in linked.items() if not env)





