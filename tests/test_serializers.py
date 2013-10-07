#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import pytest

from perch.serializers import JSONSerializer

@pytest.fixture
def json():
    return JSONSerializer()

@pytest.fixture
def now():
    return datetime.now()


class TestJSONSerializer(object):
    def test_loads(self, json):
        assert json.load('[]') == []

    def test_dumps(self, json):
        assert json.dump([]) == '[]'

    def test_dumps_dates(self, json, now):
        assert json.dump({'date': now}) == '{"date": "%s"}' % now.isoformat()

    def test_loads_dates(self, json, now):
        assert json.load('{"date": "%s"}' % now.isoformat()) == {'date': now.isoformat()}
