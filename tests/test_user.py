# -*- coding: utf-8 -*-
from rrmngmnt import User, InternalDomain, ADUser, Domain


def test_user():
    assert "user" == User("user", 'pass').full_name


def test_indernal_domain():
    assert "user@internal" == ADUser(
        "user", "pass", InternalDomain(),
    ).full_name


def test_domain():
    assert "user@example.com" == ADUser(
        "user", "pass", Domain("example.com"),
    ).full_name
