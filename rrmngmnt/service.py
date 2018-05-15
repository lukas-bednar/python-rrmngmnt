from rrmngmnt.resource import Resource
import re


class Service(Resource):
    """
    General service provided by Host.
    """

    class LoggerAdapter(Resource.LoggerAdapter):
        """
        Makes sure that all logs made in this class, has appropriate prefix:
        [IP]
        """
        def process(self, msg, kwargs):
            return (
                "[%s] %s" % (
                    self.extra['self'].host.ip,
                    msg,
                ),
                kwargs,
            )

    def __init__(self, host):
        super(Service, self).__init__()
        self.host = host


class SystemService(Service):
    """
    Read https://fedoraproject.org/wiki/SysVinit_to_Systemd_Cheatsheet
    for more info / differences between Systemd and SysVinit
    """
    default_timeout = 30
    cmd = None

    class CanNotHandle(Exception):
        pass

    class Error(Exception):
        pass

    def __init__(self, host, name, timeout=None):
        super(SystemService, self).__init__(host)
        self.name = name
        if timeout is None:
            timeout = self.default_timeout
        self.timeout = timeout
        self._can_handle()

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self.name)

    def is_enabled(self):
        raise NotImplementedError()

    def enable(self):
        raise NotImplementedError()

    def disable(self):
        raise NotImplementedError()

    def status(self):
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def restart(self):
        raise NotImplementedError()

    def reload(self):
        raise NotImplementedError()

    def mask(self):
        raise NotImplementedError("Method supported only under systemd")

    def unmask(self):
        raise NotImplementedError("Method supported only under systemd")

    def _can_handle(self):
        """
        Raises:
            CanNotHandle
        """
        executor = self.host.executor()
        rc, _, _ = executor.run_cmd(
            ['which', self.cmd],
            io_timeout=self.timeout,
        )
        if rc:
            raise self.CanNotHandle("Missing %s" % self.cmd)


class SysVinit(SystemService):
    cmd = 'service'
    manage_cmd = 'chkconfig'
    _not_supported = (
        'libvirtd',
    )

    def _can_handle(self):
        if self.name in self._not_supported:
            raise self.CanNotHandle("%s is not supported" % self.name)
        super(SysVinit, self)._can_handle()
        init_script = '/etc/init.d/%s' % self.name
        executor = self.host.executor()
        cmd = ('[', '-e', init_script, ']')
        rc, _, _ = executor.run_cmd(cmd, io_timeout=self.timeout)
        if rc:
            raise self.CanNotHandle(
                "there is missing init script %s" % init_script
            )

    def _toggle(self, action):
        cmd = [
            self.cmd,
            self.name,
            action,
        ]
        executor = self.host.executor()
        rc, _, _ = executor.run_cmd(cmd, io_timeout=self.timeout)
        return rc == 0

    def _manage(self, action):
        cmd = [
            self.manage_cmd,
            self.name,
            action,
        ]
        executor = self.host.executor()
        rc, _, _ = executor.run_cmd(cmd, io_timeout=self.timeout)
        return rc == 0

    def is_enabled(self):
        cmd = [
            self.manage_cmd,
            self.name,
        ]
        executor = self.host.executor()
        rc, _, _ = executor.run_cmd(cmd, io_timeout=self.timeout)
        return rc == 0

    def enable(self):
        return self._manage('on')

    def disable(self):
        return self._manage('off')

    def status(self):
        return self._toggle('status')

    def start(self):
        return self._toggle('start')

    def stop(self):
        return self._toggle('stop')

    def restart(self):
        return self._toggle('restart')

    def reload(self):
        return self._toggle('reload')


class Systemd(SystemService):
    cmd = 'systemctl'

    def _can_handle(self):
        super(Systemd, self)._can_handle()

        orig_name = self.name
        if "@" in self.name:
            self.name = re.match(r'^.*@', self.name).group(0)

        cmd = (
            'systemctl', 'list-unit-files', '|',
            'grep', '-o', '^[^.][^.]*.service', '|',
            'cut', '-d.', '-f1', '|',
            'sort', '|', 'uniq',
        )
        executor = self.host.executor()
        rc, out, _ = executor.run_cmd(cmd, io_timeout=self.timeout)
        out = out.strip().splitlines()
        if rc or self.name not in out:
            raise self.CanNotHandle(
                "%s is not listed in %s" % (orig_name, out)
            )
        self.name = orig_name

    def _execute(self, action):
        cmd = [
            self.cmd,
            action,
            self.name + ".service",
        ]
        executor = self.host.executor()
        rc, _, _ = executor.run_cmd(cmd, io_timeout=self.timeout)

        if rc:
            cmd = ['journalctl', '-u', self.name + ".service"]
            _, out, _ = executor.run_cmd(cmd, io_timeout=self.timeout)
            self.logger.warning(out)

        return rc == 0

    def is_enabled(self):
        return self._execute('is-enabled')

    def enable(self):
        return self._execute('enable')

    def disable(self):
        return self._execute('disable')

    def status(self):
        return self._execute('status')

    def start(self):
        return self._execute('start')

    def stop(self):
        return self._execute('stop')

    def restart(self):
        return self._execute('restart')

    def reload(self):
        return self._execute('reload')

    def mask(self):
        return self._execute('mask')

    def unmask(self):
        return self._execute('unmask')


class InitCtl(SystemService):
    cmd = 'initctl'

    def _can_handle(self):
        super(InitCtl, self)._can_handle()
        executor = self.host.executor()
        cmd = [
            self.cmd, 'list', '|',
            'cut', '-d', ' ', '-f1', '|',
            'sort', '|', 'uniq',
        ]
        rc, out, _ = executor.run_cmd(cmd, io_timeout=self.timeout)
        out = out.strip().splitlines()
        if rc or self.name not in out:
            raise self.CanNotHandle(
                "%s is not listed in %s" % (self.name, out)
            )

    def _execute(self, action):
        cmd = [
            self.cmd,
            action,
            self.name,
        ]
        executor = self.host.executor()
        rc, out, err = executor.run_cmd(cmd, io_timeout=self.timeout)
        if rc:
            raise self.Error(err)
        return out.strip()

    def _toggle(self, action):
        try:
            self._execute(action)
        except self.Error as ex:
            self.logger.error("Failed to %s service: %s", action, ex)
            return False
        return True

    def status(self):
        out = self._execute('status')
        return '/running' in out

    def start(self):
        return self._toggle('start')

    def stop(self):
        return self._toggle('stop')

    def restart(self):
        if not self.status():
            # NOTE: see man(initctl) restart part:
            # Note that this command can only be used when there is
            # an instance of JOB, if there is none then it returns an error
            # instead of starting a new one.
            return self.start()
        return self._toggle('restart')

    def reload(self):
        return self._toggle('reload')
