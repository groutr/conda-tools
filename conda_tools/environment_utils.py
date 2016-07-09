"""
Utility functions that map information from environments onto package cache
"""

from os.path import join

import utils
from .environment import Environment, environments
from .cache import PackageInfo


def hard_linked(env):
    """
    Return all packages that are hard-linked into env
    :param env: Environment
    :return: dict<str:PackageInfo>
    """
    return {p.name: p for p in env._link_type_packages(link_type='hard-link')}

def check_hardlinked_env(env):
    """
    Check all hardlinked packages in env
    """
    return {k: check_hardlinked_pkg(env, v) for k, v in hard_linked(env).items()}


def check_hardlinked_pkg(env, Pkg):
    """
    Check that pkg in cache is correctly (ie completely) hardlinked into env.
    :param env: path to environments
    :param Pkg: PackageInfo object
    :return: list<str> list of bad hard links
    """

    bad_linked = []
    for f in Pkg.files:
        src = join(Pkg.path, f)
        tgt = join(env.path, f)
        if not utils.is_hardlinked(src, tgt):
            bad_linked.append(f)
    return bad_linked


def explicitly_installed(env):
    """
    Return list of explicitly installed packages.
    Note that this does not work with root environments
    """

    current_pkgs = set(environ.package_specs)
    
    hist = environ.history

    # Map date to explicitly installed package specs
    _ci = {'install', 'create'}
    installed_specs = {x['date']: set(t.split()[0] 
                        for t in x['specs']) 
                        for x in hist.get_user_requests 
                        if x['action'] in _ci}

    # See what packages were actually installed
    actually_installed = {date: set(pkg_spec) for date, pkg_spec in hist.construct_states}    
    for date, specs in installed_specs.items():
        # Translate name only spec to full specs
        name_spec = {x for x in actually_installed[date] if x.split('-')[0] in specs}
        actually_installed[date] = name_spec

    # Intersect with currently installed packages
    actually_installed = {date: specs.intersection(current_pkgs) for date, specs in actually_installed.items()}
    return actually_installed
    
        



