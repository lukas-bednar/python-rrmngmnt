# python-rrmngmnt
Remote Resources MaNaGeMeNT
[![Build Status](https://travis-ci.org/rhevm-qe-automation/python-rrmngmnt.svg?branch=master)](https://travis-ci.org/rhevm-qe-automation/python-rrmngmnt)

## Intro
This tool helps you manage remote machines and services running on that.
It is targeted to Linux based machines. All is done via SSH connection,
that means SSH server must be running there already.
```
from rrmngmnt import Host, RootUser

h = Host("10.11.12.13")
h.users.append(RootUser('123456'))
exec = h.executor()
print exec.run_cmd(['echo', 'Hello World'])
```

## Features
List of provided interfaces to manage resources on machine, and examples.

### Filesystem
Basic file operations, you can find there subset of python 'os' module related
to files.
```
print h.fs.exists("/path/to/file")
h.fs.chown("/path/to/file", "root", "root")
h.fs.chmod("/path/to/file", "644")
h.fs.unlink("/path/to/file")
```

### Network
It allows to manage network configuration.
```
print h.network.hostname
h.network.hostname = "my.machine.org"
print h.network.all_interfaces()
print h.network.list_bridges()
```

### Package Management
It encapsulates various package managements. It is able to determine
which package management to use. You can still specify package management
explicitly.

Implemented managements:

  * APT
  * YUM
  * DNF
  * RPM

```
# install htop package using implicit management
h.package_management.install('htop')
# remove htop package using rpm explicitly
h.package_management('rpm').remove('htop')
```

### System Services
You can toggle system services, it encapsulates various service managements.
It is able to determine which service management to use in most cases.

Implemented managements:

  * Systemd
  * SysVinit
  * InitCtl

```
if h.service('httpd').status():
    h.service('httpd').stop()
if h.service('httpd').is_enabled():
    h.service('httpd').disable()
```

### Storage Management
It is in PROGRESS state. Planed are NFS & LVM services.

## Requires
* paramiko
* netaddr

### Power Management
Give you possibility to control host power state, you can restart, poweron,
poweroff host and get host power status.

Implemented managements:

  * SSH
  * IPMI

```
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
```

## Install
```
python setup.py devop
```
