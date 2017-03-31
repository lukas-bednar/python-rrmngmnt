# -*- coding: utf-8 -*-
import pytest
import netaddr
from rrmngmnt import common


def test_fqdn2ip_positive():
    ip = common.fqdn2ip('github.com')
    assert netaddr.valid_ipv4(ip)


def test_fqdn2ip_negative():
    with pytest.raises(Exception) as ex_info:
        common.fqdn2ip('github.or')
    assert 'github.or' in str(ex_info.value)
