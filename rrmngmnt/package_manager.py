from rrmngmnt import errors
from rrmngmnt.service import Service

PIPE_GREP_COMMAND_D = ('|', 'grep', '-E')
PIPE_XARGS_COMMAND_D = ('|', 'xargs')


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

        Args:
            cmd (list): Command to run

        Returns:
            bool: True, if command success, otherwise false
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

        Args:
            package (str): Name of package

        Returns:
            bool: True, if package exist, otherwise false

        Raises:
            NotImplementedError
        """
        if not self.exist_command_d:
            raise NotImplementedError("There is no 'exist' command defined.")
        cmd = list(self.exist_command_d)
        cmd.append(package)
        self.logger.info(
            "Check if host %s have %s package", self.host, package
        )
        return self._run_command_on_host(cmd)

    def list_(self):
        """
        List installed packages on host

        Returns:
            list: Installed packages

        Raises:
            NotImplementedError, CommandExecutionFailure
        """
        if not self.list_command_d:
            raise NotImplementedError(
                "There is no 'list_' command defined."
            )
        cmd = self.list_command_d
        self.logger.debug(
            "Getting all instaled packages from host %s", self.host
        )
        rc, out, err = self.host.executor().run_cmd(cmd)
        if not rc:
            return out.split('\n')
        self.logger.error(
            "Failed to get installed packages on host %s, rc: %s, err: %s",
            self.host, rc, err
        )
        raise errors.CommandExecutionFailure(
            cmd=cmd, executor=self.host.executor, rc=rc, err=err
        )

    def install(self, package):
        """
        Install package on host

        Args:
            package (str): Name of package

        Returns:
            bool: True, if package installation success, otherwise false

        Raises:
            NotImplementedError
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

    def remove(self, package, pattern=False):
        """
        Remove package from host, or packages which match pattern if pattern
        is set to True

        Args:
            pattern (bool): If true package name is pattern
            package (str): Name of package or extended regular expression
                pattern take a look at -e option in man grep

        Returns:
            bool: True, if package(s) removal success, otherwise false

        Raises:
            NotImplementedError
        """
        if not self.remove_command_d:
            raise NotImplementedError("There is no 'remove' command defined.")
        if pattern and not self.list_command_d:
            raise NotImplementedError(
                "list_ is not implemented!"
            )

        cmd = list(self.remove_command_d)
        package_exists = False
        if pattern:
            self.logger.info(
                "Erase packages which match pattern %s on host %s", package,
                self.host
            )
            grep_xargs_command = (
                list(PIPE_GREP_COMMAND_D) + ['\'%s\'' % package] +
                list(PIPE_XARGS_COMMAND_D)
            )
            remove_pattern_command = (
                list(self.list_command_d) + grep_xargs_command + cmd
            )
            if not self._run_command_on_host(remove_pattern_command):
                return False
            return True

        package_exists = self.exist(package)
        if not package_exists:
            self.logger.info(
                "Package %s does not exist on host %s", package, self.host
            )
            return True

        self.logger.info(
            "Erase package %s on host %s", package, self.host
        )
        cmd.append(package)
        return self._run_command_on_host(cmd)

    def update(self, packages=None):
        """
        Updated specified packages, or all available system updates
        if no packages are specified

        __author__ = "omachace"

        Args:
            packages (list): Packages to be updated, if empty, update system

        Returns:
            bool: True when updates succeed, false otherwise

        Raises:
            NotImplementedError
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
    exist_command_d = (binary, '-q', 'list', 'installed')
    list_command_d = exist_command_d + (
        '|', 'cut', '-d', ' ', '-f', '1', '|', 'sed', '\'/^$/d\'', '|', 'tail',
        '-n', '+2'
    )
    install_command_d = (binary, 'install', '-y')
    remove_command_d = (binary, 'remove', '-y')
    update_command_d = (binary, 'update', '-y')


class DnfPackageManager(PackageManager):
    """
    DNF package manager class
    """
    binary = 'dnf'
    exist_command_d = (binary, '-q', 'list', 'installed')
    list_command_d = exist_command_d + (
        '|', 'cut', '-d', ' ', '-f', '1', '|', 'sed', '\'/^$/d\'', '|', 'tail',
        '-n', '+2'
    )
    list_command_d = exist_command_d
    install_command_d = (binary, 'install', '-y')
    remove_command_d = (binary, 'remove', '-y')
    update_command_d = (binary, 'update', '-y')


class RPMPackageManager(PackageManager):
    """
    RPM package manager class
    """
    binary = 'rpm'
    exist_command_d = (binary, '-q')
    list_command_d = (binary, '-qa')
    install_command_d = (binary, '-i')
    remove_command_d = (binary, '-e')
    update_command_d = (binary, '-U')


class APTPackageManager(PackageManager):
    """
    APT package manager class
    """
    binary = 'apt'
    binary_base = 'dpkg'
    list_command_d = (
        binary_base, '--get-selections', '|', 'grep', 'install', '|', 'cut',
        '-f1'
    )
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
