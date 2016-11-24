# -*- coding: utf-8 -*-
from rrmngmnt import Host, User, RootUser
import pytest


def get_host(ip='1.1.1.1'):
    return Host(ip)


class TestExecutorUser(object):

    def test_no_user(self):
        with pytest.raises(Exception):
            get_host().executor()

    def test_root_user(self):
        h = get_host()
        h.users.append(RootUser('123456'))
        e = h.executor()
        assert e.user.name == RootUser.NAME

    def test_custom_user(self):
        user = User('lukas', '123456')
        e = get_host().executor(user=user)
        assert e.user.name == 'lukas'

    def test_executor_user(self):
        user = User('lukas', '123456')
        h = get_host()
        h.executor_user = user
        e = h.executor()
        e.user.name == 'lukas'


class TestHostFqdnIp(object):

    def test_host_ip(self):
        h = Host('127.0.0.1')
        assert h.ip == '127.0.0.1'
        assert 'localhost' in h.fqdn

    def test_host_fqdn(self):
        h = Host('localhost')
        assert h.ip == '127.0.0.1'
        assert 'localhost' in h.fqdn
