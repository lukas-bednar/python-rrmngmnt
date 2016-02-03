# -*- coding: utf8 -*-
from rrmngmnt import Host
from .common import FakeExecutor
import pytest


def fake_cmd_data(cmd_to_data):
    def executor(self, user=None):
        e = FakeExecutor(user)
        e.cmd_to_data = cmd_to_data.copy()
        return e
    Host.executor = executor


class TestFilesystem(object):
    data = {
        '[ -e /tmp/exits ]': (0, '', ''),
        '[ -e /tmp/doesnt_exist ]': (1, '', ''),
        '[ -f /tmp/file ]': (0, '', ''),
        '[ -f /tmp/nofile ]': (1, '', ''),
        '[ -d /tmp/dir ]': (0, '', ''),
        '[ -d /tmp/nodir ]': (1, '', ''),
        'rm -f /path/to/remove': (0, '', ''),
        'rm -f /dir/to/remove': (
            1, '', 'rm: cannot remove ‘.tox/’: Is a directory',
        ),
        'rm -rf /dir/to/remove': (0, '', ''),
        'cat %s' % "/tmp/file": ('', 'data', ''),
    }

    @classmethod
    def setup_class(cls):
        fake_cmd_data(cls.data)

    def get_host(self, ip='1.1.1.1'):
        return Host(ip)

    def test_exists_positive(self):
        assert self.get_host().fs.exists('/tmp/exits')

    def test_exists_negative(self):
        assert not self.get_host().fs.exists('/tmp/doesnt_exist')

    def test_isfile_positive(self):
        assert self.get_host().fs.isfile('/tmp/file')

    def test_isfile_negative(self):
        assert not self.get_host().fs.isfile('/tmp/nofile')

    def test_isdir_positive(self):
        assert self.get_host().fs.isdir('/tmp/dir')

    def test_isdir_negative(self):
        assert not self.get_host().fs.isdir('/tmp/nodir')

    def test_remove_positive(self):
        assert self.get_host().fs.remove('/path/to/remove')

    def test_remove_negative(self):
        assert not self.get_host().fs.remove('/dir/to/remove')

    def test_rmdir_positive(self):
        assert self.get_host().fs.rmdir('/dir/to/remove')

    def test_rmdir_negative(self):
        with pytest.raises(ValueError):
            self.get_host().fs.rmdir('/')

    def test_read_file(self):
        assert self.get_host().fs.read_file("/tmp/file") == "data"
