import os
from rrmngmnt.service import Service


class FileSystem(Service):
    """
    Class for working with filesystem.
    It has same interface as 'os' module.
    """
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

    def mkdir(self, path):
        """
        Create directory on host

        :param path: directory path
        :type path: str
        :return: True, if action succeed, otherwise False
        :rtype: bool
        """
        return self.host.run_command(
            ['mkdir', path]
        )[0] == 0

    def chown(self, path, username, groupname):
        """
        Change owner of file or directory

        :param path: file or directory path
        :type path: str
        :param username: change user owner to username
        :type username: str
        :param groupname: change group owner to groupname
        :type groupname: str
        :return: True, if action succeed, otherwise False
        :rtype: bool
        """
        return self.host.run_command(
            ['chown', '%s:%s' % (username, groupname), path]
        )[0] == 0

    def chmod(self, path, mode):
        """
        Change permission of directory or file

        :param path: file or directory path
        :type path: str
        :param mode: permission mode(600 for example or u+x)
        :type mode: str
        :return: True, if action succeed, otherwise False
        :rtype: bool
        """
        return self.host.run_command(
            ['chmod', mode, path]
        )[0] == 0
