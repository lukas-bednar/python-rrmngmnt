"""
This module provides interface to obtain operating system information.
"""
from collections import namedtuple
from rrmngmnt.service import Service
from rrmngmnt import errors


class OperatingSystem(Service):

    def __init__(self, host):
        super(OperatingSystem, self).__init__(host)
        self._release_str = None
        self._release_info = None
        self._dist = None
        self._kernel = None
        self._timezone = None

    def _exec_command(self, cmd, err_msg=None):
        host_executor = self.host.executor()
        rc, out, err = host_executor.run_cmd(cmd)
        if err_msg:
            err = "{err_msg}: {err}".format(err_msg=err_msg, err=err)
        if rc:
            raise errors.CommandExecutionFailure(
                executor=host_executor, cmd=cmd, rc=rc, err=err
            )
        return out

    def get_release_str(self):
        cmd = ['cat', '/etc/system-release']
        out = self._exec_command(
            cmd=cmd, err_msg="Failed to obtain release string"
        )
        return out.strip()

    @property
    def release_str(self):
        if not self._release_str:
            self._release_str = self.get_release_str()
        return str(self._release_str)

    def get_release_info(self):
        """
        /etc/os-release became to be standard on systemd based operating
        systems.

        It might raise exception in case the systemd is not deployed on system.

        Raises:
            UnsupportedOperation
        """
        os_release_file = '/etc/os-release'
        cmd = ['cat', os_release_file]
        executor = self.host.executor()
        rc, out, err = executor.run_cmd(cmd)
        if rc:
            try:
                if not self.host.fs.exists(os_release_file):
                    raise errors.UnsupportedOperation(
                        self.host, "OperatingSystem.release_info",
                        "Requires 'systemd' based operating system.",
                    )
            except errors.UnsupportedOperation:
                raise
            except Exception:
                pass
            raise errors.CommandExecutionFailure(
                executor, cmd, rc,
                "Failed to obtain release info, system doesn't follow "
                "systemd standards: {0}".format(err)
            )
        release_info = dict()
        for line in out.strip().splitlines():
            values = line.split("=", 1)
            if len(values) != 2:
                continue
            release_info[values[0].strip()] = values[1].strip(" \"'")
        return release_info

    @property
    def release_info(self):
        if not self._release_info:
            self._release_info = self.get_release_info()
        return self._release_info.copy()

    def get_distribution(self):
        """
        Get OS info (Distro, version and code name)

        Returns:
            namedtuple Distribution: Results tuple(distname, version, id}

        Examples:
             distribution(
                    distname='red hat enterprise linux server',
                    id='maipo',
                    version'='7.1'
                    )

        """
        values = ["distname", "version", "id"]
        cmd = [
            "python", "-c",
            "import platform;print(','.join(platform.linux_distribution()))"
        ]
        out = self._exec_command(
            cmd=cmd, err_msg="Failed to obtain release info"
        )
        Distribution = namedtuple('Distribution', values)
        return Distribution(*[i.strip() for i in out.split(",")])

    @property
    def distribution(self):
        if not self._dist:
            self._dist = self.get_distribution()
        return self._dist

    def get_kernel_info(self):
        """
        Get kernel info (release, version and type)

        Returns:
            namedtuple Kernel: Results tuple(release, version and type)

        Examples:
             kernel(
                    release='4.18.0-135.el8.x86_64',
                    version='#1 SMP Fri Aug 16 19:31:40 UTC 2019',
                    type'='x86_64'
                    )
        """
        values = ["release", "version", "type"]
        cmd = ["uname", "-r", ";", "uname", "-v", ";", "uname", "-m"]
        out = self._exec_command(
            cmd=cmd, err_msg="Failed to obta kernel info"
        )
        Kernel = namedtuple('Kernel', values)
        return Kernel(*[i.strip() for i in out.strip().split("\n")])

    @property
    def kernel_info(self):
        if not self._kernel:
            self._kernel = self.get_kernel_info()
        return self._kernel

    def get_timezone(self):
        """
        Get timezone (name and offset)

        Returns:
            namedtuple Timezone: Results tuple(name and offset)

        Examples:
             kernel(name='IDT', offset='+0300')
        """
        values = ["name", "offset"]
        cmd = ["date", "+%Z\\", "%z"]
        out = self._exec_command(
            cmd=cmd, err_msg="Failed to obtain timezone info"
        )
        Timezone = namedtuple('Timezone', values)
        return Timezone(*[i.strip() for i in out.split()])

    @property
    def timezone(self):
        if not self._timezone:
            self._timezone = self.get_timezone()
        return self._timezone

    def stat(self, path):
        """
        Get file or directory stats

        Returns:
            collections.namedtuple: File stats
        """
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
        posix_stat_result = namedtuple(
            "posix_stat_result", type_map.keys()
        )

        cmd = [
            "stat",
            "-c",
            ",".join(["%s=%s" % (k, v[0]) for k, v in type_map.items()]),
            path
        ]
        out = self._exec_command(cmd=cmd)
        out = out.strip().split(',')

        data = {}

        for pair in out:
            key, value = pair.split('=')
            data[key] = type_map[key][1](value)

        return posix_stat_result(**data)

    def get_file_permissions(self, path):
        """
        Get file permissions

        Returns:
            str: File permission in octal form(example 0644)
        """
        cmd = ["stat", "-c", "%a", path]
        return self._exec_command(cmd=cmd).strip()

    def get_file_owner(self, path):
        """
        Get file user and group owner name

        Returns:
            list: File user and group owner names(example ['root', 'root'])
        """
        cmd = ["stat", "-c", "%U %G", path]
        return self._exec_command(cmd=cmd).split()

    def user_exists(self, user_name):
        """
        Check if user exist on system

        Args:
            user_name (str): User name

        Returns:
            bool: True, if user exist, otherwise false
        """
        try:
            cmd = ["id", "-u", user_name]
            self._exec_command(cmd=cmd)
        except errors.CommandExecutionFailure:
            return False
        return True

    def group_exists(self, group_name):
        """
        Check if group exist on system

        Args:
            group_name (str): Group name

        Returns:
            bool: True, if group exist, otherwise false

        """
        try:
            cmd = ["id", "-g", group_name]
            self._exec_command(cmd=cmd)
        except errors.CommandExecutionFailure:
            return False
        return True
