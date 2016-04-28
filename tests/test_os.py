# -*- coding: utf8 -*-
import pytest

from rrmngmnt import Host, User
from rrmngmnt import errors
from .common import FakeExecutor


host_executor = Host.executor


def teardown_module():
    Host.executor = host_executor


def fake_cmd_data(cmd_to_data, files):
    def executor(self, user=User("fake", "pass"), pkey=False):
        e = FakeExecutor(user, self.ip)
        e.cmd_to_data = cmd_to_data.copy()
        e.files_content = files
        return e
    Host.executor = executor


class TestOperatingSystem(object):
    data = {
        'cat /etc/system-release': (
            0, 'Fedora release 23 (Twenty Three)', '',
        ),
        'cat /etc/os-release': (
            0,
            "\n".join(
                [
                    'NAME=Fedora',
                    'VERSION="23 (Workstation Edition)"',
                    'ID=fedora',
                    'VERSION_ID=23',
                    'PRETTY_NAME="Fedora 23 (Workstation Edition)"',
                    'ANSI_COLOR="0;34"',
                    'CPE_NAME="cpe:/o:fedoraproject:fedora:23"',
                    'HOME_URL="https://fedoraproject.org/"',
                    'BUG_REPORT_URL="https://bugzilla.redhat.com/"',
                    'REDHAT_BUGZILLA_PRODUCT="Fedora"',
                    'REDHAT_BUGZILLA_PRODUCT_VERSION=23',
                    'REDHAT_SUPPORT_PRODUCT="Fedora"',
                    'REDHAT_SUPPORT_PRODUCT_VERSION=23',
                    'PRIVACY_POLICY_URL=https://fedoraproject.org/wiki/'
                    'Legal:PrivacyPolicy',
                    'VARIANT="Workstation Edition"',
                    'VARIANT_ID=workstation',
                ]
            ), '',
        ),
        'python -c "import platform;print(\',\'.join('
        'platform.linux_distribution()))"': (0, 'Fedora,23,Twenty Three', ''),
    }
    files = {}

    @classmethod
    def setup_class(cls):
        fake_cmd_data(cls.data, cls.files)

    def get_host(self, ip='1.1.1.1'):
        return Host(ip)

    def test_get_release_str(self):
        result = self.get_host().os.release_str
        assert result == "Fedora release 23 (Twenty Three)"

    def test_get_release_info(self):
        result = self.get_host().os.release_info
        assert result['NAME'] == 'Fedora'
        assert result['ID'] == 'fedora'
        assert result['VERSION_ID'] == '23'
        assert result['VARIANT_ID'] == 'workstation'
        assert len(result) == 16

    def test_distro(self):
        result = self.get_host().os.distribution
        assert result.distname == 'Fedora'
        assert result.version == '23'
        assert result.id == 'Twenty Three'

    def test_old_distro(self):
        result = self.get_host().os_info
        assert result['dist'] == 'Fedora'
        assert result['ver'] == '23'
        assert result['name'] == 'Twenty Three'


class TestOperatingSystemNegative(object):
    data = {
        'cat /etc/system-release': (
            1, '', 'cat: /etc/system-release: No such file or directory',
        ),
        'cat /etc/os-release': (
            1, '', 'cat: /etc/os-release: No such file or directory',
        ),
        'python -c "import platform;print(\',\'.join('
        'platform.linux_distribution()))"': (1, '', 'SyntaxError'),
    }
    files = {}

    @classmethod
    def setup_class(cls):
        fake_cmd_data(cls.data, cls.files)

    def get_host(self, ip='1.1.1.1'):
        return Host(ip)

    def test_get_release_str(self):
        with pytest.raises(errors.CommandExecutionFailure) as ex_info:
            self.get_host().os.release_str
        assert "No such file" in str(ex_info.value)

    def test_get_release_info(self):
        with pytest.raises(errors.CommandExecutionFailure) as ex_info:
            self.get_host().os.release_info
        assert "No such file" in str(ex_info.value)

    def test_distro(self):
        with pytest.raises(errors.CommandExecutionFailure) as ex_info:
            self.get_host().os.distribution
        assert "SyntaxError" in str(ex_info.value)


class TestOperatingSystemUnsupported(object):
    data = {
        'cat /etc/os-release': (
            1, '', 'cat: /etc/os-release: No such file or directory',
        ),
        '[ -e /etc/os-release ]': (1, '', ''),
    }
    files = {}

    @classmethod
    def setup_class(cls):
        fake_cmd_data(cls.data, cls.files)

    def get_host(self, ip='1.1.1.1'):
        return Host(ip)

    def test_get_release_info(self):
        with pytest.raises(errors.UnsupportedOperation) as ex_info:
            self.get_host().os.release_info
        assert "release_info" in str(ex_info.value)


class TestOsReleaseCorrupted(object):
    data = {
        'cat /etc/os-release': (
            0,
            "\n".join(
                [
                    'NAME=Fedora',
                    'VERSION="23 (Workstation Edition)"',
                    'ID=fedora',
                    'VERSION_ID 23',
                    'PRETTY_NAME="Fedora 23 (Workstation Edition)"',
                    ' '
                ]
            ), '',
        ),
    }
    files = {}

    @classmethod
    def setup_class(cls):
        fake_cmd_data(cls.data, cls.files)

    def get_host(self, ip='1.1.1.1'):
        return Host(ip)

    def test_get_release_info(self):
        info = self.get_host().os.release_info
        assert 'VERSION_ID' not in info
        assert len(info) == 4
