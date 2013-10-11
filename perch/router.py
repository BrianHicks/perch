#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import namedtuple
from functools import wraps
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
    def __init__(self, directory):
        self.directory = directory

    def _stages(self):
        "find stages in a directory"
        return list(files_in_dir(self.directory))

    def _configurations(self):
        "find configurations for all stages"
        return {
            stage: {}
            for stage in self._stages()
        }
