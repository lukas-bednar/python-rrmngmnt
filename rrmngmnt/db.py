from rrmngmnt.service import Service


class Database(Service):

    def __init__(self, host, name, user):
        """
        Args:
            host (Host): Remote resouce to DB machine
            name (str): database name
            user (User): user/role
        """
        super(Database, self).__init__(host)
        self.name = name
        self.user = user

    def psql(self, sql, *args):
        """
        Execute sql command on host

        Args:
            sql (str): sql command
            args (list): positional format arguments for command

        Returns:
            list: list of lines with records.
        """
        separator = '__RECORD_SEPARATOR__'
        sql = sql % tuple(args)
        cmd = [
            'export', 'PGPASSWORD=%s;' % self.user.password,
            'psql', '-d', self.name, '-U', self.user.name, '-h', 'localhost',
            '-R', separator, '-t', '-A', '-c', sql,
        ]

        executor = self.host.executor()
        with executor.session() as ss:
            rc, out, err = ss.run_cmd(cmd)
        if rc:
            raise Exception(
                "Failed to exec sql command: %s" % err
            )
        return [
            a.strip().split('|') for a in out.strip().split(separator)
            if a.strip()
        ]
        # NOTE: I am considering to use Psycopg2 to access DB directly.
        # I need to think whether it is better or not.
        # We need to realize that connection can be forbidden from outside ...

    def psql_cmd(self, command):
        """
        Execute psql special command on host (e.g. \\dt, \\dv, ...)

        Args:
            command (str): special psql command
        Returns:
            str: output of the command
        """
        cmd = [
            'export', 'PGPASSWORD=%s;' % self.user.password,
            'psql', '-d', self.name, '-U', self.user.name, '-h', 'localhost',
            '-c', command
        ]
        executor = self.host.executor()
        with executor.session() as ss:
            rc, out, err = ss.run_cmd(cmd)
        if rc:
            raise Exception(
                "Failed to exec command: %s" % err
            )
        if not out and err:
            out = err
        return out

    def restart(self):
        """
        Restart postgresql service
        """
        self.host.service('postgresql').restart()
