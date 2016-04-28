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

    def get_release_str(self):
        cmd = ['cat', '/etc/system-release']
        executor = self.host.executor()
        rc, out, err = executor.run_cmd(cmd)
        if rc:
            raise errors.CommandExecutionFailure(
                executor, cmd, rc,
                "Failed to obtain release string: {0}".format(err)
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

        :raises: UnsupportedOperation
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

        :return: Results tuple(distname, version, id}
            example:
            Distribution(
              distname='Red Hat Enterprise Linux Server',
              id='Maipo',
              version'='7.1'
            )
        :rtype: namedtuple Distribution
        """
        values = ["distname", "version", "id"]
        cmd = [
            "python", "-c",
            "import platform;print(','.join(platform.linux_distribution()))"
        ]
        executor = self.host.executor()
        rc, out, err = executor.run_cmd(cmd)
        if rc:
            raise errors.CommandExecutionFailure(
                executor, cmd, rc,
                "Failed to obtain release info: {0}".format(err)
            )
        Distribution = namedtuple('Distribution', values)
        return Distribution(*[i.strip() for i in out.split(",")])

    @property
    def distribution(self):
        if not self._dist:
            self._dist = self.get_distribution()
        return self._dist
