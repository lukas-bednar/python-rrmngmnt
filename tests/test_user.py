# -*- coding: utf-8 -*-
from rrmngmnt import User, UserWithPKey, InternalDomain, ADUser, Domain


def test_user():
    user = User("user", 'pass')
    assert "user" == user.full_name
    assert user.credentials == user.password


def test_indernal_domain():
    assert "user@internal" == ADUser(
        "user", "pass", InternalDomain(),
    ).full_name


def test_domain():
    assert "user@example.com" == ADUser(
        "user", "pass", Domain("example.com"),
    ).full_name


def test_user_with_pkey():
    user = UserWithPKey("user", "/path/to/key")
    assert 'user' == user.full_name
    assert '/path/to/key' == user.credentials
