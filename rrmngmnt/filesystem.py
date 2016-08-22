import os

import six

from rrmngmnt import errors
from rrmngmnt.service import Service


class FileSystem(Service):
    """
    Class for working with filesystem.
    It has same interface as 'os' module.
    """
    def _exec_command(self, cmd):
        host_executor = self.host.executor()
        rc, out, err = host_executor.run_cmd(cmd)
        if rc:
            raise errors.CommandExecutionFailure(
                cmd=cmd, executor=host_executor, rc=rc, err=err
            )
        return out

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
                fh.write(six.b(content))
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

    def get(self, path_src, path_dst):
        """
        Fetch file from Host and store on local system

        :param path_src: path to file on remote system
        :type path_src: str
        :param path_dst: path to file on local system or directory
        :type path_dst: str
        :return: path to destination file
        :rtype: str
        """
        if os.path.isdir(path_dst):
            path_dst = os.path.join(path_dst, os.path.basename(path_src))
        with self.host.executor().session() as ss:
            with ss.open_file(path_src, 'rb') as rh:
                with open(path_dst, 'wb') as wh:
                    wh.write(rh.read())
        return path_dst

    def put(self, path_src, path_dst):
        """
        Upload file from local system to Host

        :param path_src: path to file on local system
        :type path_src: str
        :param path_dst: path to file on remote system or directory
        :type path_dst: str
        :return: path to destination file
        :rtype: str
        """
        if self.isdir(path_dst):
            path_dst = os.path.join(path_dst, os.path.basename(path_src))
        with self.host.executor().session() as ss:
            with open(path_src, 'rb') as rh:
                with ss.open_file(path_dst, 'wb') as wh:
                    wh.write(rh.read())
        return path_dst

    def transfer(self, path_src, target_host, path_dst):
        """
        Transfer file from one remote system (self) to other
        remote system (target_host).

        :param path_src: path to file on local system
        :type path_src: str
        :param target_host: target system
        :type target_host: instance of Host
        :param path_dst: path to file on remote system or directory
        :type path_dst: str
        :return: path to destination file
        :rtype: str
        """
        if target_host.fs.isdir(path_dst):
            path_dst = os.path.join(path_dst, os.path.basename(path_src))
        with self.host.executor().session() as h1s:
            with target_host.executor().session() as h2s:
                with h1s.open_file(path_src, 'rb') as rh:
                    with h2s.open_file(path_dst, 'wb') as wh:
                        wh.write(rh.read())
        return path_dst

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
