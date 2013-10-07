#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Settings(dict):
    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError('no key or attribute "%s"' % attr)

    def __setattr__(self, attr, val):
        raise TypeError('"settings" object does not support item assignment')

    def __setitem__(self, attr, val):
        raise TypeError('"settings" object does not support item assignment')


constants = Settings({
    'stage_env_var': 'PERCH_CONFIG',

    # serializer stuff
    'serializer_key': 'serializer',
    'default_serializer': 'json',
})
