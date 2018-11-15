from setuptools import find_packages
from setuptools import setup

import os
import glob

setup(name='conda_tools',
    version='0.1',
    description='Useful abstractions of conda environments and package cache',
    author='Ryan Grout',
    author_email='ryan@ryangrout.org',
    url='https://github.com/groutr/conda-tools',
    packages=find_packages('src'),
    package_dir={'':'src'},
    zip_safe=False      
)
