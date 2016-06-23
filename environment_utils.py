"""
Utility functions that map information from environments onto package cache
"""

from environment import Environment, environments


def packages_in_cache(env):
    """
    Determine whether a linked package in an environment still exists in cache.
    :param package: PackageInfo
    :return: bool
    """

    packages = env._packages


def hard_linked(env):
    """
    Return all packages that are hard-linked into env
    :param env:
    :return:
    """
    environ = Environment(env)
    return environ._link_type_packages(link_type='hard-link')


def explicitly_installed(env):
    environ = Environment(env)
    current_pkgs = set(environ.package_specs)
    
    hist = environ.history

    # Map date to explicitly installed package specs
    _ci = {'install', 'create'}
    installed_specs = {x['date']: set(t.split()[0] for t in x['specs']) for x in hist.get_user_requests if x['action'] in _ci}

    # See what packages were actually installed
    actually_installed = {date: set(pkg_spec) for date, pkg_spec in hist.construct_states}    
    for date, specs in installed_specs.items():
        # Translate name only spec to full specs
        name_spec = {x for x in actually_installed[date] if x.split('-')[0] in specs}
        actually_installed[date] = name_spec

    # Intersect with currently installed packages
    actually_installed = {date: specs.intersection(current_pkgs) for date, specs in actually_installed.items()}
    return actually_installed
        



