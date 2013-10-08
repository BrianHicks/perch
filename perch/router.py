#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from .config import constants
from .serializers import serializers
from .utils import files_in_dir


class Discoverer(object):
    categories = ['collector', 'filter', 'renderer']

    def __init__(self, directory):
        self.directory = directory
        self._stages = []
        self._classified = {}

    def _find_stages(self):
        "find stages in a directory"
        if self._stages:
            return

        self._stages = list(files_in_dir(self.directory))

    def _classify_stages(self):
        "classify the stages already found"
        if self._classified:
            return

        self._classified = {
            category: {
                f for f in self._stages
                if category in f.relto(self.directory)
            }
            for category in self.categories
        }

    def discover(self):
        "discover stages"
        self._find_stages()
        self._classify_stages()
        return self._classified
