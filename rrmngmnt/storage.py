import logging
import shlex
from rrmngmnt.service import Service

logger = logging.getLogger(__name__)

LV_CHANGE_CMD = 'lvchange -a %s %s/%s'


class NFSService(Service):
    """
    Storage management class to maintain NFS services
    """

    def mount(self, source, target=None, opts=None):
        """
        Mounts source to target mount point

        __author__ = "ratamir"

        Args:
            source (str): Full path to source
            target (str): Path to target directory, if omitted, a temporary
                folder is created instead
            opts (list): List of mount options such as

        Returns:
            str: Path to mount point if succeeded, none otherwise
        """
        target = '/tmp/mnt_point' if target is None else target
        cmd = ['mkdir', '-p', target]
        self.logger.info(
            "Creating directory %s to use as a mount point", target
        )
        rc, out, err = self.host.run_command(cmd)
        if rc:
            self.logger.error(
                "Failed to create a directory to be used as a mount point "
                "for %s. Output: %s, Error: %s ", source, out, err
            )
            return None

        cmd = ['mount', source, target]
        if opts:
            cmd.extend(opts)
        rc, out, err = self.host.run_command(cmd)
        if rc:
            self.logger.error(
                "Failed to mount source %s to target %s. Output: %s",
                source, target, out
            )
            return None
        return target

    def umount(self, mount_point, force=True, remove_mount_point=True):
        """
        Performs an 'umount' on input 'mount_point' directory, and
        optionally removes 'mount_point'

        __author__ = "ratamir"

        Args:
            mount_point (str): Path to directory that should be unmounted
            force (bool): True if the mount point should be forcefully removed
                (such as in the case of an unreachable nfs server)
            remove_mount_point (bool): True if mount point should be deleted
                after 'umount' operation completes, false otherwise

        Returns:
            bool: True if umount operation and mount point removal succeeded,
                false otherwise
        """
        cmd = ['umount', mount_point, '-v']
        if force:
            cmd.append('-f')
        rc, out, err = self.host.run_command(cmd)
        if rc:
            self.logger.error(
                "failed to umount directory: %s, output: %s, error: %s",
                mount_point, out, err
            )
            return False
        if remove_mount_point:
            rc = self.host.fs.rmdir(mount_point)
            if not rc:
                self.logger.error("failed to remove directory %s", mount_point)
                return False
        return True


class LVMService(Service):
    """
    Storage management class to maintain LVM services
    """
    def lvchange(self, vg_name, lv_name, activate=True):
        """
        Activate or deactivate a Logical volume
        (by setting it's 'active' attribute)

        __author__ = "ratamir"

        Args:
            activate (bool): True when the logical volume should be activated,
                false when it should be deactivated
            vg_name (str): The name of the volume group under which the lv
                resides
            lv_name (str): The name of the logical volume which will be
                activated or deactivated

        Returns:
            bool: True if setting the logical volume 'active' flag succeeded,
                false otherwise
        """
        active = 'y' if activate else 'n'
        return self.host.run_command(
            shlex.split(LV_CHANGE_CMD % (active, vg_name, lv_name))
        )[0] == 0

    def pvscan(self):
        """
        Execute 'pvscan' in order to get the current list of physical volumes

        __author__ = "ratamir"

        Returns:
            bool: True if the pvscan command succeded, false otherwise
        """
        return self.host.run_command(['pvscan'])[0] == 0
