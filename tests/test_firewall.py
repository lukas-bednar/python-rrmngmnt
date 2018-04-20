# -*- coding: utf-8 -*-
import pytest
from rrmngmnt import Host
from rrmngmnt.user import RootUser
from .common import FakeExecutorFactory

host_executor_factory = Host.executor_factory


def teardown_module():
    Host.executor_factory = host_executor_factory


def fake_cmd_data(cmd_to_data, files=None):
    Host.executor_factory = FakeExecutorFactory(cmd_to_data, files)


def get_host(ip='1.1.1.1'):
    h = Host(ip)
    h.users.append(RootUser('123456'))
    return h


class TestFirewall(object):

    data = {
        'which systemctl': (0, '/usr/bin/systemctl', ''),
        'systemctl list-unit-files | grep -o ^[^.][^.]*.service '
        '| cut -d. -f1 | sort | uniq': (
            0,
            '\n'.join(
                [
                    'iptables',
                    'noniptables',
                ]
            ),
            ''
        ),
        'systemctl status iptables.service': (0, '', ''),
        'systemctl status noniptables.service': (1, '', ''),
    }

    @classmethod
    def setup_class(cls):
        fake_cmd_data(cls.data)

    def test_running_service_positive(self):
        assert get_host().firewall.is_active('iptables')


class TestChain(object):

    data = {
        'iptables --append OUTPUT --destination 2.2.2.2 --jump DROP '
        '--protocol all': (0, '', ''),
        'iptables --append INPUT --source 2.2.2.2 --jump DROP '
        '--protocol all': (0, '', ''),
        'iptables --insert OUTPUT --destination 2.2.2.2 --jump DROP '
        '--protocol all': (0, '', ''),
        'iptables --insert INPUT --source 2.2.2.2 --jump DROP '
        '--protocol all': (0, '', ''),
        'iptables --delete OUTPUT --destination 2.2.2.2 --jump DROP '
        '--protocol all': (0, '', ''),
        'iptables --delete INPUT --source 2.2.2.2 --jump DROP '
        '--protocol all': (0, '', ''),
        'iptables --append OUTPUT --destination 2.2.2.2 --jump DROP '
        '--protocol tcp --match multiport --dports '
        '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15': (0, '', ''),
        'iptables --append OUTPUT --destination 2.2.2.2 --jump DROP '
        '--protocol tcp --match multiport --dports '
        '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15, 16': (
            4, '', 'iptables v1.4.21: too many ports specified'
        ),
        'iptables --flush OUTPUT': (0, '', '')
    }

    destination_host = {'address': ['2.2.2.2']}
    ports = [
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13',
        '14', '15'
    ]
    too_many_ports = [
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13',
        '14', '15', '16'
    ]

    @classmethod
    def setup_class(cls):
        fake_cmd_data(cls.data)

    def test_wrong_chain_name(self):
        with pytest.raises(NotImplementedError):
            get_host().firewall.chain('CHAIN')

    def test_add_outgoing_rule(self):
        assert get_host().firewall.chain('OUTPUT').add_rule(
            self.destination_host, 'DROP'
        )

    def test_add_incoming_rule(self):
        assert get_host().firewall.chain('INPUT').add_rule(
            self.destination_host, 'DROP'
        )

    def test_insert_outgoing_rule(self):
        assert get_host().firewall.chain('OUTPUT').insert_rule(
            self.destination_host, 'DROP'
        )

    def test_insert_incoming_rule(self):
        assert get_host().firewall.chain('INPUT').insert_rule(
            self.destination_host, 'DROP'
        )

    def test_delete_outgoing_rule(self):
        assert get_host().firewall.chain('OUTPUT').delete_rule(
            self.destination_host, 'DROP'
        )

    def test_delete_incoming_rule(self):
        assert get_host().firewall.chain('OUTPUT').delete_rule(
            self.destination_host, 'DROP'
        )

    def test_add_outgoing_rule_with_ports(self):
        assert get_host().firewall.chain('OUTPUT').add_rule(
            self.destination_host, 'DROP', ports=self.ports
        )

    def test_add_outgoing_rule_with_too_many_ports(self):
        with pytest.raises(NotImplementedError):
            get_host().firewall.chain('OUTPUT').add_rule(
                self.destination_host, 'DROP', ports=self.too_many_ports
            )

    def test_clean_firewall_rules(self):
        assert get_host().firewall.chain('OUTPUT').clean_rules()
