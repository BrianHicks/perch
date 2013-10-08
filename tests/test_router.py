#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from perch.router import Discoverer

@pytest.fixture
def empty(tmpdir):
    return tmpdir

@pytest.fixture(params=[
    'test_collector.py',
    'collectors/test.py'
])
def collectors(request, empty):
    empty.join(request.param).ensure()

    return empty, request.param


@pytest.mark.incremental
class TestDiscoverer(object):
    def test_find_stages(self, collectors):
        tmpdir, name = collectors

        d = Discoverer(tmpdir)
        d._find_stages()

        assert list(d._stages) == [tmpdir.join(name)]

    def test_classify_stages(self, collectors):
        tmpdir, name = collectors

        d = Discoverer(tmpdir)
        d._find_stages()
        d._classify_stages()

        assert d._classified == {"collector": set([tmpdir.join(name)]), 'filter': set(), 'renderer': set()}

    def test_discover(self, collectors):
        tmpdir, name = collectors
        
        d = Discoverer(tmpdir)
        assert d.discover() == {"collector": set([tmpdir.join(name)]), 'filter': set(), 'renderer': set()}
