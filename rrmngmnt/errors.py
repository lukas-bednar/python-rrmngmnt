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
        :param executor: executor used for execution
        :type executor: instance of RemoteExecutor
        :param cmd: executed command
        :type cmd: list
        :param rc: return code
        :type rc: int
        :param err: standard error output if provided
        :type err: string
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
        :param host: relevant host
        :type host: instance of Host
        :param operation: name of unsupported operation
        :type operation: str
        :param reason: message
        :type message: str
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
