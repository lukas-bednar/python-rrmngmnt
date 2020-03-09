import contextlib
import json
import os.path
import uuid

from rrmngmnt.common import CommandReader
from rrmngmnt.resource import Resource
from rrmngmnt.service import Service


class PlaybookRunner(Service):
    """
    Class for working with and especially executing Ansible playbooks on hosts.
    On your Host instance, it might be accessed (similar to other services) by
    playbook property.
    Each instance of this class represent a unique ansible run with an uuid.

    Example:
        rc,out, err = my_host.playbook.run('long_task.yml')

    In such case, the default logger of this class (called PlaybookRunner) will
    be used to log playbook's output. It will propagate events to handlers of
    ancestor loggers. However, PlaybookRunner might also be directly
    instantiated with instance of logging.Logger passed to logger parameter.

    Example:
        my_runner = PlaybookRunner(my_host, logging.getLogger('playbook'))
        rc, out, err = my_runner.run('long_task.yml')

    In that case, custom provided logger will be used instead. In both cases,
    each log record will be prefixed with UUID generated specifically for that
    one playbook execution.
    """
    class LoggerAdapter(Resource.LoggerAdapter):

        def process(self, msg, kwargs):
            return "[%s] %s" % (self.extra['self'].short_run_uuid, msg), kwargs

    tmp_dir = "/tmp"
    binary = "ansible-playbook"
    extra_vars_file = "extra_vars.json"
    default_inventory_name = "inventory"
    default_inventory_content = "localhost ansible_connection=local"
    ssh_common_args_param = "--ssh-common-args"
    check_mode_param = "--check"

    def __init__(self, host, logger=None):
        """
        Args:
            host (rrmngmnt.Host): Underlying host for this service
            logger (logging.Logger): Alternate logger for Ansible output
        """
        super(PlaybookRunner, self).__init__(host)
        if logger:
            self.set_logger(logger)
        self.run_uuid = uuid.uuid4()
        self.short_run_uuid = str(self.run_uuid).split('-')[0]
        self.tmp_exec_dir = None
        self.cmd = [self.binary]
        self.rc = None
        self.out = None
        self.err = None

    @contextlib.contextmanager
    def _exec_dir(self):
        """
        Context manager that makes sure that for each execution of playbook,
        temporary directory (whose name is the same as run's UUID) is created
        on the host and removed afterwards.
        """
        exec_dir_path = os.path.join(self.tmp_dir, self.short_run_uuid)
        self.host.fs.rmdir(exec_dir_path)
        self.host.fs.mkdir(exec_dir_path)
        self.tmp_exec_dir = exec_dir_path
        try:
            yield
        finally:
            self.tmp_exec_dir = None
            self.host.fs.rmdir(exec_dir_path)

    def _upload_file(self, file_):
        file_path_on_host = os.path.join(
            self.tmp_exec_dir, os.path.basename(file_)
        )
        self.host.fs.put(path_src=file_, path_dst=file_path_on_host)
        return file_path_on_host

    def _dump_vars_to_json_file(self, vars_):
        file_path_on_host = os.path.join(
            self.tmp_exec_dir, self.extra_vars_file
        )
        self.host.fs.create_file(
            content=json.dumps(vars_), path=file_path_on_host
        )
        return file_path_on_host

    def _generate_default_inventory(self):
        file_path_on_host = os.path.join(
            self.tmp_exec_dir, self.default_inventory_name
        )
        self.host.fs.create_file(
            content=self.default_inventory_content,
            path=file_path_on_host
        )
        return file_path_on_host

    def run(
        self, playbook, extra_vars=None, vars_files=None, inventory=None,
        verbose_level=1, run_in_check_mode=False, ssh_common_args=None,
        upload_playbook=True
    ):
        """
        Run Ansible playbook on host

        Args:
            playbook (str): Path to playbook you want to execute (the location
                is determine by remote_playbook argument - default is local)
            extra_vars (dict): Dictionary of extra variables that are to be
                passed to playbook execution. They will be dumped to JSON file
                and included using -e@ parameter
            vars_files (list): List of additional variable files to be included
                using -e@ parameter. If one variable is specified both in
                extra_vars and in one of the vars_files, the one in vars_files
                takes precedence.
            inventory (str): Path to an inventory file (on your machine) to be
                used for playbook execution. If none is provided, default
                inventory including only localhost will be generated and used
            verbose_level (int): How much should playbook be verbose. Possible
                values are 1 through 5 with 1 being the most quiet and 5 being
                the most verbose
            run_in_check_mode (bool): If True, playbook will not actually be
                executed, but instead run with --check parameter
            ssh_common_args (list): List of options that will extend (not
                replace) the list of default options that Ansible uses when
                calling ssh/sftp/scp. Example: ["-o StrictHostKeyChecking=no",
                "-o UserKnownHostsFile=/dev/null"]
            upload_playbook (bool): If the playbook is going to be uploaded
                from the local machine (True - Default) or not (False)

        Returns:
            tuple: tuple of (rc, out, err)
        """
        self.logger.info(
            "Running playbook {} on {}".format(
                os.path.basename(playbook),
                self.host.fqdn
            )
        )

        with self._exec_dir():

            if extra_vars:
                self.cmd.append(
                    "-e@{}".format(self._dump_vars_to_json_file(extra_vars))
                )

            if vars_files:
                for f in vars_files:
                    self.cmd.append("-e@{}".format(self._upload_file(f)))

            self.cmd.append("-i")
            if inventory:
                self.cmd.append(self._upload_file(inventory))
            else:
                self.cmd.append(self._generate_default_inventory())

            self.cmd.append("-{}".format("v" * verbose_level))

            if run_in_check_mode:
                self.cmd.append(self.check_mode_param)

            if ssh_common_args:
                self.cmd.append(
                    "{}={}".format(
                        self.ssh_common_args_param, " ".join(ssh_common_args)
                    )
                )

            if upload_playbook:
                playbook = self._upload_file(playbook)
            self.cmd.append(playbook)

            self.logger.debug("Executing: {}".format(" ".join(self.cmd)))

            playbook_reader = CommandReader(self.host.executor(), self.cmd)
            for line in playbook_reader.read_lines():
                self.logger.debug(line)
            self.rc, self.out, self.err = (
                playbook_reader.rc,
                playbook_reader.out,
                playbook_reader.err
            )

            self.logger.debug(
                "Ansible playbook finished with RC: {}".format(self.rc)
            )

        return self.rc, self.out, self.err
