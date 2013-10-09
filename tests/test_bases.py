#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import pytest

from perch.bases import StdIOHandler, Collector, Filter, Renderer

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

@pytest.fixture
def stubbedconv():
    class Mangler(Collector):
        name = 'test'
        input_tags = ['a', 'b']

        def parse(self, msg):
            return {'msg': msg}

        def final(self):
            yield {'msg': 'finish'}

    return Mangler()

@pytest.fixture
def messages():
    return StringIO(
        '{"filename": "a.txt"}\n'
        '{"filename": "b.txt"}\n'
        '{"filename": "c.txt"}\n'
    )


@pytest.fixture
def bfilter():
    class BFilter(Filter):
        def check(self, obj):
            return 'b' in obj['filename']

    return BFilter()


@pytest.fixture
def renderer():
    class ARenderer(Renderer):
        def render(self, obj):
            return 'path/to/a.txt', 'test content'

    return ARenderer()


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


class TestCollector(object):
    def test_process_starts_with_parse(self, stubbedconv, messages):
        messages = stubbedconv.process(messages)

        for message, letter in zip(list(messages)[:-1], 'abc'):
            assert {'msg': {'filename': '%s.txt' % letter}} == message

    def test_process_ends_with_final(self, stubbedconv, messages):
        message = list(stubbedconv.process(messages))[-1]
        assert {'msg': 'finish'} == message

def test_filter(bfilter):
    xs = [
        (StringIO('{"filename": "a.txt"}'), 0),
        (StringIO('{"filename": "b.txt"}'), 1),
        (StringIO('{"filename": "c.txt"}'), 0),
    ]
    for message, items in xs:
        assert items == len(list(bfilter.process(message)))


def test_renderer(renderer, messages):
    for item in renderer.process(messages):
        assert item['filename'] == 'path/to/a.txt'
        assert item['content'] == 'test content'
