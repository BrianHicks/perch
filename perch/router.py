#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from .config import constants
from .serializers import serializers
from .utils import files_in_dir
from functools import wraps


def cache(func):
    @wraps(func)
    def inner(self):
        cache_name = '__' + func.__name__ + '_cache'

        if not getattr(self, cache_name, None):
            setattr(self, cache_name, func(self))

        return getattr(self, cache_name)

    return inner


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
