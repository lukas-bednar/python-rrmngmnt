import os.path

import pytest

from rrmngmnt import Host, User
from rrmngmnt.playbook_runner import PlaybookRunner
from .common import FakeExecutorFactory


class PlaybookRunnerBase(object):

    # The fake run UUID will be used instead of unique ID that's auto-generated
    # for each playbook execution
    fake_run_uuid = '123'

    playbook_name = 'test.yml'
    playbook_content = ''
    vars_file_name = 'my_vars.yml'
    vars_file_content = ''
    inventory_name = 'my_inventory'
    inventory_content = ''
    ssh_no_strict_host_key_checking = "-o StrictHostKeyChecking=no"

    tmp_dir = os.path.join(PlaybookRunner.tmp_dir, fake_run_uuid)

    success = (0, '', '')
    failure = (1, '', '')

    data = {
        # Filesystem-related operations
        'rm -rf {}'.format(tmp_dir): success,
        'mkdir {}'.format(tmp_dir): success,
        '[ -d {tmp_dir}/{playbook} ]'.format(
            tmp_dir=tmp_dir, playbook=playbook_name
        ): failure,
        '[ -d {tmp_dir}/{vars_file} ]'.format(
            tmp_dir=tmp_dir, vars_file=vars_file_name
        ): failure,
        '[ -d {tmp_dir}/{inventory} ]'.format(
            tmp_dir=tmp_dir, inventory=inventory_name
        ): failure,
        # Actual execution of ansible-playbook
        # Basic scenario
        '{bin} -i {tmp_dir}/{inventory} -v {tmp_dir}/{playbook}'.format(
            bin=PlaybookRunner.binary,
            tmp_dir=tmp_dir,
            inventory=PlaybookRunner.default_inventory_name,
            playbook=playbook_name
        ): success,
        # Extra vars have been provided
        '{bin} -e@{tmp_dir}/{extra_vars} -i {tmp_dir}/{inventory} '
        '-v {tmp_dir}/{playbook}'.format(
            bin=PlaybookRunner.binary,
            extra_vars=PlaybookRunner.extra_vars_file,
            tmp_dir=tmp_dir,
            inventory=PlaybookRunner.default_inventory_name,
            playbook=playbook_name
        ): success,
        # File with additional variables has been provided
        '{bin} -e@{tmp_dir}/{vars_file} -i {tmp_dir}/{inventory} '
        '-v {tmp_dir}/{playbook}'.format(
            bin=PlaybookRunner.binary,
            vars_file=vars_file_name,
            tmp_dir=tmp_dir,
            inventory=PlaybookRunner.default_inventory_name,
            playbook=playbook_name
        ): success,
        # Custom inventory has been provided
        '{bin} -i {tmp_dir}/{inventory} -v {tmp_dir}/{playbook}'.format(
            bin=PlaybookRunner.binary,
            tmp_dir=tmp_dir,
            inventory=inventory_name,
            playbook=playbook_name
        ): success,
        # Verbosity has been increased to max
        '{bin} -i {tmp_dir}/{inventory} -vvvvv {tmp_dir}/{playbook}'.format(
            bin=PlaybookRunner.binary,
            tmp_dir=tmp_dir,
            inventory=PlaybookRunner.default_inventory_name,
            playbook=playbook_name
        ): success,
        # Running in check mode
        '{bin} -i {tmp_dir}/{inventory} -v {check_mode_param} '
        '{tmp_dir}/{playbook}'.format(
            bin=PlaybookRunner.binary,
            tmp_dir=tmp_dir,
            inventory=PlaybookRunner.default_inventory_name,
            check_mode_param=PlaybookRunner.check_mode_param,
            playbook=playbook_name
        ): success,
        # Running with extended SSH common args
        '{bin} -i {tmp_dir}/{inventory} '
        '-v "{ssh_common_args_param}={ssh_common_args}" '
        '{tmp_dir}/{playbook}'.format(
            bin=PlaybookRunner.binary,
            tmp_dir=tmp_dir,
            inventory=PlaybookRunner.default_inventory_name,
            ssh_common_args_param=PlaybookRunner.ssh_common_args_param,
            ssh_common_args=ssh_no_strict_host_key_checking,
            playbook=playbook_name
        ): success,
    }

    @classmethod
    @pytest.fixture(scope='class')
    def fake_host(cls):
        fh = Host('1.1.1.1')
        fh.add_user(User('root', '11111'))
        fh.executor_factory = FakeExecutorFactory(cls.data, cls.files)
        return fh

    @pytest.fixture()
    def fake_playbook(self, tmpdir):
        fp = tmpdir.join(self.playbook_name)
        fp.write(self.playbook_content)
        return str(fp)

    @pytest.fixture()
    def fake_remote_playbook(self, fake_host):
        fp = os.path.join(self.tmp_dir, self.playbook_name)
        fake_host.fs.create_file(
            content=self.playbook_content, path=str(fp)
        )
        return str(fp)

    @pytest.fixture()
    def playbook_runner(self, fake_host):
        playbook_runner = PlaybookRunner(fake_host)
        playbook_runner.short_run_uuid = self.fake_run_uuid
        return playbook_runner

    def check_files_on_host(self, files=None):
        """
        Check that all files provided to files parameter (and only those) have
        been "copied" to our imaginary host. In reality, they should not be
        present on host once the playbook's execution is done. However here
        we'll use the fact that our fake host does not really implements file
        removal. Because of this, in the end of the test case, we can check
        that files that should have been copied to the host (by using
        FileSystem service) have actually been sent there.

        Args:
            files (list): List of files that should have been copied to the
                host. Don't include test playbook into this list since its
                presence is implicitly expected. You can also provide only one
                file as a string.

        Returns:
            bool: True if files expected on host and those present match,
                False otherwise
        """
        if files is None:
            files = []
        if isinstance(files, str):
            files = [files]
        expected_files = [os.path.join(self.tmp_dir, self.playbook_name)]
        expected_files.extend(files)
        return sorted(expected_files) == sorted(list(self.files.keys()))


