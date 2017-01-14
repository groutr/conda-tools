"""
Utility functions that map information from environments onto package cache
"""
from __future__ import print_function

from os.path import join

from .environment import Environment, environments
from .cache import PackageInfo
from .utils import is_hardlinked
from .compat import ditems


def hard_linked(env):
    """
    Return dictionary of all packages (as PackageInfo instances) that are hard-linked into *env*
    """
    return {p.name: p for p in env._link_type_packages(link_type='hard-link')}

def check_hardlinked_env(env):
    """
    Check all hardlinked packages in env
    """
    return {k: check_hardlinked_pkg(env, v) for k, v in ditems(hard_linked(env))}


def owns(env, path):
    """
    Return the package in env that owns file.

    This function will return all packages that claim the file. This
    shouldn't typically happen, and if it does, could mean the packages in the
    environment were incorrectly built.
    """
    return tuple(p for p in env.packages if path in p.files)


def check_hardlinked_pkg(env, Pkg):
    """
    Check that pkg in cache is correctly (or completely) hardlinked into env.

    Returns a list of improperly hardlinked files.
    """

    bad_linked = []
    for f in Pkg.files:
        src = join(Pkg.path, f)
        tgt = join(env.path, f)
        if not is_hardlinked(src, tgt):
            bad_linked.append(f)
    return bad_linked


def explicitly_installed(env):
    """
    Return list of explicitly installed packages.
    Note that this does not work with root environments
    """

    current_pkgs = set(env.package_specs)

    hist = env.history

    # Map date to explicitly installed package specs
    _ci = {'install', 'create'}
    installed_specs = {x['date']: set(t.split()[0]
                       for t in x['specs'])
                       for x in hist.get_user_requests
                       if x['action'] in _ci}

    # See what packages were actually installed
    actually_installed = {date: set(pkg_spec) for date, pkg_spec in hist.construct_states}
    for date, specs in ditems(installed_specs):
        # Translate name only spec to full specs
        name_spec = {x for x in actually_installed[date] if x.split('-')[0] in specs}
        actually_installed[date] = name_spec

    # Intersect with currently installed packages
    actually_installed = {date: specs.intersection(current_pkgs) for date, specs in ditems(actually_installed)}
    return actually_installed

def orphaned(env):
    """
    Return a list of orphaned packages in the env.

    A package that has 0 packages depending on it will be considered orphaned.

    Since we don't have a full dependency solver, this method naively only
    considers package names (and ignores versions and version constraints).
    """
    current_pkgs = set(env.packages)
    depended_on = set().union(pkg.depends for pkg in current_pkgs)
    return current_pkgs.difference(depended_on)



