# -*- coding: utf-8 -*-
from rrmngmnt import Host, User
from rrmngmnt.service import SysVinit, Systemd, InitCtl
from .common import FakeExecutorFactory
import pytest


host_executor_factory = Host.executor_factory


def teardown_module():
    Host.executor_factory = host_executor_factory


def fake_cmd_data(cmd_to_data, files=None):
    Host.executor_factory = FakeExecutorFactory(cmd_to_data, files)


def get_host(ip='1.1.1.1'):
    h = Host(ip)
    h.add_user(User('root', 'fakepasswd'))
    return h


class TestSystemService(object):
    __test__ = False

    service_enabled = "s-enabled"
    service_disabled = "s-disabled"
    service_stopped = "s-stopped"
    service_running = "s-running"
    factory = None
    data = None

    @classmethod
    def setup_class(cls):
        fake_cmd_data(cls.data)

    def get_service(self, name):
        return self.factory(get_host(), name)

    def test_is_enabled_positive(self):
        assert self.get_service(self.service_enabled).is_enabled()

    def test_is_enabled_negative(self):
        assert not self.get_service(self.service_disabled).is_enabled()

    def test_enable(self):
        assert self.get_service(self.service_disabled).enable()

    def test_disable(self):
        assert self.get_service(self.service_enabled).disable()

    def test_status_running(self):
        assert self.get_service(self.service_running).status()

    def test_status_stopped(self):
        assert not self.get_service(self.service_stopped).status()

    def test_start_positive(self):
        assert self.get_service(self.service_stopped).start()

    def test_start_negative(self):
        assert not self.get_service(self.service_running).start()

    def test_stop_positive(self):
        assert self.get_service(self.service_running).stop()

    def test_stop_negative(self):
        assert not self.get_service(self.service_stopped).stop()

    def test_restart(self):
        assert self.get_service(self.service_running).restart()

    def test_reload(self):
        assert self.get_service(self.service_running).reload()

    def test_mask(self):
        assert self.get_service(self.service_stopped).mask()

    def test_unmask(self):
        assert self.get_service(self.service_stopped).unmask()


class TestSystemd(TestSystemService):
    __test__ = True

    factory = Systemd
    data = {
        'which systemctl': (0, '/usr/bin/systemctl', ''),
        'systemctl list-unit-files | grep -o ^[^.][^.]*.service '
        '| cut -d. -f1 | sort | uniq': (
            0,
            '\n'.join(
                [
                    's-disabled',
                    's-enabled',
                    's-stopped',
                    's-running',
                ]
            ),
            ''
        ),
        'systemctl is-enabled s-enabled.service': (0, '', ''),
        'systemctl is-enabled s-disabled.service': (1, '', ''),
        'journalctl -u s-disabled.service': (0, '-- No entries --', ''),
        'systemctl enable s-disabled.service': (0, '', ''),
        'systemctl disable s-enabled.service': (0, '', ''),
        'systemctl status s-running.service': (0, '', ''),
        'systemctl status s-stopped.service': (1, '', ''),
        'journalctl -u s-stopped.service': (0, '-- No entries --', ''),
        'systemctl start s-stopped.service': (0, '', ''),
        'systemctl start s-running.service': (1, '', ''),
        'journalctl -u s-running.service': (0, '-- No entries --', ''),
        'systemctl stop s-stopped.service': (1, '', ''),
        'journalctl -u s-stopped.service': (0, '-- No entries --', ''),
        'systemctl stop s-running.service': (0, '', ''),
        'systemctl restart s-running.service': (0, '', ''),
        'systemctl reload s-running.service': (0, '', ''),
        'systemctl mask s-stopped.service': (0, '', ''),
        'systemctl unmask s-stopped.service': (0, '', ''),
    }


class TestSysVinit(TestSystemService):
    __test__ = True
    factory = SysVinit
    data = {
        'which service': (0, '/usr/sbin/service', ''),
        '[ -e /etc/init.d/s-enabled ]': (0, '', ''),
        '[ -e /etc/init.d/s-disabled ]': (0, '', ''),
        '[ -e /etc/init.d/s-running ]': (0, '', ''),
        '[ -e /etc/init.d/s-stopped ]': (0, '', ''),
        'chkconfig s-enabled': (0, '', ''),
        'chkconfig s-disabled': (1, '', ''),
        'chkconfig s-disabled on': (0, '', ''),
        'chkconfig s-enabled off': (0, '', ''),
        'service s-running status': (0, '', ''),
        'service s-stopped status': (1, '', ''),
        'service s-stopped start': (0, '', ''),
        'service s-running start': (1, '', ''),
        'service s-stopped stop': (1, '', ''),
        'service s-running stop': (0, '', ''),
        'service s-running restart': (0, '', ''),
        'service s-running reload': (0, '', ''),
    }

    def test_mask(self):
        with pytest.raises(NotImplementedError):
            super(TestSysVinit, self).test_mask()

    def test_unmask(self):
        with pytest.raises(NotImplementedError):
            super(TestSysVinit, self).test_unmask()


class TestInitCtl(TestSystemService):
    __test__ = True
    factory = InitCtl
    data = {
        'which initctl': (0, '/sbin/initctl', ''),
        'initctl list | cut -d " " -f1 | sort | uniq': (
            0,
            '\n'.join(
                [
                    's-disabled',
                    's-enabled',
                    's-stopped',
                    's-running',
                ]
            ),
            '',
        ),
        'initctl status s-running': (0, 's-running start/running', ''),
        'initctl status s-stopped': (0, 's-stopped stop/waiting', ''),
        'initctl start s-stopped': (0, '', ''),
        'initctl start s-running': (
            1, '', 'initctl: Job is already running: s-running',
        ),
        'initctl stop s-stopped': (1, '', ''),
        'initctl stop s-running': (0, '', ''),
        'initctl restart s-running': (0, '', ''),
        'initctl reload s-running': (0, '', ''),
    }

    def test_is_enabled_positive(self):
        with pytest.raises(NotImplementedError):
            super(TestInitCtl, self).test_is_enabled_positive()

    def test_is_enabled_negative(self):
        with pytest.raises(NotImplementedError):
            super(TestInitCtl, self).test_is_enabled_negative()

    def test_enable(self):
        with pytest.raises(NotImplementedError):
            super(TestInitCtl, self).test_enable()

    def test_disable(self):
        with pytest.raises(NotImplementedError):
            super(TestInitCtl, self).test_disable()

    def test_mask(self):
        with pytest.raises(NotImplementedError):
            super(TestInitCtl, self).test_mask()

    def test_unmask(self):
        with pytest.raises(NotImplementedError):
            super(TestInitCtl, self).test_unmask()
