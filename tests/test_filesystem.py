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


class TestFilesystem(object):
    data = {
        '[ -e /tmp/exits ]': (0, '', ''),
        '[ -e /tmp/doesnt_exist ]': (1, '', ''),
        '[ -f /tmp/file ]': (0, '', ''),
        '[ -f /tmp/nofile ]': (1, '', ''),
        '[ -d /tmp/dir ]': (0, '', ''),
        '[ -d /tmp/nodir ]': (1, '', ''),
        '[ -d /path/to/file1 ]': (1, '', ''),
        '[ -d /path/to ]': (0, '', ''),
        '[ -d somefile ]': (1, '', ''),
        '[ -x /tmp/executable ]': (0, '', ''),
        '[ -x /tmp/nonexecutable ]': (1, '', ''),
        'rm -f /path/to/remove': (0, '', ''),
        'rm -f /dir/to/remove': (
            1, '', 'rm: cannot remove ‘.tox/’: Is a directory',
        ),
        'rm -rf /dir/to/remove': (0, '', ''),
        'cat %s' % "/tmp/file": (0, 'data', ''),
        'chmod +x /tmp/hello.sh': (0, '', ''),
        'mkdir /dir/to/remove': (0, '', ''),
        'mkdir -p -m 600 /dir/to/remove2/remove': (0, '', ''),
        'chown root:root /dir/to/remove': (0, '', ''),
        'chmod 600 /dir/to/remove': (0, '', ''),
        'chmod 600 /tmp/nofile': (
            1, '',
            'chmod: cannot access ‘/tmp/nofile’: No such file or directory',
        ),
        'touch /path/to/file /path/to/file1': (0, '', ''),
        'touch /path/to/file2': (0, '', ''),
        'touch /path/to/nopermission': (1, '', ''),
        'ls -A1 /path/to/empty': (0, '\n', ''),
        'ls -A1 /path/to/two': (0, 'first\nsecond\n', ''),
        'mktemp -d': (0, '/path/to/tmpdir', ''),
        'mount -v -t xfs -o bind,ro /path/to /path/to/tmpdir': (0, '', ''),
        'ls -A1 /path/to/tmpdir': (0, 'first\nsecond\n', ''),
        'mount -v -o remount,bind,rw /path/to/tmpdir': (0, '', ''),
        'umount -v -f /path/to/tmpdir': (0, '', ''),
        'mount -v /not/device /path/to/tmpdir': (
            32, '', '/not/device is not a block device\n'
        ),
        'truncate -s 0 /tmp/file_to_flush': (0, '', ''),
        'mv /tmp/source /tmp/destination': (0, '', ''),
    }
    files = {}

    @classmethod
    def setup_class(cls):
        fake_cmd_data(cls.data, cls.files)

    def get_host(self, ip='1.1.1.1'):
        h = Host(ip)
        h.add_user(User('root', '11111'))
        return h

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

    def test_isexec_positive(self):
        assert self.get_host().fs.isexec('/tmp/executable')

    def test_isexec_negative(self):
        assert not self.get_host().fs.isexec('/tmp/nonexecutable')

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

    def test_move(self):
        assert self.get_host().fs.move("/tmp/source", "/tmp/destination")

    def test_flush_file(self):
        assert self.get_host().fs.flush_file("/tmp/file_to_flush")

    def test_create_file(self):
        data = "hello world"
        path = "/tmp/hello.txt"
        self.get_host().fs.create_file(data, path)
        assert self.files[path].data == data

    def test_create_script(self):
        data = "echo hello"
        path = '/tmp/hello.sh'
        self.get_host().fs.create_script(data, path)
        assert self.files[path].data == data

    def test_mkdir_positive(self):
        self.get_host().fs.mkdir('/dir/to/remove')

    def test_mkdir_pm_positive(self):
        self.get_host().fs.mkdir(
            '/dir/to/remove2/remove', parents=True, mode='600'
        )

    def test_chown_positive(self):
        self.get_host().fs.chown('/dir/to/remove', 'root', 'root')

    def test_chmod_positive(self):
        self.get_host().fs.chmod('/dir/to/remove', '600')

    def test_chmod_negative(self):
        with pytest.raises(errors.CommandExecutionFailure) as ex_info:
            self.get_host().fs.chmod('/tmp/nofile', '600')
        assert "No such file or directory" in str(ex_info.value)

    def test_touch_positive(self):
        assert self.get_host().fs.touch('/path/to/file', '/path/to/file1')

    def test_touch_negative(self):
        assert not self.get_host().fs.touch('/path/to/nopermission')

    def test_backwards_comp_touch(self):
        assert self.get_host().fs.touch('file2', '/path/to')

    def test_touch_wrong_params(self):
        with pytest.raises(Exception) as ex_info:
            self.get_host().fs.touch('/path/to', 'somefile')
        assert "touch /path/to" in str(ex_info.value)

    def test_listdir_empty(self):
        assert self.get_host().fs.listdir('/path/to/empty') == []

    def test_listdir_two(self):
        assert self.get_host().fs.listdir('/path/to/two') == [
            'first', 'second',
        ]

    def test_mount_point(self):
        with self.get_host().fs.mount_point(
            '/path/to', opts='bind,ro', fs_type='xfs'
        ) as mp:
            assert not mp.remount('bind,rw')

    def test_fail_mount(self):
        with pytest.raises(errors.MountError) as ex_info:
            with self.get_host().fs.mount_point('/not/device'):
                pass
        assert "is not a block device" in str(ex_info.value)


class TestFSGetPutFile(object):
    data = {
        "[ -d /path/to/put_dir ]": (0, "", ""),
    }
    files = {
        "/path/to/get_file": "data of get_file",
    }

    @classmethod
    def setup_class(cls):
        fake_cmd_data(cls.data, cls.files)

    def get_host(self, ip='1.1.1.1'):
        h = Host(ip)
        h.add_user(User('root', '11111'))
        return h

    def test_get(self, tmpdir):
        self.get_host().fs.get("/path/to/get_file", str(tmpdir))
        assert tmpdir.join("get_file").read() == "data of get_file"

    def test_put(self, tmpdir):
        p = tmpdir.join("put_file")
        p.write("data of put_file")
        self.get_host().fs.put(str(p), "/path/to/put_dir")
        assert self.files[
            '/path/to/put_dir/put_file'].data == "data of put_file"


class TestTransfer(object):
    data = {
        "[ -d /path/to/dest_dir ]": (0, "", ""),
    }
    files = {
        "/path/to/file_to_transfer": "data to transfer",
    }

    @classmethod
    def setup_class(cls):
        fake_cmd_data(cls.data, cls.files)

    def get_host(self, ip='1.1.1.1'):
        h = Host(ip)
        h.add_user(User('root', '11111'))
        return h

    def test_transfer(self):
        self.get_host().fs.transfer(
            "/path/to/file_to_transfer", self.get_host("1.1.1.2"),
            "/path/to/dest_dir",
        )
        assert self.files[
            '/path/to/dest_dir/file_to_transfer'].data == "data to transfer"
