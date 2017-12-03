#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from setuptools import setup


def _load_lines(filename):
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        return [l.strip() for l in f.readlines()]


setup(
    name="pyramid_oas3",
    version='0.0.1',
    description='Validator/Parser for Pyramid WebApp in OpenAPI 3.0',
    packages=["pyramid_oas3"],
    author="Kazuki Oikawa",
    author_email="k@oikw.org",
    license="MIT",
    url="http://github.com/kazuki/pyramid-oas3",
    install_requires=_load_lines('requirements.txt'),
    tests_requires=_load_lines('test-requirements.txt'),
    test_suite='nose2.collector.collector',
)
