#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from .config import constants
from .serializers import serializers
from .utils import files_in_dir
from functools import wraps
import shlex


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
        )

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
            return shlex.split(shebang[2:])

        # if that didn't work, guess from the extension
        try:
            return shlex.split(self.runners[self.pathfile.ext])
        except KeyError:
            raise ValueError(
                "I don't know how to handle %s files!" % self.pathfile.ext
            )

    # @attribute
    # @cache
    # def configuration(self):

    # def run(self, obj):



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
