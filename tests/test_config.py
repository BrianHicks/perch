#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
from perch.config import Settings

@pytest.fixture
def settings():
    return Settings(a=1)

def test_get_dot(settings):
    'getting works with __getattr__'
    assert settings.a == 1

def test_get_dict(settings):
    'getting works with __getitem__'
    assert settings['a'] == 1

def test_set_dot(settings):
    'setting does not work with __setattr__'
    with pytest.raises(TypeError):
        settings.a = 2

    assert settings.a == 1

def test_set_dict(settings):
    'setting does not work with __setitem__'
    with pytest.raises(TypeError):
        settings['a'] = 2

    assert settings.a == 1
