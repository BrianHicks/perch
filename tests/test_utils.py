#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
from perch.utils import ClassRegistry

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
