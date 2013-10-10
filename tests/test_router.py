#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import pytest

from perch.router import Graph, Stage

@pytest.fixture
def empty(tmpdir):
    return tmpdir

def content(name, intags, outtags):
    return """#!/bin/sh\n/bin/echo '%s' """ % json.dumps({
        'name': name,
        'input_tags': intags,
        'output_tags': outtags,
    })

@pytest.fixture(params=[
    # test single files
    (
        ('a.py', ('a', ('filesystem',), ('post',))),
    ),
    # test multiple files
    (
        ('a.py', ('a', ('filesystem',), ('post',))),
        ('b.py', ('a', ('post',), ('tag',))),
    ),
    # test files in directories
    (
        ('static/pngcrush.py', ('pngcrush', ('filesystem',), ('static',))),
        ('static/sass.py', ('sass', ('filesystem',), ('static',))),
    ),
    # test mixed
    (
        ('pngcrush.py', ('pngcrush', ('filesystem',), ('static',))),
        ('static/sass.py', ('sass', ('filesystem',), ('static',))),
    ),
])
def collectors(request, empty):
    for fname, fcontent in request.param:
        f = empty.join(fname)
        f.ensure()
        f.write(content(*fcontent))

    return empty, request.param


@pytest.mark.incremental
class TestGraph(object):
    def test_stages(self, collectors):
        tmpdir, files = collectors

        d = Graph(tmpdir)

        assert set(d._stages()) == set(tmpdir.join(f[0]) for f in files)

@pytest.mark.incremental
class TestStage(object):
    @pytest.mark.parametrize("fname,content,output", [
        ('test.py', '#!/usr/bin/env python', '/usr/bin/env python'),
        ('test.py', 'some content', 'python'),
        ('test.py', '', 'python'),
        ('test.rb', '', 'ruby'),
        ('test.js', '', 'node'),
        ('test.sh', '', 'bash'),
        ('test', '#!/usr/bin/env python', '/usr/bin/env python')
    ])
    def test_runner(self, tmpdir, fname, content, output):
        f = tmpdir.join(fname)
        f.write(content)

        stage = Stage(f)

        assert stage.runner() == output

    def test_runner_error(self, tmpdir):
        f = tmpdir.join('test.badext')
        f.write('')
        stage = Stage(f)

        with pytest.raises(ValueError) as exc:
            stage.runner()

        assert str(exc).endswith("I don't know how to handle .badext files!")
