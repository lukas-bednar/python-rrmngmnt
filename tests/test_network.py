# -*- coding: utf-8 -*-
from rrmngmnt import Host, RootUser
from .common import FakeExecutor


host_executor = Host.executor


def teardown_module():
    Host.executor = host_executor


def fake_cmd_data(cmd_to_data, files):
    def executor(self, user=None, pkey=False):
        e = FakeExecutor(user, self.ip)
        e.cmd_to_data = cmd_to_data.copy()
        e.files = files
        return e
    Host.executor = executor


def get_host(ip='1.1.1.1'):
    h = Host(ip)
    h.users.append(RootUser('123456'))
    return h


class TestNetwork(object):
    __test__ = True

    data = {
        'ip route': (
            0,
            '\n'.join(
                [

                    'default via 10.11.12.254 dev ovirtmgmt ',
                    '10.11.12.0/24 dev ovirtmgmt  proto kernel  scope link  '
                    'src 10.11.12.35 ',
                    '10.11.12.0/24 dev enp4s0f1  proto kernel  scope link  '
                    'src 10.11.12.81 ',
                    '10.11.12.0/24 dev enp5s0f0  proto kernel  scope link  '
                    'src 10.11.12.83 ',
                    '169.254.0.0/16 dev enp5s0f0  scope link  metric 1002 ',
                    '169.254.0.0/16 dev enp4s0f1  scope link  metric 1005 ',
                    '169.254.0.0/16 dev ovirtmgmt  scope link  metric 1007',
                ]
            ),
            '',
        ),
        'ip -6 route': (
            0,
            '\n'.join(
                [
                    'unreachable ::/96 dev lo  metric 1024  error -101',
                    'unreachable 2002:a9fe::/32 lo metric 1024  error -101',
                    'unreachable 2002:ac10::/28 lo metric 1024  error -101',
                    'fe80:52:0::3fe dev eth0  proto static  metric 100 ',
                    'default via fe80::0:3fe dev eth0 proto static metric 100',
                ]
            ),
            '',
        ),
        'ip addr': (
            0,
            ''.join(
                [
                    '1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue '
                    'state UNKNOWN \n',
                    '    link/loopback 00:00:00:00:00:00 brd '
                    '00:00:00:00:00:00\n',
                    '    inet 127.0.0.1/8 scope host lo\n',
                    '       valid_lft forever preferred_lft forever\n',
                    '    inet6 ::1/128 scope host \n',
                    '       valid_lft forever preferred_lft forever\n',
                    '2: enp5s0f0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 '
                    'qdisc mq state UP qlen 1000\n',
                    '    link/ether 44:1e:a1:73:3c:98 brd ff:ff:ff:ff:ff:ff\n',
                    '    inet 10.11.12.83/24 brd 10.11.12.255 scope global '
                    'enp5s0f0\n',
                    '       valid_lft forever preferred_lft forever\n',
                    '    inet6 fe80::461e:a1ff:fe73:3c98/64 scope link \n',
                    '       valid_lft forever preferred_lft forever\n',
                    '3: enp4s0f0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 '
                    'qdisc mq master ovirtmgmt state UP qlen 1000\n',
                    '    link/ether 00:9c:02:b0:bf:a0 brd ff:ff:ff:ff:ff:ff\n',
                    '    inet6 fe80::29c:2ff:feb0:bfa0/64 scope link \n',
                    '       valid_lft forever preferred_lft forever\n',
                    '4: enp5s0f1: <BROADCAST,MULTICAST> mtu 1500 qdisc noop '
                    'state DOWN qlen 1000\n',
                    '    link/ether 44:1e:a1:73:3c:99 brd ff:ff:ff:ff:ff:ff\n',
                    '5: enp4s0f1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 '
                    'qdisc mq state UP qlen 1000\n',
                    '    link/ether 00:9c:02:b0:bf:a4 brd ff:ff:ff:ff:ff:ff\n',
                    '    inet 10.11.12.81/24 brd 10.11.12.255 scope global '
                    'enp4s0f1\n',
                    '       valid_lft forever preferred_lft forever\n',
                    '    inet6 fe80::29c:2ff:feb0:bfa4/64 scope link \n',
                    '       valid_lft forever preferred_lft forever\n',
                    '6: bond0: <BROADCAST,MULTICAST,MASTER> mtu 1500 qdisc '
                    'noop state DOWN \n',
                    '    link/ether 16:17:fe:8e:0f:46 brd ff:ff:ff:ff:ff:ff\n',
                    '7: ovirtmgmt: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 '
                    'qdisc noqueue state UP \n',
                    '    link/ether 00:9c:02:b0:bf:a0 brd ff:ff:ff:ff:ff:ff\n',
                    '    inet 10.11.12.35/24 brd 10.11.12.255 scope global '
                    'dynamic ovirtmgmt\n',
                    '       valid_lft 41596sec preferred_lft 41596sec\n',
                    '    inet6 fe80::29c:2ff:feb0:bfa0/64 scope link \n',
                    '       valid_lft forever preferred_lft forever\n',
                    '8: ;vdsmdummy;: <BROADCAST,MULTICAST> mtu 1500 qdisc '
                    'noop state DOWN \n',
                    '    link/ether 82:0c:ab:0f:ed:8b brd ff:ff:ff:ff:ff:ff\n',
                ]
            ),
            '',
        ),
        'ip addr show to 10.11.12.83': (
            0,
            '\n'.join(
                [
                    '2: enp5s0f0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 '
                    'qdisc mq state UP qlen 1000',
                    '    inet 10.11.12.83/24 brd 10.11.12.255 scope global '
                    'enp5s0f0',
                    '           valid_lft forever preferred_lft forever',
                ]
            ),
            ''
        ),
        'ip addr show eth0': (
            0,
            '\n'.join(
                [
                    '2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu ...',
                    'link/ether 00:1a:4a:01:3f:1c brd ff:ff:ff:ff:ff:ff',
                    'inet 10.11.12.84/22 brd 10.11.12.255 scope global',
                    'valid_lft 20343sec preferred_lft 20343sec',
                    'inet6 2620:52:0::fe01:3f1c/64 scope global dynamic',
                    'valid_lft 2591620sec preferred_lft 604420sec',
                    'inet6 fe80::4aff:fe01:3f1c/64 scope link ',
                    'valid_lft forever preferred_lft forever',
                ]
            ),
            ''
        ),
        'ip -6 addr show eth0': (
            0,
            '\n'.join(
                [
                    '2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu ...',
                    'link/ether 00:1a:4a:01:3f:1c brd ff:ff:ff:ff:ff:ff',
                    'inet6 2620:52:0::fe01:3f1c/64 scope global dynamic',
                    'valid_lft 2591620sec preferred_lft 604420sec',
                    'inet6 fe80::4aff:fe01:3f1c/64 scope link ',
                    'valid_lft forever preferred_lft forever',
                ]
            ),
            ''
        ),
        'brctl show | sed -e "/^bridge name/ d" '
        '-e \'s/^\\s\\s*\\(\\S\\S*\\)$/CONT:\\1/I\'': (
            0,
            '\n'.join(
                [
                    ';vdsmdummy;     8000.000000000000   no      ',
                    'ovirtmgmt       8000.009c02b0bfa0   no      enp4s0f0',
                ]
            ),
            '',
        ),
        'brctl addbr br1': (0, '', ''),
        'brctl addif br1 net1': (0, '', ''),
        'ls -la /sys/class/net | grep \'dummy_\|pci\' | grep -o \'[^/]*$\'': (
            0,
            '\n'.join(
                [
                    'enp4s0f0',
                    'enp4s0f1',
                    'enp5s0f0',
                    'enp5s0f',
                ]
            ),
            '',
        ),
        "ethtool -P enp5s0f0": (
            0,
            "Permanent address: 44:1e:a1:73:3c:98",
            ''
        ),
        'ip link set up interface': True,
        'ip link set down interface': True,
    }
    files = {
    }

    @classmethod
    def setup_class(cls):
        fake_cmd_data(cls.data, cls.files)

    def test_get_info(self):
        info = get_host().network.get_info()
        expected_info = {
            'bridge': 'N/A',
            'ip': '10.11.12.83',
            'gateway': '10.11.12.254',
            'interface': 'enp5s0f0',
        }
        assert info == expected_info

    def test_find_default_gw(self):
        dgw = get_host().network.find_default_gw()
        assert dgw == '10.11.12.254'

    def test_list_bridges(self):
        bridges = get_host().network.list_bridges()
        expected = [
            {
                'id': '8000.000000000000',
                'interfaces': [],
                'name': ';vdsmdummy;',
                'stp': 'no',
            },
            {
                'id': '8000.009c02b0bfa0',
                'interfaces': ['enp4s0f0'],
                'name': 'ovirtmgmt',
                'stp': 'no',
            },
        ]
        assert bridges == expected

    def test_add_bridge(self):
        assert get_host().network.add_bridge("br1", "net1")

    def test_find_mgmt_interface(self):
        assert get_host().network.find_mgmt_interface() == 'enp5s0f0'

    def test_all_interfaces(self):
        expected = ['enp4s0f0', 'enp4s0f1', 'enp5s0f0', 'enp5s0f']
        assert get_host().network.all_interfaces() == expected

    def test_get_mac_address_by_ip(self):
        expected = "44:1e:a1:73:3c:98"
        assert get_host().network.get_mac_by_ip("10.11.12.83") == expected

    def test_find_ip_by_int(self):
        assert get_host().network.find_ip_by_int("eth0") == "10.11.12.84"

    def test_find_ipv6_by_int(self):
        expected = "2620:52:0::fe01:3f1c"
        assert get_host().network.find_ipv6_by_int("eth0") == expected

    def test_find_default_gwv6(self):
        assert get_host().network.find_default_gwv6() == "fe80::0:3fe"

    def if_up(self):
        assert get_host().network.if_up("interface")

    def if_down(self):
        assert get_host().network.if_down("interface")


class TestHostNameCtl(object):

    data = {
        'which hostnamectl': (0, '/usr/bin/hostnamectl', ''),
        'hostnamectl set-hostname something': (0, '', ''),
        'hostnamectl status | grep hostname | tr -d " " | cut -d: -f2': (
            0, 'local', '',
        ),
    }
    files = {
    }

    @classmethod
    def setup_class(cls):
        fake_cmd_data(cls.data, cls.files)

    def test_get(self):
        assert get_host().network.hostname == "local"

    def test_set(self):
        get_host().network.hostname = "something"


class TestHostNameEtc(object):

    data = {
        'which hostnamectl': (1, '', ''),
        'hostname -f': (0, 'local', ''),
        'hostname something ; sed -i -e /^HOSTNAME/d /etc/sysconfig/network '
        '&& echo HOSTNAME=something >> /etc/sysconfig/network': (0, '', ''),
    }
    files = {
    }

    @classmethod
    def setup_class(cls):
        fake_cmd_data(cls.data, cls.files)

    def test_get(self):
        assert get_host().network.hostname == "local"

    def test_set(self):
        get_host().network.hostname = "something"
