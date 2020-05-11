import six
import socket


def fqdn2ip(fqdn):
    """
    translate fqdn to IP

    Args:
        fqdn (str): host name

    Returns:
        str: IP address
    """
    try:
        return socket.gethostbyname(fqdn)
    except (socket.gaierror, socket.herror) as ex:
        args = list(ex.args)
        message = "%s: %s" % (fqdn, args[1])
        args[1] = message
        ex.strerror = message
        ex.args = tuple(args)
        raise


def normalize_string(data):
    """
    get normalized string

    Args:
        data (object): data to process
    Returns:
        object: normalized string
    """
    if isinstance(data, six.binary_type):
        data = data.decode('utf-8', errors='replace')
    return data


class CommandReader(object):
    """
    This class is for gradual reading of commands output lines as they come in.
    Each instance of CommandReader is tied to one command and one executor.
    The executor calls the command only once the method read_lines is called.
    After the execution of command finishes, CommandReader object may be
    queried for return code, stdout and stderr of the command.

    Example usage:
        my_host = Host("1.2.3.4")
        my_host.users.append(RootUser("1234"))
        my_executor = my_host.executor()
        cr = CommandReader(my_executor, ['ansible-playbook', 'long_task.yml']
        for line in cr.read_lines():
            print(line)
    """

    def __init__(self, executor, cmd, cmd_input=None):
        """
        Args:
            executor (rrmngmnt.Executor): instance of rrmngmnt.Executor class
                or one of its subclasses that executes provided command
            cmd (list): Command to be executed
            cmd_input(str): Input for the command
        """
        self.executor = executor
        self.cmd = cmd
        self.cmd_input = cmd_input
        self.rc = None
        self.out = ''
        self.err = ''

    def read_lines(self):
        """
        Generator that yields lines of command output as they come to
        underlying file handler.

        Yields:
            str: Line of command's output stripped of newline character
        """
        with self.executor.session() as ss:
            command = ss.command(self.cmd)
            with command.execute() as (in_, out, err):
                if self.cmd_input:
                    in_.write(self.cmd_input)
                    in_.close()
                while True:
                    line = out.readline()
                    self.out += line
                    if line:
                        yield line.strip('\n')
                        continue
                    if command.rc is not None:
                        break
                self.rc = command.rc
                self.err = err.read()
