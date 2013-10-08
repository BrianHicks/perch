#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import sys

from .config import constants
from .serializers import serializers


class StdIOHandler(object):
    "Provide common I/O handling to the command line"
    def __init__(self):
        self.config = json.loads(os.environ.get(constants.stage_env_var, '{}'))
        self.serializer = serializers.get(self.config.get(
            constants.serializer_key, constants.default_serializer
        ))()

    def get_configuration(self):
        return self.serializer.dump({
            'name': self.name,
            'input_tags': self.input_tags,
        })

    def run(self, args=None):
        command = (args or sys.argv)[-1]

        if command == 'config':
            sys.stdout.write(self.get_configuration() + '\n')

        elif command == 'process':
            for obj in self.process(sys.stdin):
                sys.stdout.write(self.serializer.dump(obj) + '\n')

        elif command == 'start':
            for obj in self.start():
                sys.stdout.write(self.serializer.dump(obj) + '\n')

        else:
            sys.stderr.write('Cannot do "%s"\n' % command)


class Converter(StdIOHandler):
    "Base class for converters"
    def process(self, in_file):
        "process the file supplied by the superclass"
        for line in in_file.readlines():
            parsed = self.parse(self.serializer.load(line))

            if parsed:
                yield parsed

        # some converters might want to output files after each file has been
        # processed - implement "final" to do that.
        try:
            for line in self.final():
                yield line
        except AttributeError:
            pass


class Filter(StdIOHandler):
    "base class for filters"
    def process(self, in_file):
        for line in in_file.readlines():
            if self.check(self.serializer.load(line)):
                yield line
