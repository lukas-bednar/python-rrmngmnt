# -*- coding: utf-8 -*-
import pytest

from rrmngmnt import Host, User
from rrmngmnt import errors
from .common import FakeExecutorFactory


host_executor_factory = Host.executor_factory


def teardown_module():
    Host.executor_factory = host_executor_factory


def fake_cmd_data(cmd_to_data, files=None):
    Host.executor_factory = FakeExecutorFactory(cmd_to_data, files)


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
        'uname -r ; uname -v ; uname -m': (
            0, '4.18.0-135.el8\n#1 SMP Fri Aug 16 19:31:40 UTC\nx86_64\n', '',
        ),
        'date +%Z\\ %z': (0, 'IDT +0300', ''),
    }
    files = {}

    @classmethod
    def setup_class(cls):
        fake_cmd_data(cls.data, cls.files)

    def get_host(self, ip='1.1.1.1'):
        h = Host(ip)
        h.add_user(User('root', '11111'))
        return h

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

    def test_get_kernel_info(self):
        result = self.get_host().os.kernel_info
        assert result.release == '4.18.0-135.el8'
        assert result.version == '#1 SMP Fri Aug 16 19:31:40 UTC'
        assert result.type == 'x86_64'

    def test_get_timezone(self):
        result = self.get_host().os.timezone
        assert result.name == 'IDT'
        assert result.offset == '+0300'


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
        h = Host(ip)
        h.add_user(User('root', '11114'))
        return h

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
        h = Host(ip)
        h.add_user(User('root', '22222'))
        return h

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
        h = Host(ip)
        h.add_user(User('root', '3333'))
        return h

    def test_get_release_info(self):
        info = self.get_host().os.release_info
        assert 'VERSION_ID' not in info
        assert len(info) == 4


type_map = {
    'st_mode': ('0x%f', lambda x: int(x, 16)),
    'st_ino': ('%i', int),
    'st_dev': ('%d', int),
    'st_nlink': ('%h', int),
    'st_uid': ('%u', int),
    'st_gid': ('%g', int),
    'st_size': ('%s', int),
    'st_atime': ('%X', int),
    'st_mtime': ('%Y', int),
    'st_ctime': ('%W', int),
    'st_blocks': ('%b', int),
    'st_blksize': ('%o', int),
    'st_rdev': ('%t', int),
}


class TestFileStats(object):
    data = {
        'stat -c %s /tmp/test' %
        ','.join(["%s=%s" % (k, v[0]) for k, v in type_map.items()]): (
            0,
            (
                'st_ctime=0,'
                'st_rdev=0,'
                'st_blocks=1480,'
                'st_nlink=1,'
                'st_gid=0,'
                'st_dev=2051,'
                'st_ino=11804680,'
                'st_mode=0x81a4,'
                'st_mtime=1463487739,'
                'st_blksize=4096,'
                'st_size=751764,'
                'st_uid=0,'
                'st_atime=1463487196'
            ),
            ''
        ),
        'stat -c "%U %G" /tmp/test': (
            0,
            'root root',
            ''
        ),
        'stat -c %a /tmp/test': (
            0,
            '644\n',
            ''
        ),
        'id -u root': (
            0,
            '',
            ''
        ),
        'id -g root': (
            0,
            '',
            ''
        )
    }
    files = {}

    @classmethod
    def setup_class(cls):
        fake_cmd_data(cls.data, cls.files)

    def get_host(self, ip='1.1.1.1'):
        h = Host(ip)
        h.add_user(User('root', '11331'))
        return h

    def test_get_file_stats(self):
        file_stats = self.get_host().os.stat('/tmp/test')
        assert (
            file_stats.st_mode == 33188 and
            file_stats.st_uid == 0 and
            file_stats.st_gid == 0
        )

    def test_get_file_owner(self):
        file_user, file_group = self.get_host().os.get_file_owner('/tmp/test')
        assert file_user == 'root' and file_group == 'root'

    def test_get_file_permissions(self):
        assert self.get_host().os.get_file_permissions('/tmp/test') == '644'

    def test_user_exists(self):
        assert self.get_host().os.user_exists('root')

    def test_group_exists(self):
        assert self.get_host().os.group_exists('root')


class TestFileStatsNegative(object):
    data = {
        'stat -c %s /tmp/negative_test' %
        ','.join(["%s=%s" % (k, v[0]) for k, v in type_map.items()]): (
            1,
            '',
            'cannot stat ‘/tmp/negative_test’: No such file or directory'
        ),
        'stat -c "%U %G" /tmp/negative_test': (
            1,
            '',
            'cannot stat ‘/tmp/negative_test’: No such file or directory'
        ),
        'stat -c %a /tmp/negative_test': (
            1,
            '',
            'cannot stat ‘/tmp/negative_test’: No such file or directory'
        ),
        'id -u test': (
            1,
            '',
            ''
        ),
        'id -g test': (
            1,
            '',
            ''
        )
    }
    files = {}

    @classmethod
    def setup_class(cls):
        fake_cmd_data(cls.data, cls.files)

    def get_host(self, ip='1.1.1.1'):
        h = Host(ip)
        h.add_user(User('root', '155511'))
        return h

    def test_get_file_stats(self):
        with pytest.raises(errors.CommandExecutionFailure) as ex_info:
            self.get_host().os.stat('/tmp/negative_test')
        assert "No such file" in str(ex_info.value)

    def test_get_file_owner(self):
        with pytest.raises(errors.CommandExecutionFailure) as ex_info:
            self.get_host().os.get_file_owner('/tmp/negative_test')
        assert "No such file" in str(ex_info.value)

    def test_get_file_permissions(self):
        with pytest.raises(errors.CommandExecutionFailure) as ex_info:
            self.get_host().os.get_file_permissions('/tmp/negative_test')
        assert "No such file" in str(ex_info.value)

    def test_user_exists(self):
        assert not self.get_host().os.user_exists('test')

    def test_group_exists(self):
        assert not self.get_host().os.group_exists('test')
