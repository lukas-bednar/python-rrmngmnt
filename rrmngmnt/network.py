import logging
import netaddr
import os
import re
import shlex
import six
import subprocess

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
        :return: hostname
        :rtype: string
        """
        rc, out, _ = self._m.runCmd(['hostname', '-f'])
        if rc:
            return None
        return out.strip()

    @keep_session
    def set_hostname(self, name):
        """
        Set hostname persistently
        :param name: hostname to be set
        :type name: string
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
        :return: hostname
        :rtype: string
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
        :param name: hostname to be set
        :type name: string
        """
        cmd = ['hostnamectl', 'set-hostname', name]
        rc, _, err = self._m.runCmd(cmd)
        if rc:
            raise Exception("Unable to set hostname: %s" % err)


class Network(Service):
    def __init__(self, host):
        super(Network, self).__init__(host)
        self._m = _session(host)
        self._hnh = None

    @keep_session
    def _cmd(self, cmd):
        rc, out, err = self._m.runCmd(cmd)

        if rc:
            cmd_out = " ".join(cmd)
            raise Exception(
                "Fail to run command %s: %s ; %s" % (cmd_out, out, err))
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

        :return: list of interfaces
        :rtype: list of strings
        """
        out = self._cmd(
            "ls -la /sys/class/net | grep 'dummy_\|pci' | grep -o '["
            "^/]*$'".split()
        )
        out = out.strip().splitlines()
        out.sort(key=lambda x: 'dummy_' in x)
        return out

    @keep_session
    def find_default_gw(self):
        """
        Find host default gateway

        :return: default gateway
        :rtype: string
        """
        out = self._cmd(["ip", "route"]).splitlines()
        for i in out:
            if re.search("default", i):
                default_gw = re.findall(r'[0-9]+(?:\.[0-9]+){3}', i)
                if netaddr.valid_ipv4(default_gw[0]):
                    return default_gw[0]
        return None

    @keep_session
    def find_ips(self):
        """
        Find host IPs

        :return: list of ips and list of cird ips
        :rtype: tuple(list of strings, list of strings)
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

        :param default_gw: default gw of the host
        :type default_gw: string
        :param ips_and_mask: list of host ips with mask x.x.x.x/xx
        :type ips_and_mask: list of strings
        :return: ip
        :rtype: string
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

        :param ip: ip of the interface to find
        :type ip: string
        :return: interface
        :rtype: string
        """
        out = self._cmd(["ip", "addr", "show", "to", ip])
        return out.split(":")[1].strip()

    @keep_session
    def find_ip_by_int(self, interface):
        """
        Find host interface by interface or Bridge name

        :param interface: interface to get ip from
        :type interface: string
        :return: IP or None
        :rtype: string or None
        """
        out = self._cmd(["ip", "addr", "show", interface])
        match_ip = re.search(r'[0-9]+(?:\.[0-9]+){3}', out)
        if match_ip:
            interface_ip = match_ip.group()
            if netaddr.valid_ipv4(interface_ip):
                return interface_ip
        return None

    @keep_session
    def find_int_by_bridge(self, bridge):
        """
        Find host interface by Bridge name

        :param bridge: bridge to get ip from
        :type bridge: string
        :return: interface
        :rtype: string
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

        :param interfaces: list of interfaces
        :type interfaces: list of strings
        :return: list of macs
        :rtype: list of strings
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
        Find host mgmt interface (interface with IP that lead
        to default gateway)

        :return: interface
        :rtype: string
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

        :return: list of bridges
        :rtype: list of dict(name, id, stp, interfaces)
        """
        bridges = []
        cmd = [
            'brctl', 'show', '|',
            'sed', '-e', '/^bridge name/ d',  # remove header
            # deal with multiple interfaces
            '-e', "'s/^\s\s*\(\S\S*\)$/CONT:\\1/I'"
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

        :return: bridge
        :rtype: dict(name, id, stp, interfaces)
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

        :param bridge: Bridge name
        :type bridge: str
        :param network: Network name
        :type network: str
        :return: True/False
        :rtype: bool
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

        :param bridge: Bridge name
        :type bridge: str
        :return: True/False
        :rtype: bool
        """
        cmd_br_down = ["ip", "link", "set", "down", bridge]
        cmd_del_br = ["brctl", "delbr", bridge]
        self._cmd(cmd_br_down)
        self._cmd(cmd_del_br)
        return True

    @keep_session
    def get_info(self):
        """
        Get network info for host, return info for main IP.

        :return: network info
        :rtype: dict
        """
        net_info = {}
        gateway = self.find_default_gw()
        net_info["gateway"] = gateway
        ips, ips_and_mask = self.find_ips()
        if gateway is not None:
            ip = self.find_ip_by_default_gw(gateway, ips_and_mask)
            net_info["ip"] = ip
            if ip is not None:
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

        :param nic: NIC name
        :type nic: str
        :param params: Ifcfg file content
        :type params: dict
        :param ifcfg_path: Ifcfg files path
        :type ifcfg_path: str
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

        :param nic: NIC name
        :type nic: str
        :param ifcfg_path: Ifcfg files path
        :type ifcfg_path: str
        :return: True/False
        :rtype: bool
        """
        dst = os.path.join(ifcfg_path, "ifcfg-%s" % nic)
        logger.info("Delete %s ", dst)
        if not self.host.fs.remove(dst):
            logger.error("Failed to delete %s", dst)
            return False
        return True

    def send_icmp(self, dst, count="5", size="1500", extra_args=None):
        """
        Send ICMP to destination IP/FQDN

        :param dst: IP/FQDN to send ICMP to
        :type dst: str
        :param count: Number of ICMP packets to send
        :type count: str
        :param size: Size of the ICMP packet
        :type size: str
        :param extra_args: Extra args for ping command
        :type extra_args: str
        :return: True/False
        :rtype: bool
        """
        cmd = ["ping", dst, "-c", count, "-s", size]
        if size != "1500":
            cmd.extend(["-M", "do"])
        if extra_args is not None:
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

        :param nics: List on NICs
        :type nics: list
        :param mtu: MTU size
        :type mtu: str
        :return: True or raise Exception
        :rtype: bool or Exception
        """
        base_cmd = "ip link set mtu %s %s"
        for nic in nics:
            str_cmd = base_cmd % (mtu, nic)
            self._cmd(shlex.split(str_cmd))
        return True

    def delete_interface(self, interface):
        """
        Delete interface from host

        :param interface: Interface name
        :type interface: str
        :return: True/False
        :rtype: bool
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

        :param ip: ip address
        :type ip: str
        :return: mac address
        :rtype: str
        """
        interface = self.find_int_by_ip(ip=ip)
        return self.find_mac_by_int([interface])[0]

    def if_up(self, nic):
        """
        Set nic up

        :param nic: NIC name
        :type nic: str
        :return: True if setting NIC up succeeded, False otherwise
        :rtype: bool
        """
        cmd = "ip link set up %s" % nic
        rc, _, _ = self.host.run_command(shlex.split(cmd))
        return not bool(rc)

    def if_down(self, nic):
        """
        Set nic down

        :param nic: NIC name
        :type nic: str
        :return: True if setting NIC down succeeded, False otherwise
        :rtype: bool
        """
        cmd = "ip link set down %s" % nic
        rc, _, _ = self.host.run_command(shlex.split(cmd))
        return not bool(rc)

    def is_connective(self, ping_timeout=20.0):
        """
        Check if host network is connective via ping command

        :param ping_timeout: time to wait for response
        :type ping_timeout: float
        :return: True if address is connective via ping command,
            False otherwise
        :rtype: bool
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
