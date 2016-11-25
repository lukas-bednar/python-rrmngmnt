import os

import six
import warnings

from rrmngmnt import errors
from rrmngmnt.service import Service
from rrmngmnt.resource import Resource


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

    def touch(self, *args):
        """
        Creates files on host

        __author__ = "vkondula"
        :param args: Paths of files to create
        :type args: list of str
        :returns: True when file creation succeeds, False otherwise
        :rtype: bool
        """
        if len(args) == 2 and self.isdir(args[1]):
            warnings.warn(
                "This usecase is deprecated and will be removed. "
                "Use list of fullpaths instead"
            )
            return self._deprecated_touch(args[0], args[1])
        return self.host.run_command(['touch'] + list(args))[0] == 0

    def _deprecated_touch(self, file_name, path):
        """
        Creates a file on host

        __author__ = "ratamir"
        :param file_name: The file to create
        :type file_name: str
        :param path: The path under which the file will be created
        :type path: str
        :returns: True when file creation succeeds, False otherwise
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

    def move(self, source_path, destination_path):
        """
        Moves a file or directory from source to destination.

        :param source_path: The source path to move from.
        :type source_path: str
        :param destination_path: The destination path to move to.
        :type destination_path: str
        :return: True if there were no errors, False otherwise.
        :rtype: bool
        """
        cmd = ["mv", source_path, destination_path]
        return self.host.run_command(cmd)[0] == 0

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

    def mktemp(self, template=None, tmpdir=None, directory=False):
        """
        Make temporary file

        :param template: template for path, 'X's are replaced
        :type template: str
        :param tmpdir: where to create file, if not specified
            use $TMPDIR if set, else /tmp
        :type tmpdir: str
        :param directory: create directory instead of a file
        :type directory: bool
        :return: absolute path to file or None if failed
        :rtype: str
        """
        cmd = ['mktemp']
        if tmpdir:
            cmd.extend(['-p', tmpdir])
        if directory:
            cmd.append('-d')
        if template:
            cmd.append(template)
        rc, out, _ = self.host.run_command(cmd)
        if rc:
            raise errors.FailCreateTemp(cmd)
        return out.replace('\n', '')

    def mount_point(
        self, source, target=None, fs_type=None, opts=None
    ):
        return MountPoint(
            self,
            source=source,
            target=target,
            fs_type=fs_type,
            opts=opts,
        )


class MountPoint(Resource):
    """
    Class for mounting devices.
    """
    def __init__(self, fs, source, target=None, fs_type=None, opts=None):
        """
        Mounts source to target mount point

        __author__ = "vkondula"
        :param fs: FileSystem object instance
        :type fs: FileSystem
        :param source: Full path to source
        :type source: str
        :param target: Path to target directory, if omitted, a temporary
        folder is created instead
        :type target: str
        :param fs_type: File system type
        :type fs_type: str
        :param opts: Mount options separated by a comma such as:
        'sync,rw,guest'
        :type opts: str
        """
        super(MountPoint, self).__init__()
        self.fs = fs
        self.source = source
        self.opts = opts
        self.fs_type = fs_type
        self.target = target
        self._tmp = not bool(target)
        self._mounted = False

    def __enter__(self):
        self.mount()
        return self

    def __exit__(self, type_, value, tb):
        try:
            self.umount()
        except errors.MountError as e:
            self.logger.error(e)
            if not type_:
                raise

    def __str__(self):
        return (
            """
            Mounting point:
            source: {source}
            target: {target}
            file system: {fs}
            options: {opts}
            """.format(
                source=self.source,
                target=self.target or "*tmp*",
                fs=self.fs_type or "DEFAULT",
                opts=self.opts or "DEFAULT",
            )
        )

    def mount(self):
        if self._tmp:
            self.target = self.fs.mktemp(directory=True)
        cmd = ['mount', '-v']
        if self.fs_type:
            cmd.extend(['-t', self.fs_type])
        if self.opts:
            cmd.extend(['-o', self.opts])
        cmd.extend([self.source, self.target])
        rc, out, err = self.fs.host.run_command(cmd)
        if rc:
            raise errors.FailToMount(self, out, err)
        self._mounted = True

    def umount(self, force=True):
        cmd = ['umount', '-v']
        if force:
            cmd.append('-f')
        cmd.append(self.target)
        rc, out, err = self.fs.host.run_command(cmd)
        if rc:
            raise errors.FailToUmount(self, out, err)
        if self._tmp and not self.fs.listdir(self.target):
            self.fs.rmdir(self.target)
        self._mounted = False

    def remount(self, opts):
        """
        Remount disk

        'remount' option is implicit
        :param opts: Mount options separated by a comma such as:
        'sync,rw,guest'
        :type opts: str
        """
        if not self._mounted:
            raise errors.FailToRemount(self, '', 'not mounted!')
        cmd = ['mount', '-v']
        cmd.extend(['-o', 'remount,%s' % opts])
        cmd.append(self.target)
        rc, out, err = self.fs.host.run_command(cmd)
        if rc:
            raise errors.FailToRemount(self, out, err)
        self.opts = opts
