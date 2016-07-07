import subprocess as sp
import pytest
from os.path import join

from conda.config import root_dir
import environment as env

base_create = ('conda', 'create', '--yes', '--quiet', '-n')
base_destroy = ('conda', 'env', 'remove', '--yes', '--quet', '-n')
base_specs = ('python=3.5.1')
root_envs = join(root_dir, 'envs')

@pytest.fixture(scope='module')
def create_cttest1(request):
    sp.call(base_create + ('ct_test1', *base_specs))

    def destroy_cttest1():
        sp.call(base_destroy + ('ct_test1',))
    request.addfinalizer(destroy_cttest1) 


def test_instantiate(create_cttest1):
    e = env.Environment(join(root_envs, 'ct_test1'))
    assert e.path
    assert e._packages
    return e

def test_linked_packages(create_cttest1):
    x = test_instantiate(create_cttest1)   
    installed_pkgs = {'pip', 'python', 'setuptools',
        'ujson', 'vs2015_runtime', 'wget', 'wheel'}

    linked_packages = x.linked_packages
    assert set(linked_packages.keys()) == installed_pkgs
    
def test_link_types_all(create_cttest1):
    x = test_instantiate(create_cttest1)
    all_types = x._link_type_packages('all')

    assert isinstance(all_types, dict)
    assert 'hard-link' in all_types
    assert 'soft-link' in all_types
    assert 'copy' in all_types

    return all_types

def test_link_types_hard(create_cttest1):
    all_types = test_link_types_all(create_cttest1)
    x = test_instantiate(create_cttest1)

    assert x._link_type_packages('hard-link') == all_types['hard-link']

def test_link_types_soft(create_cttest1):
    all_types = test_link_types_all(create_cttest1)
    x = test_instantiate(create_cttest1)

    assert  x._link_type_packages('soft-link') == all_types['soft-link']

def test_link_types_copy(create_cttest1):
    all_types = test_link_types_all(create_cttest1)
    x = test_instantiate(create_cttest1)

    assert x._link_type_packages('copy') == all_types['copy']

def 

def test_environments(create_cttest1):
    result = env.environments(root_envs)
    assert isinstance(result, tuple)
    return result

def test_environments_root(create_cttest1):
    result = set(test_environments(create_cttest1))
    assert env.Environment(root_dir) in result

def test_environments_cttest1(create_cttest1):
    result = set(test_environments(create_cttest1))
    assert env.Environment(join(root_envs, 'ct_test1')) in result
    
def test_named_environments(create_cttest1):
    result = env.named_environments(root_envs)
    assert isinstance(result, dict)

        

