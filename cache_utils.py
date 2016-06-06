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
    linked_envs = (e for e in envs if package in set(envs.package_info.values()))
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
