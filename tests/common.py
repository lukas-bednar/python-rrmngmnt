import contextlib
from subprocess import list2cmdline
from cStringIO import StringIO
from rrmngmnt.executor import Executor


class FakeExecutor(Executor):
    cmd_to_data = None
    class Session(Executor.Session):
        def __init__(self, executor, timeout=None, use_pkey=False):
            super(FakeExecutor.Session, self).__init__(executor)
            self._timeout = timeout

        def open(self):
            pass

        def get_data(self, cmd):
            cmd = list2cmdline(cmd)
            try:
                return self._executor.cmd_to_data[cmd]
            except KeyError:
                raise Exception("There are no data for '%s'" % cmd)

        def command(self, cmd):
            return FakeExecutor.Command(cmd, self)

        def run_cmd(self, cmd, input_=None, timeout=None):
            cmd = self.command(cmd)
            return cmd.run(input_, timeout)

        def open_file(self, name, mode):
            raise NotImplementedError()

    class Command(Executor.Command):

        def get_rc(self):
            return self._rc

        def run(self, input_, timeout=None):
            with self.execute() as (in_, out, err):
                self.out = out.read()
                self.err = err.read()
            return self.rc, self.out, self.err

        @contextlib.contextmanager
        def execute(self, bufsize=-1, timeout=None):
            rc, out, err = self._ss.get_data(self.cmd)
            yield StringIO(), StringIO(out), StringIO(err)
            self._rc = rc

    def session(self, timeout=None):
        return FakeExecutor.Session(self, timeout)

    def run_cmd(self, cmd, input_=None, tcp_timeout=None, io_timeout=None):
        with self.session(tcp_timeout) as session:
            return session.run_cmd(cmd, input_, io_timeout)


if __name__ == "__main__":
    from rrmngmnt import RootUser
    u = RootUser('password')
    e = FakeExecutor(u)
    e.cmd_to_data = {'echo ahoj': (0, 'ahoj', '')}
    print e.run_cmd(['echo', 'ahoj'])
