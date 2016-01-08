from rrmngmnt.service import Service


class PackageManager(Service):
    """
    Base class which defines interface for package management.
    """
    binary = None
    exist_command_d = None
    install_command_d = None
    remove_command_d = None
    update_command_d = None

    @classmethod
    def is_available(cls, h):
        if not cls.binary:
            raise NotImplementedError("Name of binary file is not available.")
        rc, _, _ = h.executor().run_cmd(
            [
                'which', cls.binary,
            ]
        )
        return not rc

    def _run_command_on_host(self, cmd):
        """
        Run given command on host

        :param cmd: command to run
        :type cmd: list
        :return: True, if command success, otherwise False
        :rtype: bool
        """
        self.logger.info(
            "Execute command '%s' on host %s", " ".join(cmd), self.host
        )
        rc, out, err = self.host.executor().run_cmd(cmd)
        if rc:
            self.logger.error(
                "Failed to execute command '%s' on host %s; out: %s; err: %s",
                " ".join(cmd), self.host, out, err
            )
            return False
        return True

    def exist(self, package):
        """
        Check if package exist on host

        :param package: name of package
        :type package: str
        :return: True, if package exist, otherwise False
        :rtype: bool
        :raise: NotImplementedError
        """
        if not self.exist_command_d:
            raise NotImplementedError("There is no 'exist' command defined.")
        cmd = list(self.exist_command_d)
        cmd.append(package)
        self.logger.info(
            "Check if host %s have %s package", self.host, package
        )
        return self._run_command_on_host(cmd)

    def install(self, package):
        """
        Install package on host

        :param package: name of package
        :type package: str
        :return: True, if package installation success, otherwise False
        :rtype: bool
        :raise: NotImplementedError
        """
        if not self.install_command_d:
            raise NotImplementedError("There is no 'install' command defined.")
        cmd = list(self.install_command_d)
        cmd.append(package)
        if not self.exist(package):
            self.logger.info(
                "Install package %s on host %s", package, self.host
            )
            return self._run_command_on_host(cmd)
        self.logger.info(
            "Package %s already exist on host %s", package, self.host
        )
        return True

    def remove(self, package):
        """
        Remove package from host

        :param package: name of package
        :type package: str
        :return: True, if package removal success, otherwise False
        :rtype: bool
        :raise: NotImplementedError
        """
        if not self.remove_command_d:
            raise NotImplementedError("There is no 'remove' command defined.")
        cmd = list(self.remove_command_d)
        cmd.append(package)
        if self.exist(package):
            self.logger.info(
                "Erase package %s on host %s", package, self.host
            )
            return self._run_command_on_host(cmd)
        self.logger.info(
            "Package %s not exist on host %s", package, self.host
        )
        return True

    def update(self, packages=None):
        """
        Updated specified packages, or all available system updates
        if no packages are specified

        __author__ = "omachace"
        :param packages: Packages to be updated, if empty, update system
        :type packages: list
        :return: True when updates succeed, False otherwise
        :rtype: bool
        :raise: NotImplementedError
        """
        if not self.update_command_d:
            raise NotImplementedError("There is no 'update' command defined.")
        cmd = list(self.update_command_d)
        if packages:
            cmd.extend(packages)
            self.logger.info(
                "Update packages %s on host %s", packages, self.host
            )
        else:
            self.logger.info("Updating system on host %s", self.host)
        return self._run_command_on_host(cmd)


class YumPackageManager(PackageManager):
    """
    YUM package manager class
    """
    binary = 'yum'
    exist_command_d = (binary, 'list', 'installed')
    install_command_d = (binary, 'install', '-y')
    remove_command_d = (binary, 'remove', '-y')
    update_command_d = (binary, 'update', '-y')


class DnfPackageManager(PackageManager):
    """
    DNF package manager class
    """
    binary = 'dnf'
    exist_command_d = (binary, 'list', 'installed')
    install_command_d = (binary, 'install', '-y')
    remove_command_d = (binary, 'remove', '-y')
    update_command_d = (binary, 'update', '-y')


class RPMPackageManager(PackageManager):
    """
    RPM package manager class
    """
    binary = 'rpm'
    exist_command_d = (binary, '-q')
    install_command_d = (binary, '-i')
    remove_command_d = (binary, '-e')
    update_command_d = (binary, '-U')


class APTPackageManager(PackageManager):
    """
    APT package manager class
    """
    binary = 'apt'
    # FIXME: Once apt will return correct return codes fix this
    exist_command_d = (binary, 'list', '--installed', '|', 'grep')
    install_command_d = (binary, 'install', '-y')
    remove_command_d = (binary, 'remove', '-y')
    update_command_d = (binary, 'update', '-y')


class PackageManagerProxy(Service):
    """
    This class is helper to determine proper package manager for target system
    """
    managers = {
        "rpm": RPMPackageManager,
        "yum": YumPackageManager,
        "dnf": DnfPackageManager,
        "apt": APTPackageManager,
    }
    order = ('dnf', 'yum', 'apt', 'rpm')

    def __init__(self, h):
        super(PackageManagerProxy, self).__init__(h)
        self._manager = None

    def __call__(self, name):
        """
        This method allows you pick up specific package manager.

        host.package_manager('rpm').install(...)
        """
        try:
            return self.managers[name](self.host)
        except KeyError:
            raise ValueError("Unknown package manager: %s" % name)

    def __getattr__(self, name):
        """
        This method let you use implicit package manager.

        host.package_manager.install(...)
        """
        if self._manager is None:
            for name_manager in self.order:
                manager = self.managers[name_manager]
                if manager.is_available(self.host):
                    self.logger.info(
                        "Using %s package manager for %s",
                        name_manager, self.host,
                    )
                    self._manager = manager(self.host)
                    break
            else:
                self.logger.error(
                    "None of %s package managers is suitable for %s",
                    self.order, self.host,
                )
                raise RuntimeError(
                    "Can not determine package manager for %s" % self.host
                )
        return getattr(self._manager, name)
