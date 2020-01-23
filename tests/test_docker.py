import pytest
from rrmngmnt import Host, User
from rrmngmnt.ssh import RemoteExecutorFactory


@pytest.fixture(scope='session')
def provisioned_hosts(docker_ip, docker_services):
    hosts = {}
    for h in ('ubuntu',):
        host = Host(docker_ip)
        host.add_user(User("root", "docker.io"))
        host.executor_factory = RemoteExecutorFactory(
            port=docker_services.port_for(h, 22))
        executor = host.executor()
        docker_services.wait_until_responsive(
            timeout=30.0, pause=1,
            check=lambda: executor.is_connective,
        )
        hosts[h] = host
    return hosts


@pytest.mark.skip(msg="Not enough tests in module to justify running")
def test_echo(provisioned_hosts):
    ubuntu_host = provisioned_hosts['ubuntu']
    ubuntu_host.executor().run_cmd(['echo', 'hello'])
