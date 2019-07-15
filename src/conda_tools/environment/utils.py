"""
Utility functions that map information from environments onto package cache
"""
from __future__ import print_function

from os.path import join

from .environment import Environment, environments
from ..cache.package import Package
from ..utils import is_hardlinked
from ..constants import LINK_TYPE


def check_hardlinked_env(env:Environment) -> dict:
    """
    Check all hardlinked packages in env
    """
    return {p.name: check_hardlinked_pkg(env, p.to_package()) for p in env.hard_linked}


def owns(env:Environment, path) -> tuple:
    """
    Return the package in env that owns file.

    This function will return all packages that claim the file. This
    shouldn't typically happen, and if it does, could mean the packages in the
    environment were incorrectly built.
    """
    return tuple(p for p in env.packages if path in p.files)


def check_hardlinked_pkg(env:Environment, Pkg:Package) -> list:
    """
    Check that pkg in cache is correctly (or completely) hardlinked into env.

    Returns a list of improperly hardlinked files.
    """
    bad_linked = []
    expected_linked = Pkg.files - Pkg.has_prefix.keys() - Pkg.no_link
    for f in expected_linked:
        src = join(Pkg.path, f)
        tgt = join(env.path, f)
        if not is_hardlinked(src, tgt):
            bad_linked.append(f)
    return bad_linked


def explicitly_installed(env:Environment) -> dict:
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
                       if x.get('action') in _ci}

    # See what packages were actually installed
    actually_installed = {date: set(pkg_spec) for date, pkg_spec in hist.construct_states}
    for date, specs in installed_specs.items():
        # Translate name only spec to full specs
        name_spec = {x for x in actually_installed[date] if x.split('-')[0] in specs}
        actually_installed[date] = name_spec

    # Intersect with currently installed packages
    actually_installed = {date: specs.intersection(current_pkgs) for date, specs in actually_installed.items()}
    return actually_installed

def orphaned(env:Environment) -> set:
    """
    Return a list of orphaned packages in the env.

    A package that has 0 packages depending on it will be considered orphaned.

    Since we don't have a full dependency solver, this method naively only
    considers package names (and ignores versions and version constraints).
    """
    depended_on = set()
    for pkg in env.packages:
        depended_on.update(d.split(maxsplit=1)[0] for d in pkg.depends)
    return set(p for p in env.packages if p.name not in depended_on)


def dependency_graph(env:Environment) -> dict:
    """
    Return a dictionary that represents the dependency graph of the environment.
    Only package names are considered because a package cannot have
    multiple versions of the same package installed.

    The output of this function can be passed to NetworkX constructors
    Args:
        env (Environment):

    Returns:
        (dict)
    """
    graph = {}

    for pkg in env.packages:
        graph[pkg.name] = deps = []
        for depended_on in pkg.depends:
            deps.append(depended_on.split(maxsplit=1)[0])
    return graph
