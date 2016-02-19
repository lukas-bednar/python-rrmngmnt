"""
Manage host power via ssh or ipmitool
"""
import socket
import subprocess
from rrmngmnt.service import Service


class PowerManager(Service):
    """
    Base power management class
    """
    reboot_command = None
    poweron_command = None
    poweroff_command = None

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


class SSHPowerManager(PowerManager):
    """
    SSH power management class
    """
    reboot_command = ["reboot"]
    poweroff_command = ["poweroff"]

    def _exec_pm_command(self, command, *args):
        try:
            command += args
            self.host.executor().run_cmd(command)
        except socket.timeout as e:
            self.logger.debug("Socket timeout: %s", e)
        except Exception as e:
            self.logger.debug("SSH exception: %s", e)

    def poweron(self, *args):
        """
        Power on host
        """
        raise RuntimeError(
            "Not possible to power on host via ssh, "
            "please use ipmi power management"
        )


class IPMIPowerManager(PowerManager):
    """
    IPMI power management class
    """
    reboot_command = ["reset"]
    poweron_command = ["on"]
    poweroff_command = ["off"]

    def __init__(self, h, pm_if_type, pm_address, pm_user, pm_password):
        """
        Initialize IPMIPowerManagement instance

        :param pm_if_type: ipmi interface type(lan, lanplus)
        :type pm_if_type: str
        :param pm_address: power management address
        :type pm_address: str
        :param pm_user: power management user
        :type pm_user: str
        :param pm_password: power management password
        :type pm_password: str
        """
        super(IPMIPowerManager, self).__init__(h)
        self.pm_if_type = pm_if_type
        self.pm_address = pm_address
        self.pm_user = pm_user
        self.pm_password = pm_password
        self.binary = [
            "ipmitool",
            "-I", self.pm_if_type,
            "-H", self.pm_address,
            "-U", self.pm_user,
            "-P", self.pm_password,
            "power"
        ]

    def _exec_pm_command(self, command, *args):
        command = self.binary + command
        command += args
        subprocess.call(command)


class PowerManagerProxy(Service):
    """
    This class helps to determine proper power manager for the target system
    """
    managers = {
        "ipmi": IPMIPowerManager,
        "ssh": SSHPowerManager,
    }
    order = ("ipmi", "ssh")

    def __init__(self, h):
        super(PowerManagerProxy, self).__init__(h)
        self._manager = None

    def __call__(self, name):
        """
        This method allows you pick up specific power manager.

        power_manager = host.power_manager('ipmi')(init_params).restart()
        """
        try:
            return self.managers[name]
        except KeyError:
            raise ValueError("Unknown power manager: %s" % name)
