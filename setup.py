#!/usr/bin/env python

from setuptools import setup
from setuptools.extension import Extension

setup(name='VTOY',
    version='1.0',
    description='Virtualization on Your own',
    author='Tomas Hlavacek',
    author_email='tmshlvck@gmail.com',
    url='https://github.com/tmshlvck/vtoy',
    install_requires = [
        'flask',
        'jinja2', 
        'libvirt-python', 
#        'PyGObject',
        ],
    packages = ['vtoy',],
    scripts = [
        'scripts/list-assets.py', 'scripts/migrate.py',
        'scripts/virt-manager-conns.py',
        ],
   )

