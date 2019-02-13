# -*- coding: utf-8 -*-
import pytest

from rrmngmnt import Host, User
from rrmngmnt.db import Database
from .common import FakeExecutorFactory


host_executor_factory = Host.executor_factory


def teardown_module():
    Host.executor_factory = host_executor_factory


def fake_cmd_data(cmd_to_data, files=None):
    Host.executor_factory = FakeExecutorFactory(cmd_to_data, files)


class TestDb(object):
    data = {
        'which systemctl': (0, "", ""),
        'systemctl list-unit-files | grep -o ^[^.][^.]*.service | '
        'cut -d. -f1 | sort | uniq': (0, "postgresql\n", "",),
        'systemctl restart postgresql.service': (0, '', ''),
        'export PGPASSWORD=db_pass; psql -d db_name -U db_user '
        '-h localhost -R __RECORD_SEPARATOR__ -t -A -c '
        '"SELECT key, value FROM dist"': (
            0,
            "key1|value1__RECORD_SEPARATOR__key2|value2",
            "",
        ),
        'export PGPASSWORD=db_pass; psql -d db_name -U db_user -h localhost '
        '-R __RECORD_SEPARATOR__ -t -A -c "SELECT * FROM table ERROR"': (
            1, "", "Syntax Error"
        ),
        'export PGPASSWORD=db_pass; psql -d db_name -U db_user -h localhost '
        '-c \\\\dt': (
            0,
            (
                "List of relations\n"
                " Schema |         Name         | Type  | Owner\n"
                "--------+----------------------+-------+---------\n"
                " public | test_table           | table | postgres\n"
            ),
            ""
        ),
        'export PGPASSWORD=db_pass; psql -d db_name -U db_user -h localhost '
        '-c \\\\dv': (
            0, "", "Did not find any relations."
        ),
        'export PGPASSWORD=db_pass; psql -d db_name -U db_user -h localhost '
        '-c \\\\gg': (
            1, "", "invalid command \\gg"
        ),
    }
    files = {}

    db_name = "db_name"
    db_user = "db_user"
    db_pass = "db_pass"

    @classmethod
    def setup_class(cls):
        fake_cmd_data(cls.data, cls.files)

    def get_db(self, ip='1.1.1.1'):
        h = Host(ip)
        h.add_user(User('root', '34546'))
        return Database(
            h, self.db_name, User(self.db_user, self.db_pass),
        )

    def test_restart(self):
        db = self.get_db()
        db.restart()

    def test_psql(self):
        db = self.get_db()
        res = db.psql("SELECT %s, %s FROM %s", "key", "value", "dist")
        assert res == [['key1', 'value1'], ['key2', 'value2']]

    def test_negative(self):
        db = self.get_db()
        with pytest.raises(Exception) as ex_info:
            db.psql("SELECT * FROM table ERROR")
        assert "Syntax Error" in str(ex_info.value)

    def test_psql_cmd(self):
        db = self.get_db()
        res = db.psql_cmd('\\\\dt')
        assert 'List of relations' in res
        res = db.psql_cmd('\\\\dv')
        assert res == 'Did not find any relations.'

    def test_negative_cmd(self):
        db = self.get_db()
        with pytest.raises(Exception) as ex_info:
            db.psql_cmd('\\\\gg')
        assert 'invalid command' in str(ex_info.value)
