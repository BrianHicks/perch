#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import pytest
from textwrap import dedent

from perch.errors import BadRunner, BadExit
from perch.router import Graph, Stage, Coordinator
from perch.utils import files_in_dir

def content(name, intags, outtags):
    return dedent("""
        #!/usr/bin/env python
        from __future__ import print_function
        import sys
        import json

        if sys.argv[-1] == "config":
            print('{doc}')

        if sys.argv[-1] == "process":
            for l in sys.stdin.readlines():
                obj = json.loads(l)
                obj['tags'] = {outtags}
                print(json.dumps(obj))
    """.format(
        doc=json.dumps({
            'name': name,
            'input_tags': intags,
            'output_tags': outtags,
        }),
        outtags=str(outtags)
    )).strip()

def makestage(tname, *content_args):
    "make a stage object given a temp name and content args"
    tname.ensure()
    tname.write(content(*content_args))

    s = Stage(tname)
    return s


@pytest.mark.incremental
class TestGraph(object):
    def test_stages(self, tmpdir):
        files = [
            makestage(tmpdir.join(f), f.rstrip('.py'), [], [])
            for f in ['a/b.py', 'c.py', 'd.py']
        ]

        graph = Graph(tmpdir)

        assert graph.stages == files

    def test_get_by_name(self, tmpdir):
        stage = makestage(tmpdir.join('a.py'), 'a', [], [])
        g = Graph(None, [stage])

        assert g['a'] == stage

    def test_get_by_name_fail(self):
        with pytest.raises(KeyError):
            Graph(None, [])['a']


    def test_build_graph_single_chain(self, tmpdir):
        a = makestage(tmpdir.join('a.py'), 'a', ['f'], ['a'])
        b = makestage(tmpdir.join('b.py'), 'b', ['a'], ['b'])

        assert Graph(tmpdir).graph == {
            'f': set([a]),
            'a': set([b]),
            'b': set(),
        }

    def test_build_graph_multiple_chain(self, tmpdir):
        a = makestage(tmpdir.join('a.py'), 'a', ['f'], ['a'])
        b = makestage(tmpdir.join('b.py'), 'b', ['a'], ['b'])
        c = makestage(tmpdir.join('c.py'), 'c', ['a'], ['c'])

        assert Graph(tmpdir).graph == {
            'f': set([a]),
            'a': set([b, c]),
            'b': set(),
            'c': set(),
        }

    def test_build_graph_with_empty(self, tmpdir):
        makestage(tmpdir.join('a.py'), 'a', [], [])
        assert Graph(tmpdir).graph == {}

    def test_build_input_empty(self, tmpdir):
        makestage(tmpdir.join('a.py'), 'a', [], ['b'])
        assert Graph(tmpdir).graph == {'b': set()}

    def test_build_output_empty(self, tmpdir):
        a = makestage(tmpdir.join('a.py'), 'a', ['a'], [])
        assert Graph(tmpdir).graph == {
            'a': set([a]),
        }

    def test_stages_for_tag_present(self, tmpdir):
        a = makestage(tmpdir.join('a.py'), 'a', ['a'], [])
        assert Graph(tmpdir).stages_for_tag('a') == set([a])

    def test_stages_for_tag_absent(self, tmpdir):
        assert Graph(tmpdir).stages_for_tag('a') == set()


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
        makestage(tmpdir.join('test'), 'a', ['x'], ['y']).run('config')

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

        assert repr(Stage(f)) == 'Stage(%r)' % f.basename


@pytest.fixture
def filled_coordinator(tmpdir):
    post = makestage(tmpdir.join('post.py'), 'post', ['filesystem'], ['post'])
    archive = makestage(tmpdir.join('archive.py'), 'archive', ['post'], ['archive'])
    jinja = makestage(tmpdir.join('jinja.py'), 'jinja', ['post', 'archive'], ['rendered'])

    return Coordinator(Graph(tmpdir))

@pytest.fixture
def some_content(tmpdir):
    cdir = tmpdir.join('content')
    cdir.join('x.md').ensure()
    cdir.join('y.md').ensure()

    return cdir


@pytest.mark.incremental
class TestCoordinator(object):
    def test_process_tag_present(self, filled_coordinator):
        processed = filled_coordinator.process_tag('archive', [{'tags': ['post']}])
        assert [[{'tags': ['rendered']}]] == list(processed)

    def test_process_tag_absent(self, filled_coordinator):
        processed = filled_coordinator.process_tag('asdf', [{'tags': ['post']}])
        assert [] == list(processed)

    def test_process_files(self, filled_coordinator, some_content):
        processed = filled_coordinator.process_files(files_in_dir(some_content))
        should = [
            {'filename': some_content.join('y.md').strpath, 'tags': ['rendered']},
            {'filename': some_content.join('y.md').strpath, 'tags': ['rendered']},
            {'filename': some_content.join('x.md').strpath, 'tags': ['rendered']},
            {'filename': some_content.join('x.md').strpath, 'tags': ['rendered']},
        ]

        for item in should:
            assert item in processed

    def test_process_dir(self, filled_coordinator, some_content):
        processed = filled_coordinator.process_dir(some_content)
        should = [
            {'filename': some_content.join('y.md').strpath, 'tags': ['rendered']},
            {'filename': some_content.join('y.md').strpath, 'tags': ['rendered']},
            {'filename': some_content.join('x.md').strpath, 'tags': ['rendered']},
            {'filename': some_content.join('x.md').strpath, 'tags': ['rendered']},
        ]

        for item in should:
            assert item in processed
