#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import json

from .utils import ClassRegistry

serializers = ClassRegistry()


@serializers.register('json')
class JSONSerializer(object):
    "serialize to and from JSON"
    class Encoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()

            return json.JSONEncoder.default(self, obj)

    def load(self, serialized):
        return json.loads(serialized)

    def dump(self, obj):
        return json.dumps(obj, cls=self.Encoder)
