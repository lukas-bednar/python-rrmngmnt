import pytest

from rrmngmnt import Host, User, power_manager
from .common import FakeExecutor

PM_TYPE = 'lanplus'
PM_ADDRESS = 'test-mgmt.test'
PM_USER = 'test-user'
PM_PASSWORD = 'test-password'
IPMI_COMMAND = (
    'ipmitool -I {pm_type} -H {pm_address} -U {pm_user} -P {pm_password} power'
).format(
    pm_type=PM_TYPE,
    pm_address=PM_ADDRESS,
    pm_user=PM_USER,
    pm_password=PM_PASSWORD
)

host_executor = Host.executor


def teardown_module():
    Host.executor = host_executor


def fake_cmd_data(cmd_to_data):
    def executor(self, user=None, pkey=False):
        e = FakeExecutor(user, self.ip)
        e.cmd_to_data = cmd_to_data.copy()
        return e
    Host.executor = executor


class TestPowerManager(object):
    host = None
    data = {
        'reboot': (0, '', ''),
        'poweroff': (0, '', ''),
        'true': (0, '', ''),
        '{0} status'.format(IPMI_COMMAND): (0, '', ''),
        '{0} reset'.format(IPMI_COMMAND): (0, '', ''),
        '{0} on'.format(IPMI_COMMAND): (0, '', ''),
        '{0} off'.format(IPMI_COMMAND): (0, '', ''),
    }

    @classmethod
    def setup_class(cls):
        fake_cmd_data(cls.data)
        cls.host = cls.get_host()

    @staticmethod
    def get_host(ip='1.1.1.1'):
        return Host(ip)


class TestSSHPowerManager(TestPowerManager):
    @classmethod
    def get_ssh_power_manager(cls):
        host = cls.get_host()
        host.add_power_manager(pm_type=power_manager.SSH_TYPE)
        return host.get_power_manager(pm_type=power_manager.SSH_TYPE)

    def test_reboot_positive(self):
        self.get_ssh_power_manager().restart()

    def test_poweroff_positive(self):
        self.get_ssh_power_manager().poweroff()

    def test_status_positive(self):
        self.get_ssh_power_manager().status()

    def test_poweron_negative(self):
        with pytest.raises(NotImplementedError):
            self.get_ssh_power_manager().poweron()


class TestIPMIPowerManager(TestPowerManager):

    @staticmethod
    def fake_exec_pm_command():
        def exec_pm_command(self, command, *args):
            t_command = list(command)
            t_command = self.binary + t_command
            t_command += args
            self.host.executor().run_cmd(t_command)
        power_manager.IPMIPowerManager._exec_pm_command = exec_pm_command

    @classmethod
    def setup_class(cls):
        super(TestIPMIPowerManager, cls).setup_class()
        cls.fake_exec_pm_command()

    @classmethod
    def get_ipmi_power_manager(cls):
        pm_user = User(name=PM_USER, password=PM_PASSWORD)
        ipmi_init_params = {
            'pm_if_type': PM_TYPE,
            'pm_address': PM_ADDRESS,
            'user': pm_user
        }
        host = cls.get_host()
        host.add_power_manager(
            pm_type=power_manager.IPMI_TYPE, **ipmi_init_params
        )
        return host.get_power_manager(pm_type=power_manager.IPMI_TYPE)

    def test_reboot_positive(self):
        self.get_ipmi_power_manager().restart()

    def test_poweroff_positive(self):
        self.get_ipmi_power_manager().poweroff()

    def test_status_positive(self):
        self.get_ipmi_power_manager().status()

    def test_poweron_positive(self):
        self.get_ipmi_power_manager().poweron()
