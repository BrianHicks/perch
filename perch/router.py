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


def cache(func):
    @wraps(func)
    def inner(self):
        cache_name = '__' + func.__name__ + '_cache'

        if not getattr(self, cache_name, None):
            setattr(self, cache_name, func(self))

        return getattr(self, cache_name)

    return inner


class Stage(object):
    def __init__(self, pathfile):
        self.pathfile = pathfile
        self.serializer = serializers.get(
            constants.serializer_key, serializers[constants.default_serializer]
        )()

    runners = {
        '.py': 'python',
        '.rb': 'ruby',
        '.js': 'node',
        '.sh': 'bash',
    }

    @cache
    def runner(self):
        "get the runner for this instance"
        # first, look at the shebang
        try:
            shebang = self.pathfile.readlines()[0]
        except (IOError, IndexError):
            shebang = ''

        if shebang.startswith('#!'):
            return shebang[2:]

        # if that didn't work, guess from the extension
        try:
            return self.runners[self.pathfile.ext]
        except KeyError:
            raise ValueError(
                "I don't know how to handle %s files!" % self.pathfile.ext
            )

    def run(self, cmd, stdin=None, timeout=None):
        try:
            response = Popen(
                split(self.runner()) + [str(self.pathfile)] + split(cmd),
                stdin=PIPE, stdout=PIPE, stderr=PIPE
            )
        except OSError:
            raise BadRunner('No such file or directory: %s' % self.runner())

        stdout, stderr = response.communicate(stdin)

        if response.returncode != 0:
            raise BadExit('Response code %s. Stdout:\n\n%s\n\nStderr:\n\n%s' % (
                response.returncode, stdout, stderr
            ))

        loaded = [
            self.serializer.load(line)
            for line in stdout.strip().split('\n')
            if line
        ]

        return loaded, stderr, response.returncode

    @cache
    def configuration(self):
        out, _, _ = self.run('config')
        return out[0]

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

    @cache
    def _stages(self):
        "find stages in a directory"
        return list(files_in_dir(self.directory))

    @cache
    def _configurations(self):
        "find configurations for all stages"
        return {
            stage: {}
            for stage in self._stages()
        }
