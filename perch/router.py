#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import namedtuple
from functools import wraps
from itertools import chain
import os
from shlex import split
from subprocess import Popen, PIPE

from .config import constants
from .serializers import serializers
from .utils import files_in_dir
from .errors import BadRunner, BadExit


class Stage(object):
    def __init__(self, pathfile):
        self.pathfile = pathfile
        self.serializer = serializers.get(
            constants.serializer_key, serializers[constants.default_serializer]
        )()

        self.runner = self._runner()

    def __eq__(self, other):
        return self.pathfile == other.pathfile

    def __hash__(self):
        return hash(self.pathfile)

    def __repr__(self):
        return 'Stage(%r)' % self.pathfile.basename

    runners = {
        '.py': 'python',
        '.rb': 'ruby',
        '.js': 'node',
        '.sh': 'bash',
        '.pl': 'perl',
    }

    def _runner(self):
        "get the runner for this instance"
        # first, look at the shebang
        try:
            shebang = self.pathfile.readlines()[0]
        except (IOError, IndexError):
            shebang = ''

        if shebang.startswith('#!'):
            return shebang[2:]

        # if that didn't work, guess from the extension
        return self.runners.get(self.pathfile.ext, self.runners['.sh'])

    def run(self, cmd, stdin=None, timeout=None):
        cmd = split(self.runner) + [str(self.pathfile)] + split(cmd)
        try:
            response = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        except OSError:
            raise BadRunner('No such file or directory: %s' % self.runner)

        stdout, stderr = response.communicate(stdin.encode('utf-8') if stdin else stdin)

        if response.returncode != 0:
            raise BadExit('Response code %s. Stdout:\n\n%s\n\nStderr:\n\n%s' % (
                response.returncode, stdout, stderr
            ))

        loaded = [
            self.serializer.load(line)
            for line in stdout.decode('utf-8').split('\n')
            if line
        ]

        return loaded, stderr, response.returncode

    @property
    def configuration(self):
        if not getattr(self, '_configuration', None):
            out, _, _ = self.run('config')
            self._configuration = out[0]

        return self._configuration

    def process(self, objs):
        lines = '\n'.join(
            self.serializer.dump(obj)
            for obj in objs
        )
        out, _, _ = self.run('process', lines)

        return out


class Graph(object):
    def __init__(self, directory, stages=None):
        self.directory = directory
        self.stages = stages if stages is not None else [
            Stage(f)
            for f in files_in_dir(self.directory)
        ]
        self.graph = self._build_graph()

    def __getitem__(self, name):
        for stage in self.stages:
            if stage.configuration['name'] == name:
                return stage

        raise KeyError('No stage "%s"' % name)


    def _build_graph(self):
        tags = chain.from_iterable(
            stage.configuration['output_tags'] + stage.configuration['input_tags']
            for stage in self.stages
        )

        return {
            name: set(
                stage for stage in self.stages
                if name in stage.configuration['input_tags']
            )
            for name in tags
        }

    def stages_for_tag(self, tag):
        return self.graph.get(tag, set())


class Coordinator(object):
    def __init__(self, graph):
        self.graph = graph

    def process_dir(self, directory):
        return self.process_files(files_in_dir(directory))

    def process_files(self, files):
        objs = [
            {'filename': f.strpath, 'tags': ['filesystem']}
            for f in files
        ]
        finalized = []

        while True:
            # get current content
            current = []
            for tag in set(chain.from_iterable(obj['tags'] for obj in objs)):
                current += chain.from_iterable(self.process_tag(tag, objs))

            # straing off the rendered files
            objs = []
            for obj in current:
                if 'rendered' in obj['tags']:
                    finalized.append(obj)
                else:
                    objs.append(obj)

            if not objs:
                break

        return finalized

    def process_tag(self, tag, objs):
        for stage in self.graph.stages_for_tag(tag):
            yield stage.process(objs)
