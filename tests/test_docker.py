import pytest
from rrmngmnt import Host, User

@pytest.fixture(scope='session')
def centos_host(docker_ip, docker_services):
    #host = Host(docker_services.ip_for('centos'))
    host = Host(docker_ip)
    host.add_user(User("root", "docker.io"))
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1,
        check=lambda: host.network.is_connective,
    )
    executor = host.executor()
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1,
        check=lambda: executor.is_connective,
    )
    return host

def test_echo(centos_host):
    centos_host.executor().run_cmd(['echo', 'hello'])
