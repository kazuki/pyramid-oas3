#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from setuptools import setup


def _load_lines(filename):
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        return [l.strip() for l in f.readlines()]


setup(
    name='pyramid_oas3',
    version='0.1.5',
    description='OpenAPI 3.0 Validator for Pyramid',
    packages=['pyramid_oas3', 'pyramid_oas3.jsonschema'],
    author='Kazuki Oikawa',
    author_email='k@oikw.org',
    license='MIT',
    url='http://github.com/kazuki/pyramid-oas3',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=_load_lines('requirements.txt'),
    tests_requires=_load_lines('test-requirements.txt'),
    test_suite='nose2.collector.collector',
)
