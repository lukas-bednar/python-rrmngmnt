class GeneralResourceError(Exception):
    """
    Use this class as base for all new exceptions types in this module.
    """


class CommandExecutionFailure(GeneralResourceError):
    """
    This exception is used in cases where executed command failed unexpectly.
    """
    def __init__(self, executor, cmd, rc, err):
        """
        Args:
            executor (RemoteExecutor): executor used for execution
            cmd (list): executed command
            rc (int): return code
            err (str): standard error output if provided
        """
        super(CommandExecutionFailure, self).__init__(executor, cmd, rc, err)

    @property
    def executor(self):
        return self.args[0]

    @property
    def cmd(self):
        return self.args[1]

    @property
    def rc(self):
        return self.args[2]

    @property
    def err(self):
        return self.args[3]

    def __str__(self):
        return "Command execution failure, %s@%s/%s, %s, RC: %s, ERR: %s" % (
            self.executor.user.name, self.executor.address,
            self.executor.user.password, self.cmd, self.rc, self.err,
        )


class UnsupportedOperation(GeneralResourceError):
    """
    Some of operation doesn't have to be available on all platforms.
    In such cases this exception is raised.
    """
    def __init__(self, host, operation, reason):
        """
        Args:
            host (Host): relevant host
            operation (str): name of unsupported operation
            reason (str): message
        """
        super(UnsupportedOperation, self).__init__(host, operation, reason)

    @property
    def host(self):
        return self.args[0]

    @property
    def operation(self):
        return self.args[1]

    @property
    def reason(self):
        return self.args[2]

    def __str__(self):
        return "Operation '{0}' is not supported for {1}: {2}".format(
            self.operation, self.host, self.reason
        )


class FileSystemError(GeneralResourceError):
    pass


class MountError(FileSystemError):
    def __init__(self, mp):
        self.mp = mp


class FailCreateTemp(FileSystemError):
    pass


class MountCommandError(MountError):
    def __init__(self, mp, stdout, stderr):
        super(MountCommandError, self).__init__(mp)
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        return (
            """
            stdout:{out}
            stderr:{err}
            {mp}
            """.format(
                out=self.stdout,
                err=self.stderr,
                mp=self.mp,
            )
        )


class FailToMount(MountCommandError):
    pass


class FailToUmount(MountCommandError):
    pass


class FailToRemount(MountCommandError):
    pass
