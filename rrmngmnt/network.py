import json
import logging
import netaddr
import os
import re
import shlex
import six
import subprocess
from rrmngmnt.errors import CommandExecutionFailure
from rrmngmnt.nmcli import NMCLI

from rrmngmnt.service import Service

logger = logging.getLogger(__name__)

IFCFG_PATH = "/etc/sysconfig/network-scripts/"


class _session(object):
    """
    It holds ssh session, in order to improve performance
    """
    def __init__(self, host):
        self._e = host.executor()
        self._s = None
        self._c = 0

    @property
    def executor(self):
        return self._e

    def runCmd(self, cmd):
        return self._s.run_cmd(cmd)

    def __enter__(self):
        self._c += 1
        if self._s is None:
            self._s = self._e.session()
            self._s.__enter__()

    def __exit__(self, *args, **kwargs):
        self._c -= 1
        if self._c == 0:
            _s = self._s
            self._s = None
            return _s.__exit__(*args, **kwargs)


def keep_session(func):
    @six.wraps(func)
    def _dec(self, *args, **kwargs):
        with self._m:
            return func(self, *args, **kwargs)
    return _dec


class HostnameHandler(object):
    """
    Handles hostname on <= RHEL6 systems

    Follows:
    http://www.putorius.net/2013/09/how-to-change-machines-hostname-in.html
    """
    def __init__(self, session):
        self._m = session

    @keep_session
    def get_hostname(self):
        """
        Get hostname

        Returns:
            str: Hostname
        """
        rc, out, _ = self._m.runCmd(['hostname', '-f'])
        if rc:
            return None
        return out.strip()

    @keep_session
    def set_hostname(self, name):
        """
        Set hostname persistently

        Args:
            name (str): Hostname to be set
        """
        net_config = '/etc/sysconfig/network'
        cmd = [
            'hostname', name, ';',
            'sed', '-i', '-e', '/^HOSTNAME/d', net_config, '&&',
            'echo', 'HOSTNAME=%s' % name, '>>', net_config
        ]
        rc, _, err = self._m.runCmd(cmd)
        if rc:
            raise Exception("Unable to set hostname: %s" % err)


class HostnameCtlHandler(HostnameHandler):
    """
    Handles hostname on >= RHEL7 systems

    Follows:
    http://www.itzgeek.com/how-tos/linux/centos-how-tos/
    change-hostname-in-centos-7-rhel-7.html#axzz3IkdUGHUl
    """
    @keep_session
    def get_hostname(self):
        """
        Get hostname

        Returns:
            str: Hostname
        """
        cmd = [
            'hostnamectl', 'status', '|',
            'grep', 'hostname', '|',
            'tr', '-d', ' ', '|',
            'cut', '-d:', '-f2'
        ]
        rc, out, _ = self._m.runCmd(cmd)
        if rc:
            return None
        return out.strip()

    @keep_session
    def set_hostname(self, name):
        """
        Set hostname persistently

        Args:
            name (str): Hostname to be set
        """
        cmd = ['hostnamectl', 'set-hostname', name]
        rc, _, err = self._m.runCmd(cmd)
        if rc:
            raise CommandExecutionFailure(
                self._m.executor, cmd, rc, "Unable to set hostname: %s" % err)


