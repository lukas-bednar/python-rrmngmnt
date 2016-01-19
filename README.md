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
Implements APT, YUM, DNF and RPM package managements. It is able to determine
which package management to use. You can still specify package management
explicitly.
```
h.package_management.install('htop')
h.package_management('rpm').remove('htop')
```

### System Services
You can toggle system services, it implements Systemd, SysVinit and InitCtl.
It is able to determine which service management to use in most cases.
```
if h.service('httpd').status():
    h.service('httpd').stop()
if h.service('httpd').is_enabled():
    h.service('httpd').disable()
```

## Requires
* paramiko
* netaddr

## Install
```
python setup.py devop
```
