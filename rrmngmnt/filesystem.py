import os
from rrmngmnt.service import Service
from rrmngmnt import errors


class FileSystem(Service):
    """
    Class for working with filesystem.
    It has same interface as 'os' module.
    """
    def _exec_command(self, cmd):
        host_executor = self.host.executor()
        rc, _, err = host_executor.run_cmd(cmd)
        if rc:
            raise errors.CommandExecutionFailure(
                cmd=cmd, executor=host_executor, rc=rc, err=err
            )

    def _exec_file_test(self, op, path):
        return self.host.executor().run_cmd(
            ['[', '-%s' % op, path, ']']
        )[0] == 0

    def exists(self, path):
        return self._exec_file_test('e', path)

    def isfile(self, path):
        return self._exec_file_test('f', path)

    def isdir(self, path):
        return self._exec_file_test('d', path)

    def remove(self, path):
        return self.host.executor().run_cmd(
            ['rm', '-f', path]
        )[0] == 0
    unlink = remove

    def rmdir(self, path):
        if path == "/":
            raise ValueError("Attempt to remove root dir '/' !")
        return self.host.executor().run_cmd(
            ['rm', '-rf', path]
        )[0] == 0

    def listdir(self, path):
        return self.host.executor().run_cmd(
            ['ls', '-A1', path]
        )[1].split()

    def touch(self, file_name, path):
        """
        Creates a file on host

        __author__ = "ratamir"
        :param file_name: The file to create
        :type file_name: str
        :param path: The path under which the file will be created
        :type path: str
        :returns: True when file creation succeeds, False otherwise
        False otherwise
        :rtype: bool
        """
        full_path = os.path.join(path, file_name)
        return self.host.run_command(['touch', full_path])[0] == 0

    def flush_file(self, file_path):
        """
        Flushes the file.

        :param file_path: The path of file to flush.
        :type file_path: str
        :returns: True if truncated, False otherwise
        :rtype: bool
        """
        cmd = ["truncate", "-s", "0", file_path]
        return self.host.run_command(cmd)[0] == 0

    def read_file(self, path):
        """
        Reads a content of a file in a given path

        :param path: The path from where to take a content from
        :type path: str
        :return: Content of a file
        :rtype: str
        """
        cmd = ["cat", path]
        rc, out, _ = self.host.run_command(cmd)
        return out if not rc else ""

    def create_script(self, content, path):
        """
        Create script on filesystem, and make it executable.

        :param content: content of the script
        :type content: str
        :param path: path to script to create
        :type path: str
        """
        executor = self.host.executor()
        with executor.session() as session:
            with session.open_file(path, 'wb') as fh:
                fh.write(content)
            self.chmod(path=path, mode="+x")

    def mkdir(self, path):
        """
        Create directory on host

        :param path: directory path
        :type path: str
        :raises: CommandExecutionFailure, if mkdir failed
        """
        self._exec_command(['mkdir', path])

    def chown(self, path, username, groupname):
        """
        Change owner of file or directory

        :param path: file or directory path
        :type path: str
        :param username: change user owner to username
        :type username: str
        :param groupname: change group owner to groupname
        :type groupname: str
        :raises: CommandExecutionFailure, if chown failed
        """
        self._exec_command(['chown', '%s:%s' % (username, groupname), path])

    def chmod(self, path, mode):
        """
        Change permission of directory or file

        :param path: file or directory path
        :type path: str
        :param mode: permission mode(600 for example or u+x)
        :type mode: str
        :raises: CommandExecutionFailure, if chmod failed
        """
        self._exec_command(['chmod', mode, path])

    def wget(self, url, output_file, progress_handler=None):
        """
        Download file on the host from given url

        :param url: url to file
        :type url: str
        :param output_file: full path to output file
        :type output_file: str
        :param progress_handler: progress handler function
        :type progress_handler: func
        :return: absolute path to file
        :rtype: str
        """
        rc = None
        host_executor = self.host.executor()
        cmd = ["wget", "-O", output_file, "--no-check-certificate", url]
        with host_executor.session() as host_session:
            wget_command = host_session.command(cmd)
            with wget_command.execute() as (_, _, stderr):
                counter = 0
                while rc is None:
                    line = stderr.readline()
                    if counter == 1000 and progress_handler:
                        progress_handler(line)
                        counter = 0
                    counter += 1
                    rc = wget_command.get_rc()
        if rc:
            raise errors.CommandExecutionFailure(
                host_executor, cmd, rc,
                "Failed to download file from url {0}".format(url)
            )
        return output_file
