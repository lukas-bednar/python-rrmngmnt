from rrmngmnt import Host, User

from tests.common import FakeExecutorFactory


def get_host(hostname='test-host'):
    return Host(hostname=hostname)


def test_executor_with_proxy_command():
    data = {
        'which systemctl': (0, '/usr/bin/systemctl', ''),
    }
    host = get_host()
    sock = 'my proxy command --stdio=true test-host 22'
    host_user = User(name="user", password="user")
    host.executor_user = host_user
    host.executor_factory = FakeExecutorFactory(
        cmd_to_data=data, files_content=None
    )
    host.executor_factory.sock = sock
    host.executor().run_cmd(['which', 'systemctl'])