class TestBasic(PlaybookRunnerBase):

    files = {}

    def test_basic_scenario(self, playbook_runner, fake_playbook):
        """ User has provided only playbook """
        rc, _, _ = playbook_runner.run(playbook=fake_playbook)
        assert not rc
        assert self.check_files_on_host(
            os.path.join(self.tmp_dir, PlaybookRunner.default_inventory_name)
        )


class TestRemoteBasic(PlaybookRunnerBase):

    files = {}

    def test_remote_scenario(self, playbook_runner, fake_remote_playbook):
        """ User has provided only remote playbook """
        rc, _, _ = playbook_runner.run(
            playbook=fake_remote_playbook, upload_playbook=False
        )
        assert not rc
        assert self.check_files_on_host(
            os.path.join(self.tmp_dir, PlaybookRunner.default_inventory_name)
        )


class TestExtraVars(PlaybookRunnerBase):

    files = {}

    def test_extra_vars(self, playbook_runner, fake_playbook):
        """ User has provided extra vars as a dictionary """
        rc, _, _ = playbook_runner.run(
            playbook=fake_playbook,
            extra_vars={
                "greetings": "hello",
            }
        )
        assert not rc
        assert self.check_files_on_host(
            [
                os.path.join(
                    self.tmp_dir, PlaybookRunner.default_inventory_name
                ),
                os.path.join(self.tmp_dir, PlaybookRunner.extra_vars_file)
            ]
        )


class TestVarsFile(PlaybookRunnerBase):

    files = {}

    @pytest.fixture()
    def fake_vars_file(self, tmpdir):
        fvf = tmpdir.join(self.vars_file_name)
        fvf.write(self.vars_file_content)
        return str(fvf)

    def test_vars_file(self, playbook_runner, fake_playbook, fake_vars_file):
        """ User has provided YAML file with custom variables """
        rc, _, _ = playbook_runner.run(
            playbook=fake_playbook,
            vars_files=[fake_vars_file]
        )
        assert not rc
        assert self.check_files_on_host(
            [
                os.path.join(
                    self.tmp_dir, PlaybookRunner.default_inventory_name
                ),
                os.path.join(self.tmp_dir, self.vars_file_name)
            ]
        )


class TestInventory(PlaybookRunnerBase):

    files = {}

    @pytest.fixture()
    def fake_inventory(self, tmpdir):
        fi = tmpdir.join(self.inventory_name)
        fi.write(self.inventory_content)
        return str(fi)

    def test_inventory(self, playbook_runner, fake_playbook, fake_inventory):
        """ User has provided custom inventory instead of the default one """
        rc, _, _ = playbook_runner.run(
            playbook=fake_playbook,
            inventory=fake_inventory
        )
        assert not rc
        assert self.check_files_on_host(
            os.path.join(self.tmp_dir, self.inventory_name)
        )


class TestVerbosity(PlaybookRunnerBase):

    files = {}

    def test_max_verbosity(self, playbook_runner, fake_playbook):
        """ User has increased verbosity to maximum level """
        rc, _, _ = playbook_runner.run(
            playbook=fake_playbook,
            verbose_level=5
        )
        assert not rc
        assert self.check_files_on_host(
            os.path.join(self.tmp_dir, PlaybookRunner.default_inventory_name)
        )


class TestCheckMode(PlaybookRunnerBase):

    files = {}

    def test_check_mode(self, playbook_runner, fake_playbook):
        """ User is running the playbook with --check param """
        rc, _, _ = playbook_runner.run(
            playbook=fake_playbook,
            run_in_check_mode=True
        )
        assert not rc
        assert self.check_files_on_host(
            os.path.join(self.tmp_dir, PlaybookRunner.default_inventory_name)
        )


class TestSSHCommonArgs(PlaybookRunnerBase):

    files = {}

    def test_no_strict_host_key_checking(self, playbook_runner, fake_playbook):
        """
        User has provided custom SSH argument that extend default Ansible SSH
        arguments
        """
        rc, _, _ = playbook_runner.run(
            playbook=fake_playbook,
            ssh_common_args=[self.ssh_no_strict_host_key_checking]
        )
        assert not rc
        assert self.check_files_on_host(
            os.path.join(self.tmp_dir, PlaybookRunner.default_inventory_name)
        )
