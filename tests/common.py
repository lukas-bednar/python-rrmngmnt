import contextlib
from subprocess import list2cmdline
from cStringIO import StringIO
from rrmngmnt.executor import Executor


class FakeExecutor(Executor):
    cmd_to_data = None
    class Session(Executor.Session):

        def open(self):
            pass

        def get_data(self, cmd):
            cmd = list2cmdline(cmd)
            try:
                return self._executor.cmd_to_data[cmd]
            except KeyError:
                raise Exception("There are no data for %s" % cmd)

        def command(self, cmd):
            return FakeExecutor.Command(cmd, self)

        def open_file(self, name, mode):
            raise NotImplementedError()

    class Command(Executor.Command):

        def get_rc(self):
            return self._rc

        def run(self, input_):
            with self.execute() as (in_, out, err):
                self.out = out.read()
                self.err = err.read()
            return self.rc, self.out, self.err

        @contextlib.contextmanager
        def execute(self, bufsize=-1):
            rc, out, err = self._ss.get_data(self.cmd)
            yield StringIO(), StringIO(out), StringIO(err)
            self._rc = rc

    def session(self):
        return FakeExecutor.Session(self)


if __name__ == "__main__":
    from rrmngmnt import RootUser
    u = RootUser('password')
    e = FakeExecutor(u)
    e.cmd_to_data = {'echo ahoj': (0, 'ahoj', '')}
    print e.run_cmd(['echo', 'ahoj'])
