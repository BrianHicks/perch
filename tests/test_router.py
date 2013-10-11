#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import pytest
from textwrap import dedent

from perch.router import Graph, Stage
from perch.errors import BadRunner, BadExit

def content(name, intags, outtags):
    return """#!/bin/sh\n/bin/echo '%s' """ % json.dumps({
        'name': name,
        'input_tags': intags,
        'output_tags': outtags,
    })


class FakeStage(Stage):
    def __init__(self, n, i, o, *args, **kwargs):
        self.configuration = {
            'name': n,
            'input_tags': i,
            'output_tags': o,
        }
        super(FakeStage, self).__init__(*args, **kwargs)


@pytest.mark.incremental
class TestGraph(object):
    def test_stages(self, tmpdir):
        tmpdir
        files = [
            tmpdir.join(f) for f in
            ['a/b.py', 'c.py', 'd.py']
        ]
        for f in files:
            f.ensure(file=True)
            f.write('test')

        graph = Graph(tmpdir)
        stages = list(map(Stage, files))

        assert graph.stages == stages


@pytest.mark.incremental
class TestStage(object):
    @pytest.mark.parametrize("fname,content,output", [
        ('test.py', '#!/usr/bin/env python', '/usr/bin/env python'),
        ('test.py', 'some content', 'python'),
        ('test.py', '', 'python'),
        ('test.rb', '', 'ruby'),
        ('test.js', '', 'node'),
        ('test.sh', '', 'bash'),
        ('test.pl', '', 'perl'),
        ('test',    '', 'bash'),
        ('test',    '#!/usr/bin/env python', '/usr/bin/env python')
    ])
    def test_runner(self, tmpdir, fname, content, output):
        f = tmpdir.join(fname)
        f.write(content)

        stage = Stage(f)

        assert stage._runner() == output

    def test_run_config(self, tmpdir):
        f = tmpdir.join('test')
        f.write(content('a', ['x'], ['y']))

        # if this fails, it'll fail. yay.
        Stage(f).run('config')

    def test_run_bad_shebang(self, tmpdir):
        f = tmpdir.join('test')
        f.write('#!/usr/bin/some-bad-filename')

        with pytest.raises(BadRunner) as exc:
            Stage(f).run('config')

    def test_nonzero_exit_code(self, tmpdir):
        f = tmpdir.join('test.sh')
        f.write('exit 1')

        with pytest.raises(BadExit) as exc:
            Stage(f).run('config')

    def test_configuration(self, tmpdir):
        f = tmpdir.join('test')
        f.write(content('a', ['x'], ['y']))

        stage = Stage(f)

        assert stage.configuration == {
            'name': 'a',
            'input_tags': ['x'], 'output_tags': ['y']
        }

    def test_process(self, tmpdir):
        f = tmpdir.join('test.py')
        f.write(dedent('''
            from __future__ import print_function
            import sys
            
            for line in sys.stdin.readlines():
                print(line)
        '''))

        lines = [
            {'a': 'b'},
            {'b': 'c'},
            {'c': 'd'},
        ]

        stage = Stage(f)

        assert stage.process(lines) == lines

    def test_equality(self, tmpdir):
        f = tmpdir.join('test.py')
        f.ensure()

        assert Stage(f) == Stage(f)

    def test_inequality(self, tmpdir):
        f = tmpdir.join('test.py')
        f.ensure()

        g = tmpdir.join('test2.py')
        g.ensure()

        assert Stage(f) != Stage(g)

    def test_repr(self, tmpdir):
        f = tmpdir.join('test.py')
        f.ensure()

        assert repr(Stage(f)) == 'Stage(%r)' % f
