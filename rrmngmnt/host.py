"""
This module define resource Host which is entry point to various services.
It should hold methods / properties which returns you Instance of specific
Service hosted on that Host.
"""
import copy
import os
import socket
import threading
import warnings

import netaddr
from rrmngmnt import errors
from rrmngmnt import power_manager
from rrmngmnt import ssh
from rrmngmnt.common import fqdn2ip
from rrmngmnt.filesystem import FileSystem
from rrmngmnt.network import Network
from rrmngmnt.operatingsystem import OperatingSystem
from rrmngmnt.package_manager import PackageManagerProxy
from rrmngmnt.resource import Resource
from rrmngmnt.service import Systemd, SysVinit, InitCtl
from rrmngmnt.storage import NFSService, LVMService


class Host(Resource):
    """
    This resource could represents any physical / virtual machine
    """

    # The purpose of inventory variable is keeping all instances of
    # interesting resources in single place.
    inventory = list()
    lock = threading.Lock()

    default_service_providers = [
        Systemd,
        SysVinit,
        InitCtl,
    ]

    class LoggerAdapter(Resource.LoggerAdapter):
        """
        Makes sure that all logs which are done via this class, has
        appropriate prefix. [IP]
        """
        def process(self, msg, kwargs):
            return (
                "[%s] %s" % (
                    self.extra['self'].ip,
                    msg,
                ),
                kwargs,
            )

    def __init__(self, ip, service_provider=None):
        """
        :param ip: IP address of machine or resolvable FQDN
        :type ip: string
        :param service_provider: system service handler
        :type service_provider: class which implement SystemService interface
        """
        super(Host, self).__init__()
        self._fqdn = None
        if not netaddr.valid_ipv4(ip):
            self._fqdn = ip
            ip = fqdn2ip(ip)
        self.ip = ip
        self.users = list()
        self._executor_user = None
        self._power_managers = dict()
        self._service_provider = service_provider
        self._package_manager = PackageManagerProxy(self)
        self.os = OperatingSystem(self)
        self.add()  # adding host to inventory

    def __str__(self):
        return "Host(%s)" % self.ip

    @classmethod
    def get(cls, ip):
        """
        Get host from inventory
        :param ip: IP address of machine or resolvable FQDN
        :type ip: str
        :return: host
        :rtype: Host
        """
        host = [h for h in cls.inventory if h.ip == ip or h.fqdn == ip]
        if not host:
            raise ValueError("There is no host with %s" % ip)
        return host[0]

    def add(self):
        """
        Add host to inventory
        """
        with self.lock:
            try:
                host = self.get(self.ip)
            except ValueError:
                pass
            else:
                self.inventory.remove(host)
            self.logger.debug("Adding host with ip '%s' to inventory", self.ip)
            self.inventory.append(self)

    @property
    def fqdn(self):
        return socket.getfqdn(self.ip) if not self._fqdn else self._fqdn

    def add_power_manager(self, pm_type, **init_params):
        """
        Add power power manager to host

        :param pm_type: power manager type(power_manager.SSH_TYPE for example)
        :type pm_type: str
        :param init_params: power manager init parameters
        :type init_params: dict
        """
        self._power_managers[pm_type] = getattr(
            power_manager, power_manager.MANAGERS[pm_type]
        )(self, **init_params)

    def get_power_manager(self, pm_type=None):
        """
        Get host power manager

        :param pm_type: power manager type(power_manager.SSH_TYPE for example)
        :type pm_type: str
        :return: instance of PowerManager
        :rtype: PowerManager
        :raises: Exception
        """
        if self._power_managers:
            if pm_type:
                if pm_type in self._power_managers:
                    return self._power_managers[pm_type]
                raise Exception(
                    "PM with type '%s' is not associated with the host %s" %
                    (pm_type, self)
                )
            else:
                return self._power_managers.values()[0]
        raise Exception("No PM is associated with the host %s" % self)

    def get_user(self, name):
        for user in self.users:
            if user.get_full_name() == name:
                return user
        raise Exception(
            "User '%s' is not assoiated with host %s" % (name, self)
        )

    def add_user(self, user):
        """
        Adds user to users collection, and tries remove duplicities.

        :param user: user to add
        :type user: instance of rrmngmnt.User
        """
        for u in self.users[:]:
            if user.get_full_name() == u.get_full_name():
                self.users.remove(u)
        self.users.append(user)

    def _set_executor_user(self, user):
        """
        This method explicitly set user which is used to execute commands
        on host.
        And adds user into users collection.

        :param user: specific user
        :type user: instance of rrmngmnt.User
        """
        self._executor_user = user
        self.add_user(user)

    def _get_executor_user(self):
        """
        The user which is supposed to be used for command execution.

        :return: user
        :rtype: instance of rrmngmnt.User
        """
        if self._executor_user:
            return copy.copy(self._executor_user)
        return copy.copy(self.root_user)

    executor_user = property(_get_executor_user, _set_executor_user)
    """
    You can set or get the user which is used to execute commands.
    For more info see _set_executor_user and _get_executor_user.
    """

    @property
    def root_user(self):
        return self.get_user('root')

    @property
    def package_manager(self):
        return self._package_manager

    @property
    def power_manager(self):
        return self.get_power_manager()

    def executor(self, user=None, pkey=False):
        """
        Gives you executor to allowing command execution

        :param user: the executed commands will be executed under this user.
                     when it is None, the default executor user is used,
                     see set_executor_user method for more info.
        """
        if user is None:
            user = self.executor_user
        return ssh.RemoteExecutor(user, self.ip, use_pkey=pkey)

    def run_command(
        self, command, input_=None, tcp_timeout=None, io_timeout=None,
        user=None, pkey=False,
    ):
        """
        Run command on host

        :param command: command
        :type command: list
        :param input_: input data
        :type input_: str
        :param tcp_timeout: tcp timeout
        :type tcp_timeout: float
        :param io_timeout: timeout for data operation (read/write)
        :type io_timeout: float
        :return: tuple of (rc, out, err)
        :rtype: tuple
        """
        self.logger.info("Executing command %s", ' '.join(command))
        rc, out, err = self.executor(user=user, pkey=pkey).run_cmd(
            command, input_=input_, tcp_timeout=tcp_timeout,
            io_timeout=io_timeout
        )
        if rc:
            self.logger.error(
                "Failed to run command %s ERR: %s OUT: %s", command, err, out
            )
        return rc, out, err

    def copy_to(self, resource, src, dst, mode=None, ownership=None):
        """
        Copy to host from another resource

        :param resource: resource to copy from
        :type resource: instance of Host
        :param src: path to source
        :type src: str
        :param dst: path to destination
        :type dst: str
        :param mode: file permissions
        :type mode: str
        :param ownership: file ownership(ex. ('root', 'root'))
        :type ownership: tuple
        """
        warnings.warn(
            "This method is deprecated and will be removed. "
            "Use Host.fs.transfer instead."
        )
        with resource.executor().session() as resource_session:
            with self.executor().session() as host_session:
                with resource_session.open_file(src, 'rb') as resource_file:
                    with host_session.open_file(dst, 'wb') as host_file:
                        host_file.write(resource_file.read())
        if mode:
            self.fs.chmod(path=dst, mode=mode)
        if ownership:
            self.fs.chown(dst, *ownership)

    def _create_service(self, name, timeout):
        for provider in self.default_service_providers:
            try:
                service = provider(self, name, timeout=timeout)
            except provider.CanNotHandle:
                pass
            else:
                self.logger.info(
                    "Setting %s as service provider", provider
                )
                self._service_provider = provider
                break
        else:
            msg = (
                "Can not find suitable service provider: %s" %
                self.default_service_providers
            )
            self.logger.error(msg)
            raise Exception(msg)
        return service

    def service(self, name, timeout=None):
        """
        Create service provider for desired service

        :param name: service name
        :type name: string
        :param timeout: expected time to complete operations
        :type timeout: int
        :return: service provider for desired service
        :rtype: instance of SystemService
        """
        if self._service_provider is None:
            # we need to pick up service provider,
            # assume same provider for all next services.
            service = self._create_service(name, timeout)
            self._service_provider = service.__class__
            return service
        try:
            return self._service_provider(self, name, timeout=timeout)
        except self._service_provider.CanNotHandle:
            # it may happen there is some special service
            # which needs different provider.
            # try to select different one
            service = self._create_service(name, timeout)
            self._service_provider = service.__class__
            return service

    def get_ssh_public_key(self, user=None):
        """
        Get SSH public key

        :param user: what user to get ssh keys for, default is root
        :type user: instance of rrmngmnt.User
        :return: SSH public key
        :rtype: str
        """
        if user is None:
            user = copy.copy(self.root_user)
        id_rsa_pub = ssh.ID_RSA_PUB % os.path.expanduser(
            "~%s" % user.name
        )
        id_rsa_prv = ssh.ID_RSA_PRV % os.path.expanduser(
            "~%s" % user.name
        )
        if not self.fs.exists(id_rsa_pub):
            # Generating SSH key if not exist
            cmd = [
                "ssh-keygen", "-q", "-t", "rsa", "-N", '', "-f",
                id_rsa_prv
            ]
            rc = self.run_command(cmd)[0]
            if rc:
                return ""

        cmd = ["cat", id_rsa_pub]
        return self.run_command(cmd)[1]

    def remove_remote_host_ssh_key(self, remote_host, user=None):
        """
        Remove remote host keys (ip, fqdn) from KNOWN_HOSTS file

        :param remote_host: Remote host resource object
        :type remote_host: Host
        :param user: what user to remove ssh keys for, default is root
        :type user: instance of rrmngmnt.User
        :return: True/False
        :rtype: bool
        """
        if user is None:
            user = copy.copy(self.root_user)
        known_hosts = ssh.KNOWN_HOSTS % os.path.expanduser(
            "~%s" % user.name
        )
        ssh_keygen = ["ssh-keygen", "-R"]
        if self.fs.exists(known_hosts):
            # Remove old keys from local host if any
            for i in [remote_host.ip, remote_host.fqdn]:
                rc = self.run_command(ssh_keygen + [i])[0]
                if rc:
                    return False
        return True

    def remove_remote_key_from_authorized_keys(self, user=None):
        """
        Remove remote ssh key from AUTHORIZED_KEYS file

        :param user: what user to remove from authorized_keys, default is root
        :type user: instance of rrmngmnt.User
        :return: True/False
        :rtype: bool
        """
        if user is None:
            user = copy.copy(self.root_user)
        authorized_keys = ssh.AUTHORIZED_KEYS % os.path.expanduser(
            "~%s" % user.name
        )
        local_fqdn = self.fqdn
        cmd = ["sed", "-c", "-i", "/%s/d" % local_fqdn, authorized_keys]
        rc = self.run_command(cmd)[0]
        if rc:
            return False
        return True

    def get_os_info(self):
        """
        Get OS info (Distro, version and code name)

        :return: Results {dist: , ver: , name:}
            example:
            {'dist': 'Red Hat Enterprise Linux Server',
             'name': 'Maipo',
             'ver': '7.1'}
        :rtype: dict
        """
        warnings.warn(
            "This method is deprecated and will be removed. "
            "Use Host.os.distribution instead."
        )
        values = ["dist", "ver", "name"]
        try:
            return {
                'dist': self.os.distribution.distname,
                'ver': self.os.distribution.version,
                'name': self.os.distribution.id,
            }
        except errors.CommandExecutionFailure:
            return dict([(x, None) for x in values])

    def get_network(self):
        return Network(self)

    @property
    def network(self):
        return self.get_network()

    @property
    def nfs(self):
        return NFSService(self)

    @property
    def lvm(self):
        return LVMService(self)

    @property
    def fs(self):
        return FileSystem(self)

    @property
    def ssh_public_key(self):
        return self.get_ssh_public_key()

    @property
    def os_info(self):
        return self.get_os_info()

    def create_script(
        self, content, name_of_script, destination_path
    ):
        """
        Create script on resource

        :param content: content of the script
        :type content: str
        :param name_of_script: name of script to create
        :type name_of_script: str
        :param destination_path: directory on host to copy script
        :type destination_path: str
        :returns: Script absolute path, if creation success,
        otherwise empty string
        :rtype: str
        """
        warnings.warn(
            "This method is deprecated and will be removed. "
            "Use Host.fs.create_script instead."
        )
        dst = os.path.join(destination_path, name_of_script)
        try:
            self.fs.create_script(content, dst)
        except errors.CommandExecutionFailure:
            return ""
        return dst

    def is_connective(self, tcp_timeout=20.0):
        """
        Check if host is connective via ssh

        :param tcp_timeout: time to wait for response
        :type tcp_timeout: float
        :return: True if host is connective, False otherwise
        :rtype: bool
        """
        warnings.warn(
            "This method is deprecated and will be removed. "
            "Use Host.executor().is_connective() instead."
        )
        return self.executor().is_connective(tcp_timeout=tcp_timeout)
