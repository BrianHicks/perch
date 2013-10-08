#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from perch.bases import StdIOHandler, Converter

@pytest.fixture
def stubbedio():
    class Stubbed(StdIOHandler):
        name = 'test'
        input_tags = ['a', 'b']

        def process(self, infile):
            yield {'msg': 'a'}
            yield {'msg': 'b'}
            yield {'msg': 'c'}

        def start(self):
            yield {'msg': 'start'}

    return Stubbed()


class TestStdIOHandler(object):
    # helpers
    def serialize(self, sz, output):
        return '\n'.join([sz.dump(o) for o in output]) + '\n'

    # test get_configuration
    def test_get_configuration(self, stubbedio):
        assert stubbedio.get_configuration() == stubbedio.serializer.dump({
            'name': stubbedio.name,
            'input_tags': stubbedio.input_tags
        })

    # test run
    def test_config(self, stubbedio, capsys):
        stubbedio.run(['config'])
        out, err = capsys.readouterr()
        
        assert out == stubbedio.get_configuration() + '\n'

    def test_process(self, stubbedio, capsys):
        stubbedio.run(['process'])
        out, err = capsys.readouterr()

        assert out == self.serialize(stubbedio.serializer, stubbedio.process(None))

    def test_start(self, stubbedio, capsys):
        stubbedio.run(['start'])
        out, err = capsys.readouterr()

        assert out == self.serialize(stubbedio.serializer, stubbedio.start())

    def test_other(self, stubbedio, capsys):
        stubbedio.run(['blah'])
        out, err = capsys.readouterr()

        assert err == 'Cannot do "blah"\n'
