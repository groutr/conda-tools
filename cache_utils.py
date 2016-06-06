"""
Utility functions that map information from caches onto environments
"""

import os
from functools import partial

from config import config
from cache import PackageInfo, load_cache
from environment import environments


def linked_environments(package, env_path):
    envs = environments(env_path)
    linked_envs = (env for env in envs if package in set(env.package_info.values()))
    return tuple(linked_envs)


def all_linked_environments(cache_path, env_path):
    """
    Return data structure that maps each package to all of its linked environments
    :param env_path:
    :return:
    """
    pkgs = load_cache(cache_path)
    result = {}
    for p in pkgs:
        result[p] = linked_environments(p, env_path)

    return result


def unlinked_packages(cache_path, env_path):
    """
    Return a tuple of all packages that are not linked into any environments

    These packages should be safe to remove.
    :param cache_path:
    :param env_path:
    :return:
    """
    linked = all_linked_environments(cache_path, env_path)
    return tuple(pkg for pkg, env in linked.items() if not env)




