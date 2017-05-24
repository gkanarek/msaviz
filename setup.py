# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 14:00:02 2017

@author: gkanarek

Used for installing the msaviz package via pip.
"""

from setuptools import setup, find_packages
from io import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

#read the requirements.txt
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    required = f.read().splitlines()


setup(
    name='msaviz',
    version='1.0.2a4',
    description='JWST-NIRSpec MSA spectral visualization tool',
    long_description=long_description,
    url='https://github.com/gkanarek/msaviz',
    author='Gray Kanarek',
    author_email='gkanarek@stsci.edu',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='JWST NIRSpec MSA spectrum visualization kivy',
    packages=find_packages(),
    install_requires=required,
    include_package_data=True,
    entry_points={
        'gui_scripts': [
            'msaviz=msaviz:run',
        ]
    },
)