class Network(Service):
    def __init__(self, host):
        super(Network, self).__init__(host)
        self._m = _session(host)
        self._hnh = None
        self._nmcli = None

    @property
    def nmcli(self):
        if self._nmcli is None:
            self._nmcli = NMCLI(self.host)
        return self._nmcli

    @keep_session
    def _cmd(self, cmd):
        rc, out, err = self._m.runCmd(cmd)

        if rc:
            raise CommandExecutionFailure(
                self._m.executor, cmd, rc, "OUT: %s\nERR: %s" % (out, err))
        return out

    @keep_session
    def _get_hostname_handler(self):
        if self._hnh is None:
            # NOTE: this strategy can be changed, but right now there are
            # no other Handlers
            rc, out, err = self._m.runCmd(['which', 'hostnamectl'])
            if not rc:
                self._hnh = HostnameCtlHandler(self._m)
            else:
                self._hnh = HostnameHandler(self._m)
        return self._hnh

    @keep_session
    def _get_hostname(self):
        h = self._get_hostname_handler()
        return h.get_hostname()

    @keep_session
    def _set_hostname(self, name):
        h = self._get_hostname_handler()
        h.set_hostname(name)

    hostname = property(_get_hostname, _set_hostname)
    """
    Get / Set hostname (persistently)

    print(network.hostname)
    network.hostname = "new.hostname.com"
    """

    @keep_session
    def all_interfaces(self):
        """
        Lists interfaces

        Returns:
            list of strings: List of interfaces
        """
        out = self._cmd(
            "ls -la /sys/class/net | grep 'dummy_\\|pci' | grep -o '["
            "^/]*$'".split()
        )
        out = out.strip().splitlines()
        out.sort(key=lambda x: 'dummy_' in x)
        return out

    @keep_session
    def find_default_gw(self):
        """
        Find host default gateway

        Returns:
            str: Default gateway
        """
        out = self._cmd(["ip", "route"]).splitlines()
        for i in out:
            if re.search("default", i):
                default_gw = re.findall(r'[0-9]+(?:\.[0-9]+){3}', i)
                if netaddr.valid_ipv4(default_gw[0]):
                    return default_gw[0]
        return None

    @keep_session
    def find_default_gwv6(self):
        """
        Find host default ipv6 gateway

        Returns:
            str: Default gateway
        """
        out = self._cmd(["ip", "-6", "route"]).splitlines()
        for i in out:
            if re.search("default", i):
                default_gw = re.findall(
                    r'(?<=\s)[0-9a-fA-F:]{3,}(?=\s)', i
                )
                if netaddr.valid_ipv6(default_gw[0]):
                    return default_gw[0]
        return None

    @keep_session
    def find_ips(self):
        """
        Find host IPs

        Returns:
            tuple(list of strings, list of strings): List of ips and list of
                cird ips
        """
        ips = []
        ip_and_netmask = []
        out = self._cmd(["ip", "addr"]).splitlines()
        for i in out:
            cidr = re.findall(r'[0-9]+(?:\.[0-9]+){3}[/]+[0-9]{2}', i)
            if cidr:
                ip_and_netmask.append(cidr[0])
                ip = cidr[0].split("/")
                if netaddr.valid_ipv4(ip[0]):
                    ips.append(ip[0])
        return ips, ip_and_netmask

    @keep_session
    def find_ip_by_default_gw(self, default_gw, ips_and_mask):
        """
        Find IP by default gateway

        Args:
            ips_and_mask (list of strings): List of host ips with
                mask x.x.x.x/xx
            default_gw (str): Default gw of the host

        Returns:
            str: Ip
        """
        dgw = netaddr.IPAddress(default_gw)
        for ip_mask in ips_and_mask:
            ipnet = netaddr.IPNetwork(ip_mask)
            if dgw in ipnet:
                ip = ip_mask.split("/")[0]
                return ip
        return None

    @keep_session
    def find_int_by_ip(self, ip):
        """
        Find host interface or bridge by IP

        Args:
            ip (str): Ip of the interface to find

        Returns:
            str: Interface
        """
        out = self._cmd(["ip", "addr", "show", "to", ip])
        return out.split(":")[1].strip()

    @keep_session
    def find_ip_by_int(self, interface):
        """
        Find host ipv4 by interface or Bridge name

        Args:
            interface (str): Interface to get ip from

        Returns:
            str or None: Ip or none
        """
        out = self._cmd(["ip", "addr", "show", interface])
        match_ip = re.search(r'[0-9]+(?:\.[0-9]+){3}', out)
        if match_ip:
            interface_ip = match_ip.group()
            if netaddr.valid_ipv4(interface_ip):
                return interface_ip
        return None

    @keep_session
    def find_ipv6_by_int(self, interface):
        """
        Find host global ipv6 by interface or Bridge name

        Args:
            interface (str): Interface to get ipv6 from

        Returns:
            str or None: Ip or none
        """
        out = self._cmd(["ip", "-6", "addr", "show", interface])
        for line in out.splitlines():
            if re.search("global", line):
                match_ip = re.search(
                    r'(?<=\s)[0-9a-fA-F:]{3,}(?=/[0-9]{1,3}\s)',
                    line,
                )
                if match_ip:
                    interface_ip = match_ip.group()
                    if netaddr.valid_ipv6(interface_ip):
                        return interface_ip
        return None

    @keep_session
    def find_int_by_bridge(self, bridge):
        """
        Find host interface by Bridge name

        Args:
            bridge (str): Bridge to get ip from

        Returns:
            str: Interface
        """
        bridge = self.get_bridge(bridge)
        try:
            # FIXME: I think it is not correct implementation
            # what if there are more interfaces, what to do then?
            # I left it like this in order to preserve method-interface
            return bridge['interfaces'][0]
        except IndexError:
            return None

    @keep_session
    def find_mac_by_int(self, interfaces):
        """
        Find interfaces MAC by interface name

        Args:
            interfaces (list of strings): List of interfaces

        Returns:
            list of strings: List of macs
        """
        mac_list = list()
        for interface in interfaces:
            if interface not in self.all_interfaces():
                return False
            out = self._cmd(["ethtool", "-P", interface])
            mac = out.split(": ")[1]
            mac_list.append(mac.strip())
        return mac_list

    @keep_session
    def find_mgmt_interface(self):
        """
        Find host mgmt interface (interface with IP that lead to default
        gateway)

        Returns:
            str: Interface
        """
        host_ip = self.find_ips()
        host_dg = self.find_default_gw()
        host_ip_by_dg = self.find_ip_by_default_gw(host_dg, host_ip[1])
        mgmt_int = self.find_int_by_ip(host_ip_by_dg)
        return mgmt_int

    @keep_session
    def list_bridges(self):
        """
        List of bridges on host

        Returns:
            list of dict(name, id, stp, interfaces): List of bridges
        """
        bridges = []
        cmd = [
            'brctl', 'show', '|',
            'sed', '-e', '/^bridge name/ d',  # remove header
            # deal with multiple interfaces
            '-e', "'s/^\\s\\s*\\(\\S\\S*\\)$/CONT:\\1/I'"
        ]
        out = self._cmd(cmd).strip()
        if not out:
            # Empty list
            return bridges
        lines = out.splitlines()
        for line in lines:
            if line.startswith("CONT:"):
                bridge = bridges[-1]
                bridge['interfaces'].append(line[5:])
            else:
                line = line.split()
                bridge = {}
                bridge['name'] = line[0]
                bridge['id'] = line[1]
                bridge['stp'] = line[2]
                bridge['interfaces'] = []
                if len(line) == 4:
                    bridge['interfaces'].append(line[3])
                bridges.append(bridge)
        return bridges

    def get_bridge(self, name):
        """
        Find bridge by name

        Returns:
            dict(name, id, stp, interfaces): Bridge
        """
        bridges = [
            bridge for bridge in self.list_bridges()
            if bridge['name'] == name
        ]
        if bridges:
            return bridges[0]
        return None

    @keep_session
    def add_bridge(self, bridge, network):
        """
        Add bridge and add network to the bridge on host

        Args:
            bridge (str): Bridge name
            network (str): Network name

        Returns:
            bool: True/false
        """
        cmd_add_br = ["brctl", "addbr", bridge]
        cmd_add_if = ["brctl", "addif", bridge, network]
        self._cmd(cmd_add_br)
        self._cmd(cmd_add_if)
        return True

    @keep_session
    def delete_bridge(self, bridge):
        """
        Add bridge and add network to the bridge on host

        Args:
            bridge (str): Bridge name

        Returns:
            bool: True/false
        """
        cmd_br_down = ["ip", "link", "set", "down", bridge]
        cmd_del_br = ["brctl", "delbr", bridge]
        self._cmd(cmd_br_down)
        self._cmd(cmd_del_br)
        return True

    @keep_session
    def get_bridges(self):
        """
        Gets a host's bridges details using the 'bridge' command.

        Returns:
            list[dict]: a list of dicts where each dict represents a bridge,
                and has the keys:
                    * "ifname" -> str
                        The interface enslaved to the bridge.
                    * "flags" -> list[str]
                        A list of flags associated with the bridge.
                    * "mtu" -> int
                        The MTU configured on the bridge.
                    * "master" -> str
                        The bridge name.
                    * "state" -> str
                    * "priority" -> int
                    * "cost" -> int
                    * "ifindex" -> int
        """
        raw_bridges = self._cmd(shlex.split("bridge -j link show"))
        return json.loads(s=raw_bridges)

    @keep_session
    def get_info(self):
        """
        Get network info for host, return info for main IP.

        Returns:
            dict: Network info
        """
        net_info = {}
        gateway = self.find_default_gw()
        net_info["gateway"] = gateway
        ips, ips_and_mask = self.find_ips()
        if gateway is not None:
            ip = self.find_ip_by_default_gw(gateway, ips_and_mask)
            net_info["ip"] = ip
            if ip is not None:
                mask = [
                    mask.split("/")[-1] for mask in ips_and_mask if ip in mask
                ]
                net_info["prefix"] = mask[0] if mask else "N/A"
                interface = self.find_int_by_ip(ip)
                # strip @NONE for PPC
                try:
                    interface = interface.strip(
                        re.findall(r'@.*', interface)[0]
                    )
                except IndexError:
                    pass
                bridge = self.get_bridge(interface)
                if bridge is not None:
                    net_info["bridge"] = bridge['name']
                    interface = self.find_int_by_bridge(bridge['name'])
                    net_info["interface"] = interface
                else:
                    net_info["bridge"] = "N/A"
                    net_info["interface"] = interface

        return net_info

    def create_ifcfg_file(self, nic, params, ifcfg_path=IFCFG_PATH):
        """
        Create ifcfg file

        Args:
            nic (str): Nic name
            ifcfg_path (str): Ifcfg files path
            params (dict): Ifcfg file content
        """
        dst = os.path.join(ifcfg_path, "ifcfg-%s" % nic)
        self.logger.info("Creating %s on %s", dst, self.host.fqdn)
        with self.host.executor().session() as resource_session:
            with resource_session.open_file(dst, 'w') as resource_file:
                resource_file.write("DEVICE=%s\n" % nic)
                for k, v in six.iteritems(params):
                    resource_file.write("%s=%s\n" % (k, v))

    def delete_ifcfg_file(self, nic, ifcfg_path=IFCFG_PATH):
        """
        Delete ifcfg file

        Args:
            nic (str): Nic name
            ifcfg_path (str): Ifcfg files path

        Returns:
            bool: True/false
        """
        dst = os.path.join(ifcfg_path, "ifcfg-%s" % nic)
        logger.info("Delete %s ", dst)
        if not self.host.fs.remove(dst):
            logger.error("Failed to delete %s", dst)
            return False
        return True

    def send_icmp(self, dst, count="5", size=None, extra_args=None):
        """
        Send ICMP to destination IP/FQDN

        Args:
            count (str): Number of icmp packets to send
            extra_args (str): Extra args for ping command
            dst (str): Ip/fqdn to send icmp to
            size (str): Size of the icmp packet

        Returns:
            bool: True/false
        """
        cmd = ["ping", dst, "-c", count]
        if size:
            cmd.extend(["-s", size, "-M", "do"])
        if extra_args:
            for ar in extra_args.split():
                cmd.extend(ar.split())
        try:
            self._cmd(cmd)
        except Exception as e:
            logger.error(e)
            return False
        return True

    def set_mtu(self, nics, mtu="1500"):
        """
        Set MTU on NICs

        Args:
            nics (list): List on nics
            mtu (str): Mtu size

        Returns:
            bool or Exception: True or raise exception
        """
        base_cmd = "ip link set mtu %s %s"
        for nic in nics:
            str_cmd = base_cmd % (mtu, nic)
            self._cmd(shlex.split(str_cmd))
        return True

    def delete_interface(self, interface):
        """
        Delete interface from host

        Args:
            interface (str): Interface name

        Returns:
            bool: True/false
        """
        cmd = "ip link del %s" % interface
        try:
            logger.info("Delete %s interface", interface)
            self._cmd(shlex.split(cmd))
        except Exception as e:
            logger.error(e)
            return False
        return True

    def get_mac_by_ip(self, ip):
        """
        Get mac address by ip address

        Args:
            ip (str): Ip address

        Returns:
            str: Mac address
        """
        interface = self.find_int_by_ip(ip=ip)
        return self.find_mac_by_int([interface])[0]

    def if_up(self, nic):
        """
        Set nic up

        Args:
            nic (str): Nic name

        Returns:
            bool: True if setting nic up succeeded, false otherwise
        """
        cmd = "ip link set {nic} up".format(nic=nic)
        rc, _, _ = self.host.run_command(shlex.split(cmd))
        return not bool(rc)

    def if_down(self, nic, tcp_timeout=20, io_timeout=20):
        """
        Set nic down

        Args:
            nic (str): Nic name
            tcp_timeout (float): TCP timeout
            io_timeout (float): Timeout for data operation (read/write)

        Returns:
            bool: True if setting nic down succeeded, false otherwise
        """
        cmd = "ip link set {nic} down".format(nic=nic)
        rc, _, _ = self.host.run_command(
            command=shlex.split(cmd),
            tcp_timeout=tcp_timeout,
            io_timeout=io_timeout
        )
        return not bool(rc)

    def add_ip(self, nic, ip, mask):
        """
        Add IP address to interface

        Args:
            nic (str): Interface name
            ip (str): IP address to add
            mask (str): IP netmask

        Returns:
            bool: True if add IP was success, False otherwise
        """
        cmd = "ip address add {ip}/{mask} dev {nic}".format(
            ip=ip, mask=mask, nic=nic
        )
        return not bool(self.host.run_command(command=shlex.split(cmd))[0])

    def is_connective(self, ping_timeout=20.0):
        """
        Check if host network is connective via ping command

        Args:
            ping_timeout (float): Time to wait for response

        Returns:
            bool: True if address is connective via ping command, false
             otherwise
        """
        host_address = self.host.ip
        # Leave it for future support of IPV6
        ping_cmd = "ping6" if netaddr.valid_ipv6(self.host.ip) else "ping"
        self.logger.info(
            "Check if address is connective via ping in given timeout %s",
            ping_timeout
        )
        command = [
            ping_cmd,
            "-c", "1",
            "-w", str(ping_timeout),
            host_address
        ]
        p = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, _ = p.communicate()
        if p.returncode:
            self.logger.debug(
                "Failed to ping address %s: %s", host_address, out
            )
            return False
        return True

    def get_interface_speed(self, interface):
        """
        Get network interface speed

        Args:
            interface (str): Interface name

        Returns:
            str: Interface speed, or empty string if error has occurred
        """
        ethtool_cmd = "ethtool -i {iface}".format(iface=interface)
        self._cmd(shlex.split(ethtool_cmd))
        speed_cmd = "cat /sys/class/net/{iface}/speed".format(iface=interface)
        out = self._cmd(shlex.split(speed_cmd))
        return out.strip()

    def get_interface_status(self, interface):
        """
        Get interface status

        Args:
            interface (str): Interface name

        Returns:
            str: Interface status (up/down)
        """
        cmd = "cat /sys/class/net/{iface}/operstate".format(iface=interface)
        out = self._cmd(shlex.split(cmd))
        return out.strip()
