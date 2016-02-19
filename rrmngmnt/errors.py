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
