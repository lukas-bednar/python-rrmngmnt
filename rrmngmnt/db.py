from rrmngmnt.service import Service


class Database(Service):

    def __init__(self, host, name, user):
        """
        :param host: Remote resouce to DB machine
        :type host: instance of Host
        :param name: database name
        :type name: str
        :param user: user/role
        :type user: instance of User
        """
        super(Database, self).__init__(host)
        self.name = name
        self.user = user

    def psql(self, sql, *args):
        """
        Execute psql command on host

        :param sql: sql command
        :type sql: string
        :param args: positional format arguments for command
        :type args: list of arguments
        :return: list of lines with records
        :rtype: list(list(string, string, ...))
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
        # We need to realize that connection can be forbiden from outside ...

    def restart(self):
        self.host.service('postgresql').restart()
