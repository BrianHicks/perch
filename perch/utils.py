#!/usr/bin/env python
# -*- coding: utf-8 -*-
from py.path import local
import os

class ClassRegistry(dict):
    "hold and register classes by nickname, to select later"
    def register(self, name):
        def inner(cls):
            self[name] = cls
            return cls

        return inner

def files_in_dir(target):
    for l in local(target).visit(sort=True):
        if l.isfile():
            yield l
