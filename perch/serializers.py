#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from .utils import ClassRegistry

serializers = ClassRegistry()


@serializers.register('json')
class JSONSerializer(object):
    "serialize to and from JSON"
    def load(self, serialized):
        return json.loads(serialized)

    def dump(self, obj):
        return json.dumps(obj)
