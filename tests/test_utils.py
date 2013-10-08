#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import pytest
from perch.utils import ClassRegistry, files_in_dir

@pytest.fixture
def registry():
    return ClassRegistry()

@pytest.fixture
def filledregistry(registry):
    registry.register('test')(1)
    return registry

class TestClassRegistery(object):
    def test_registers_name_value(self, registry):
        registry.register('test')(1)

        assert registry == {'test': 1}

    def test_access_name(self, filledregistry):
        assert filledregistry['test'] == 1

    def test_get_name(self, filledregistry):
        assert filledregistry.get('test') == 1

@pytest.fixture(params=[
    tuple(),
    ('a.py',),
    ('a.py', 'x/a.py'),
    ('a.py', 'x/a.py', 'x/y/a.py'),
])
def dir_with_files(request, tmpdir):
    "get a directory with number of files in it"
    for f in request.param:
        tmpdir.join(f).ensure(file=True)

    return tmpdir

def test_files_in_dir(dir_with_files):
    assert list(files_in_dir(dir_with_files)) == \
           list(dir_with_files.visit(sort=True))
