"""
Manage host power via ssh or ipmitool
"""
import socket
import subprocess
from rrmngmnt.service import Service

SSH_TYPE = "ssh"
IPMI_TYPE = "ipmi"

MANAGERS = {
    SSH_TYPE: "SSHPowerManager",
    IPMI_TYPE: "IPMIPowerManager"
}


class PowerManager(Service):
    """
    Base power management class
    """
    reboot_command = None
    poweron_command = None
    poweroff_command = None
    status_command = None

    def _exec_pm_command(self, command, *args):
        raise NotImplementedError("Must be implemented under child class")

    def restart(self, *args):
        """
        Reboot host
        """
        self._exec_pm_command(self.reboot_command, *args)

    def poweroff(self, *args):
        """
        Power off host
        """
        self._exec_pm_command(self.poweroff_command, *args)

    def poweron(self, *args):
        """
        Power on host
        """
        self._exec_pm_command(self.poweron_command, *args)

    def status(self, *args):
        """
        Get host power status
        """
        self._exec_pm_command(self.status_command, *args)


class SSHPowerManager(PowerManager):
    """
    SSH power management class
    """
    reboot_command = ["reboot"]
    poweroff_command = ["poweroff"]

    def _exec_pm_command(self, command, *args):
        try:
            t_command = list(command)
            t_command += args
            self.host.executor().run_cmd(
                t_command, tcp_timeout=20, io_timeout=20
            )
        except socket.timeout as e:
            self.logger.debug("Socket timeout: %s", e)
        except Exception as e:
            self.logger.debug("SSH exception: %s", e)

    def status(self, *args):
        """
        Get host power status
        """
        self.host.executor().run_cmd(['true'], tcp_timeout=5)

    def poweron(self, *args):
        """
        Power on host
        """
        raise NotImplementedError(
            "Not possible to power on host via ssh, "
            "please use ipmi power management"
        )


class IPMIPowerManager(PowerManager):
    """
    IPMI power management class
    """
    reboot_command = ["reset"]
    status_command = ["status"]
    poweron_command = ["on"]
    poweroff_command = ["off"]

    def __init__(self, h, pm_if_type, pm_address, user):
        """
        Initialize IPMIPowerManagement instance

        Args:
            pm_if_type (str): Ipmi interface type(lan, lanplus)
            pm_address (str): Power management address
            user (User): Instance of user with pm username and password
        """
        super(IPMIPowerManager, self).__init__(h)
        self.pm_if_type = pm_if_type
        self.pm_address = pm_address
        self.pm_user = user.name
        self.pm_password = user.password
        self.binary = [
            "ipmitool",
            "-I", self.pm_if_type,
            "-H", self.pm_address,
            "-U", self.pm_user,
            "-P", self.pm_password,
            "power"
        ]

    def _exec_pm_command(self, command, *args):
        t_command = list(command)
        t_command = self.binary + t_command
        t_command += args
        subprocess.call(t_command)
