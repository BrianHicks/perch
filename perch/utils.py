#!/usr/bin/env python
# -*- coding: utf-8 -*-

class ClassRegistry(dict):
    "hold and register classes by nickname, to select later"
    def register(self, name):
        def inner(cls):
            self[name] = cls
            return cls

        return inner
