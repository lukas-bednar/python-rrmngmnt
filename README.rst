python-rrmngmnt
===============

Remote Resources MaNaGeMeNT

Intro
-----

This tool helps you manage remote machines and services running on that.
It is targeted to Linux based machines. All is done via SSH connection,
that means SSH server must be running there already.

.. code:: python

    from rrmngmnt import Host, RootUser

    h = Host("10.11.12.13")
    h.users.append(RootUser('123456'))

    exec = h.executor()
    # Run with sudo
    exec = h.executor(sudo=True)

    print exec.run_cmd(['echo', 'Hello World'])

Using SSH key for authentication

.. code:: python

    from rrmngmnt import Host, UserWithPKey

    h = Host("10.11.12.13")
    user = UserWithPKey('user', '/path/to/pkey'))

    h.executor(user).run_cmd(['echo', 'Use pkey for auth instead of password'])

Using SSH key with disabled algorithms on paramiko SSHClient connect (Used when connecting to machines using old SSH)

.. code:: python

    from rrmngmnt import Host, UserWithPKey, RemoteExecutorFactory

    h = Host("10.11.12.13")
    h.executor_factory = RemoteExecutorFactory(disabled_algorithms=dict(pubkeys=['rsa-sha2-256', 'rsa-sha2-512'])
    user = UserWithPKey('user', '/path/to/pkey'))

    h.executor(user).run_cmd(['echo', 'Use pkey and disabled algorithms for old openSSH connection'])

Using with SSH ProxyCommand
.. code:: python

    proxy_command = 'some proxy command'
    h = Host(hostname="hostname")
    host.executor_factory = ssh.RemoteExecutorFactory(sock=proxy_command)
    h.executor(user).run_cmd(['echo', 'Use SSH with ProxyCommand'])

Features
--------

List of provided interfaces to manage resources on machine, and
examples.

Filesystem
~~~~~~~~~~

Basic file operations, you can find there subset of python 'os' module
related to files.

.. code:: python

    print h.fs.exists("/path/to/file")
    h.fs.chown("/path/to/file", "root", "root")
    h.fs.chmod("/path/to/file", "644")
    h.fs.unlink("/path/to/file")

In additional there are methods to fetch / put file from / to remote system
to / from local system.

.. code:: python

    h.fs.get("/path/to/remote/file", "/path/to/local/file/or/target/dir")
    h.fs.put("/path/to/local/file", "/path/to/remote/file/or/target/dir")

There is one special method which allows transfer file between hosts.

.. code:: python

    h1.fs.transfer(
        "/path/to/file/on/h1",
        h2, "/path/to/file/on/h2/or/target/dir",
    )

You can also mount devices.

.. code:: python

    with h.fs.mount_point(
        '//example.com/share', opts='ro,guest',
        fstype='cifs', target='/mnt/netdisk'
    ) as mp:
        h.fs.listdir(mp.target) # list mounted directory
        mp.remount('rw,sync,guest') # remount with different options
        h.fs.touch('%s/new_file' % mp.target) # touch file

Firewall
~~~~~~~~

Allows to manage firewall configurarion. Check which firewall service is
running on host (firewalld/iptables) and make configure this service.

.. code:: python

    h.firewall.is_active('iptables')
    h.firewall.chain('OUTPUT').list_rules()
    h.firewall.chain('OUTPUT').add_rule('1.1.1.1', 'DROP')


Network
~~~~~~~

It allows to manage network configuration.

.. code:: python

    print h.network.hostname
    h.network.hostname = "my.machine.org"
    print h.network.all_interfaces()
    print h.network.list_bridges()

Package Management
~~~~~~~~~~~~~~~~~~

It encapsulates various package managements. It is able to determine
which package management to use. You can still specify package management
explicitly.


Implemented managements:

-  APT
-  YUM
-  DNF
-  RPM

.. code:: python

    # install htop package using implicit management
    h.package_management.install('htop')
    # remove htop package using rpm explicitly
    h.package_management('rpm').remove('htop')

System Services
~~~~~~~~~~~~~~~

You can toggle system services, it encapsulates various service managements.
It is able to determine which service management to use in most cases.


Implemented managements:

-  Systemd
-  SysVinit
-  InitCtl

.. code:: python

    if h.service('httpd').status():
        h.service('httpd').stop()
    if h.service('httpd').is_enabled():
        h.service('httpd').disable()

Operating System Info
~~~~~~~~~~~~~~~~~~~~~

Host provide ``os`` attribute which allows obtain basic operating
system info.
Note that ``os.release_info`` depends on systemd init system.

.. code:: python

    print h.os.distribution
    # Distribution(distname='Fedora', version='23', id='Twenty Three')

    print h.os.release_info
    # {'HOME_URL': 'https://fedoraproject.org/',
    #  'ID': 'fedora',
    #  'NAME': 'Fedora',
    #  'PRETTY_NAME': 'Fedora 23 (Workstation Edition)',
    #  'VARIANT': 'Workstation Edition',
    #  'VARIANT_ID': 'workstation',
    #  'VERSION': '23 (Workstation Edition)',
    #  'VERSION_ID': '23',
    #  ...
    # }

    print h.os.release_str
    # Fedora release 23 (Twenty Three)

Storage Management
~~~~~~~~~~~~~~~~~~

It is in PROGRESS state. Planed are NFS & LVM services.

Power Management
~~~~~~~~~~~~~~~~

Give you possibility to control host power state, you can restart,
poweron, poweroff host and get host power status.


Implemented managements:

-  SSH
-  IPMI

.. code:: python

    ipmi_user = User(pm_user, pm_password)
    ipmi_params = {
        'pm_if_type': 'lan',
        'pm_address': 'test-mgmt.testdomain',
        'user': ipmi_user
    }
    h.add_power_manager(
        power_manager.IPMI_TYPE, **ipmi_params
    )
    # restart host via ipmitool
    h.power_manager.restart()

Requires
--------

-  paramiko
-  netaddr
-  six

Install
-------

.. code:: sh

    python setup.py devop

Test
----

.. code:: sh

    tox

