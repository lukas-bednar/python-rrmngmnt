# -*- coding: utf-8 -*-
"""
This module introduces support for the nmcli command which is provided by
NetworkManager.
"""
import shlex

from rrmngmnt.errors import CommandExecutionFailure
from rrmngmnt.service import Service


class Objects:
    CONNECTION = "connection"
    DEVICE = "device"


class Operations:
    ADD = "add"
    MODIFY = "modify"
    DELETE = "delete"
    SHOW = "show"


class NmGeneralSettings:
    _prefix = "GENERAL.{setting}"
    DEVICE = _prefix.format(setting="DEVICE")
    TYPE = _prefix.format(setting="TYPE")
    MAC = _prefix.format(setting="HWADDR")
    MTU = _prefix.format(setting="MTU")


class ObjectDetails:
    NAME = "name"
    TYPE = "type"


class ConnectionDetails(ObjectDetails):
    UUID = "uuid"
    DEVICE = "device"


class DeviceDetails(ObjectDetails):
    MAC = "mac"
    MTU = "mtu"


class Types:
    ETHERNET = "ethernet"
    BOND = "bond"
    VLAN = "vlan"
    DUMMY = "dummy"


class EthernetOptions:
    MAC = "mac"
    MTU = "mtu"


class BondOptions:
    MODE = "mode"
    MIIMON = "miimon"
    PRIMARY = "primary"


class SlaveOptions:
    MASTER = "master"


class VlanOptions:
    DEV = "dev"
    ID = "id"
    MTU = "mtu"


class NMCLI(Service):
    """
    This class implements network operations using nmcli.
    """

    def __init__(self, host):
        super(NMCLI, self).__init__(host)
        self._executor = host.executor()

    def _exec_command(self, command):
        """
        Executes a command on the remote host.

        Args:
            command (str): a command to run remotely.

        Returns:
            str: command execution output.

        Raises:
            CommandExecutionFailure: if the remote host returned a code
                indicating a failure in execution.
        """
        split = shlex.split(command)

        rc, out, err = self._executor.run_cmd(split)

        if rc != 0:
            self.logger.error(
                f"\n"
                f"command -> {command}\n"
                f"RC -> {rc}\n"
                f"OUT -> {out}\n"
                f"ERROR -> {err}"
            )
            raise CommandExecutionFailure(
                executor=self._executor, cmd=split, rc=rc, err=err
            )
        return out

    def get_all_connections(self):
        """
        Gets existing NetworkManager profiles details.

        Returns:
            list[dict]: each dict in the returned list represents a profile,
                and has the following keys:
                    - "name"
                    - "uuid"
                    - "type"
                    - "device"

        Raises:
            CommandExecutionFailure: if the remote host returned a code
                indicating a failure in execution.
        """
        connections = []

        out = self._exec_command(
            command=f"nmcli -t {Objects.CONNECTION} {Operations.SHOW}"
            )

        for line in out.splitlines():
            properties = line.split(":")
            connections.append(
                {
                    ConnectionDetails.NAME: properties[0],
                    ConnectionDetails.UUID: properties[1],
                    ConnectionDetails.TYPE: properties[2],
                    ConnectionDetails.DEVICE: properties[3],
                }
            )

        return connections

    def get_all_devices(self):
        """
        Gets existing devices details.

        Returns:
            list[dict]: each dict in the returned list represents a device,
                and has the following keys:
                    - "name"
                    - "type"
                    - "mac"
                    - "mtu"
        Raises:
            CommandExecutionFailure: if the remote host returned a code
                indicating a failure in execution.
        """
        device_names = self._exec_command(
            command=f"nmcli -g {NmGeneralSettings.DEVICE} {Objects.DEVICE} "
                    f"{Operations.SHOW}"
        )
        device_names = [
            name for name in device_names.splitlines() if name != ""
        ]

        devices = []

        for name in device_names:
            out = self._exec_command(
                command=(
                    f"nmcli -e no "
                    f"-g {NmGeneralSettings.TYPE},{NmGeneralSettings.MAC},"
                    f"{NmGeneralSettings.MTU} "
                    f"{Objects.DEVICE} {Operations.SHOW} {name}"
                )
            )
            properties = out.splitlines()
            devices.append(
                {
                    DeviceDetails.NAME: name,
                    DeviceDetails.TYPE: properties[0],
                    DeviceDetails.MAC: properties[1],
                    DeviceDetails.MTU: properties[2],
                }
            )

        return devices

    def set_connection_state(self, connection, state):
        """
        Sets a connection's state.

        Args:
            connection (str): name, UUID or path.
            state (str): the desired state.
                available states are: ["up", "down"].

        Raises:
            CommandExecutionFailure: if the remote host returned a code
                indicating a failure in execution.
        """
        self._exec_command(
            command=f"nmcli {Objects.CONNECTION} {state} {connection}"
        )

    def add_ethernet_connection(
        self,
        name,
        ifname,
        auto_connect=None,
        save=None,
        mac=None,
        mtu=None,
        ipv4_method=None,
        ipv4_addr=None,
        ipv4_gw=None,
        ipv6_method=None,
        ipv6_addr=None,
        ipv6_gw=None,
    ):
        """
        Creates an ETHERNET connection.

        Args:
            name (str): the created connection's name.
            ifname (str): the interface name to use.
            auto_connect (bool): True to connect automatically, or False for
                manual.
            save (bool): True to persist the connection, or False.
            mac (str): MAC address to set for the connection.
            mtu (int): MTU to set for the connection.
            ipv4_method (str): setting method.
                Available methods: auto, disabled, link-local, manual, shared.
            ipv4_addr (str): a static address.
            ipv4_gw (str): a gateway address.
            ipv6_method (str): setting method.
                Available methods: auto, dhcp, disabled, ignore, link-local,
                manual, shared.
            ipv6_addr (str): a static address.
            ipv6_gw (str): a gateway address.

        Raises:
            CommandExecutionFailure: if the remote host returned a code
                indicating a failure in execution.
        """
        type_options = {}
        if mac:
            type_options[EthernetOptions.MAC] = mac
        if mtu:
            type_options[EthernetOptions.MTU] = mtu

        self._exec_command(
            command=self._nmcli_cmd_builder(
                object_type=Objects.CONNECTION,
                operation=Operations.ADD,
                con_type=Types.ETHERNET,
                name=name,
                ifname=ifname,
                auto_connect=auto_connect,
                save=save,
                ipv4_method=ipv4_method,
                ipv4_addr=ipv4_addr,
                ipv4_gw=ipv4_gw,
                ipv6_method=ipv6_method,
                ipv6_addr=ipv6_addr,
                ipv6_gw=ipv6_gw,
                type_options=type_options,
            )
        )

    def add_bond(
        self,
        con_name,
        ifname,
        mode=None,
        primary=None,
        miimon=None,
        auto_connect=None,
        save=None,
        ipv4_method=None,
        ipv4_addr=None,
        ipv4_gw=None,
        ipv6_method=None,
        ipv6_addr=None,
        ipv6_gw=None,
    ):
        """
        Creates a bond connection.

        Args:
            con_name (str): the created connection's name.
            ifname (str): the created bond's name.
            mode (str): bond mode.
                Available modes are: balance-rr (0) | active-backup (1) |
                balance-xor (2) | broadcast (3)
                802.3ad (4) | balance-tlb (5) | balance-alb (6)
            primary (str): the primary slave name (to be used with mode 1).
            miimon (int): specifies (in milliseconds) how often MII link
                monitoring occurs.
            auto_connect (bool): True to connect automatically, or False for
                manual.
            save (bool): True to persist the connection, or False.
            ipv4_method (str): setting method.
                Available methods: auto, disabled, link-local, manual, shared.
            ipv4_addr (str): a static address.
            ipv4_gw (str): a gateway address.
            ipv6_method (str): setting method.
                Available methods: auto, dhcp, disabled, ignore, link-local,
                manual, shared.
            ipv6_addr (str): a static address.
            ipv6_gw (str): a gateway address.

        Raises:
            CommandExecutionFailure: if the remote host returned a code
                indicating a failure in execution.

        Notes:
            The parameters [ipv4_addr, ipv4_gw, ipv6_addr, ipv6_gw] are to be
            used with a 'manual' IP method respectively.
        """
        type_options = {}
        if mode:
            type_options[BondOptions.MODE] = mode
        if miimon:
            type_options[BondOptions.MIIMON] = miimon
        if primary:
            type_options[BondOptions.PRIMARY] = primary

        self._exec_command(
            command=self._nmcli_cmd_builder(
                object_type=Objects.CONNECTION,
                operation=Operations.ADD,
                con_type=Types.BOND,
                name=con_name,
                ifname=ifname,
                auto_connect=auto_connect,
                save=save,
                ipv4_method=ipv4_method,
                ipv4_addr=ipv4_addr,
                ipv4_gw=ipv4_gw,
                ipv6_method=ipv6_method,
                ipv6_addr=ipv6_addr,
                ipv6_gw=ipv6_gw,
                type_options=type_options,
            )
        )

    def add_slave(
        self,
        con_name,
        slave_type,
        ifname,
        master=None,
        auto_connect=None,
        save=None,
        ipv4_method=None,
        ipv4_addr=None,
        ipv4_gw=None,
        ipv6_method=None,
        ipv6_addr=None,
        ipv6_gw=None,
    ):
        """
        Creates a bond slave.

        Args:
            con_name (str): the created connection's name.
            slave_type (str): the type of slave device.
            ifname (str): the created bond's name.
            master (str): ifname, connection UUID or name.
            auto_connect (bool): True to connect automatically, or False for
                manual.
            save (bool): True to persist the connection, or False.
            ipv4_method (str): setting method.
                Available methods: auto, disabled, link-local, manual, shared.
            ipv4_addr (str): a static address.
            ipv4_gw (str): a gateway address.
            ipv6_method (str): setting method.
                Available methods: auto, dhcp, disabled, ignore, link-local,
                manual, shared.
            ipv6_addr (str): a static address.
            ipv6_gw (str): a gateway address.

        Raises:
            CommandExecutionFailure: if the remote host returned a code
                indicating a failure in execution.
        """
        type_options = {}
        if master:
            type_options = {SlaveOptions.MASTER: master}

        self._exec_command(
            command=self._nmcli_cmd_builder(
                object_type=Objects.CONNECTION,
                operation=Operations.ADD,
                con_type=slave_type,
                name=con_name,
                ifname=ifname,
                auto_connect=auto_connect,
                save=save,
                ipv4_method=ipv4_method,
                ipv4_addr=ipv4_addr,
                ipv4_gw=ipv4_gw,
                ipv6_method=ipv6_method,
                ipv6_addr=ipv6_addr,
                ipv6_gw=ipv6_gw,
                type_options=type_options,
            )
        )

    def add_vlan(
        self,
        con_name,
        dev,
        vlan_id,
        mtu=None,
        auto_connect=None,
        save=None,
        ipv4_method=None,
        ipv4_addr=None,
        ipv4_gw=None,
        ipv6_method=None,
        ipv6_addr=None,
        ipv6_gw=None,
    ):
        """
        Creates a VLAN connection.

        Args:
            con_name (str): the created connection's name.
            dev (str): parent device.
            vlan_id (int): VLAN ID.
            mtu (int): MTU to set for the connection.
            auto_connect (bool): True to connect automatically, or False for
                manual.
            save (bool): True to persist the connection, or False.
            ipv4_method (str): setting method.
                Available methods: auto, disabled, link-local, manual, shared.
            ipv4_addr (str): a static address.
            ipv4_gw (str): a gateway address.
            ipv6_method (str): setting method.
                Available methods: auto, dhcp, disabled, ignore, link-local,
                manual, shared.
            ipv6_addr (str): a static address.
            ipv6_gw (str): a gateway address.

        Raises:
            CommandExecutionFailure: if the remote host returned a code
                indicating a failure in execution.
        """
        type_options = {VlanOptions.DEV: dev, VlanOptions.ID: vlan_id}
        if mtu:
            type_options[VlanOptions.MTU] = mtu

        self._exec_command(
            command=self._nmcli_cmd_builder(
                object_type=Objects.CONNECTION,
                operation=Operations.ADD,
                con_type=Types.VLAN,
                name=con_name,
                auto_connect=auto_connect,
                save=save,
                ipv4_method=ipv4_method,
                ipv4_addr=ipv4_addr,
                ipv4_gw=ipv4_gw,
                ipv6_method=ipv6_method,
                ipv6_addr=ipv6_addr,
                ipv6_gw=ipv6_gw,
                type_options=type_options,
            )
        )

    def add_dummy(
        self,
        con_name,
        ifname,
        auto_connect=None,
        save=None,
        ipv4_method=None,
        ipv4_addr=None,
        ipv4_gw=None,
        ipv6_method=None,
        ipv6_addr=None,
        ipv6_gw=None,
    ):
        """
        Creates a dummy connection.

        Args:
            con_name (str): the created connection's name.
            ifname (str): the interface name to use.
            auto_connect (bool): True to connect automatically, or False for
                manual.
            save (bool): True to persist the connection, or False.
            ipv4_method (str): setting method.
                Available methods: auto, disabled, link-local, manual, shared.
            ipv4_addr (str): a static address.
            ipv4_gw (str): a gateway address.
            ipv6_method (str): setting method.
                Available methods: auto, dhcp, disabled, ignore, link-local,
                manual, shared.
            ipv6_addr (str): a static address.
            ipv6_gw (str): a gateway address.

        Raises:
            CommandExecutionFailure: if the remote host returned a code
                indicating a failure in execution.
        """
        self._exec_command(
            command=self._nmcli_cmd_builder(
                object_type=Objects.CONNECTION,
                operation=Operations.ADD,
                con_type=Types.DUMMY,
                name=con_name,
                ifname=ifname,
                auto_connect=auto_connect,
                save=save,
                ipv4_method=ipv4_method,
                ipv4_addr=ipv4_addr,
                ipv4_gw=ipv4_gw,
                ipv6_method=ipv6_method,
                ipv6_addr=ipv6_addr,
                ipv6_gw=ipv6_gw,
            )
        )

    def modify_connection(self, connection, properties):
        """
        Modifies a connection.

        Args:
            connection (str): name, UUID or path.
            properties (dict): properties mapping to values

        Raises:
            CommandExecutionFailure: if the remote host returned a code
                indicating a failure in execution.

        Notes:
            For multi-value properties e.g: ipv4.addresses, it is possible to
            pass a property key with a '+' prefix to append a value e.g:
            {"+ipv4.addresses": "192.168.23.2"}, or a '-' in order to remove
            a property.
        """
        self._exec_command(
            command=self._nmcli_cmd_builder(
                object_type=Objects.CONNECTION,
                operation=Operations.MODIFY,
                name=connection,
                type_options=properties,
            )
        )

    def delete_connection(self, connection):
        """
        Deletes a connection.

        Args:
            connection (str): name, UUID or path.

        Raises:
            CommandExecutionFailure: if the remote host returned a code
                indicating a failure in execution.
        """
        self._exec_command(
            command=self._nmcli_cmd_builder(
                object_type=Objects.CONNECTION,
                operation=Operations.DELETE,
                name=connection,
            )
        )

    def modify_device(self, device, properties):
        """
        Modifies a connection.

        Args:
            device (str): device name.
            properties (dict): properties mapping to values

        Raises:
            CommandExecutionFailure: if the remote host returned a code
                indicating a failure in execution.

        Notes:
            For multi-value properties e.g: ipv4.addresses, it is possible to
            pass a property key with a '+' prefix to append a value e.g:
            {"+ipv4.addresses": "192.168.23.2"}, or a '-' in order to remove
            a property.
        """
        self._exec_command(
            command=self._nmcli_cmd_builder(
                object_type=Objects.DEVICE,
                operation=Operations.MODIFY,
                name=device,
                type_options=properties,
            )
        )

    @staticmethod
    def _ip_options_builder(
        ipv4_addr, ipv4_gw, ipv4_method, ipv6_addr, ipv6_gw, ipv6_method
    ):
        """
        Extends an nmcli command with IP options.

        Args:
            ipv4_addr (str): a static address.
            ipv4_gw (str): a gateway address.
            ipv4_method (str): setting method.
                Available methods: auto, disabled, link-local, manual, shared.
            ipv6_addr (str): a static address.
            ipv6_gw (str): a gateway address.
            ipv6_method (str): setting method.
                Available methods: auto, dhcp, disabled, ignore, link-local,
                manual, shared.

        Returns:
            str: a substring of the nmcli command formatted with IP options.
        """
        command = ""

        if ipv4_method:
            command += f" ipv4.method {ipv4_method}"
        if ipv6_method:
            command += f" ipv6.method {ipv6_method}"
        if ipv4_addr:
            command += f" ipv4.addresses {ipv4_addr}"
        if ipv4_gw:
            command += f" ipv4.gateway {ipv4_gw}"
        if ipv6_addr:
            command += f" ipv6.addresses {ipv6_addr}"
        if ipv6_gw:
            command += f" ipv6.gateway {ipv6_gw}"
        return command

    @staticmethod
    def _common_options_builder(
        con_type, con_name, ifname=None, auto_connect=None, save=None
    ):
        """
        Generates a string containing common options for the nmcli command.

        Args:
            con_type (str): the connection type.
            con_name (str): the created connection's name.
            ifname (str): the interface name to use.
            auto_connect (bool): True to connect automatically, or False for
                manual.
            save (bool): True to persist the connection, or False.

        Returns:
            str: a common options string.
        """

        def _get_str_value(value):
            """
            Returns the str representation of a bool value.
            """
            return "yes" if value is True else "no"

        common_options = f"type {con_type} con-name {con_name}"

        if ifname:
            common_options += f" ifname {ifname}"
        if auto_connect is not None:
            common_options += (
                f" autoconnect {_get_str_value(value=auto_connect)}"
            )
        if save is not None:
            common_options += f" save {_get_str_value(value=save)}"

        return common_options

    def _nmcli_cmd_builder(
        self,
        object_type,
        operation,
        name,
        con_type=None,
        ifname=None,
        auto_connect=None,
        save=None,
        ipv4_method=None,
        ipv4_addr=None,
        ipv4_gw=None,
        ipv6_method=None,
        ipv6_addr=None,
        ipv6_gw=None,
        type_options=None,
    ):
        """
        Builds an nmcli command.

        Args:
            object_type (str): "connection" / "device".
            operation (str): the operation to perform. e.g: "add", "delete" ...
            name (str): connection/device name.
            con_type (str): the connection type. e.g: "ethernet", "bond" ...
            ifname (str): the interface name to use.
            auto_connect (bool): True to connect automatically, or False for
                manual.
            save (bool): True to persist the connection, or False.
            ipv4_method (str): setting method.
                Available methods: auto, disabled, link-local, manual, shared.
            ipv4_addr (str): a static address.
            ipv4_gw (str): a gateway address.
            ipv6_method (str): setting method.
                Available methods: auto, dhcp, disabled, ignore, link-local,
                manual, shared.
            ipv6_addr (str): a static address.
            ipv6_gw (str): a gateway address.
            type_options (dict): type specific options. e.g: {"mtu": "1500"}.

        Returns:
            str: an nmcli command.
        """
        command = f"nmcli {object_type} {operation}"

        if operation == Operations.DELETE or operation == Operations.MODIFY:
            command += f" {name}"

        elif operation == Operations.ADD:
            command += " {common}".format(
                common=self._common_options_builder(
                    con_type=con_type,
                    con_name=name,
                    ifname=ifname,
                    auto_connect=auto_connect,
                    save=save,
                )
            )

        if type_options:
            for _property, value in type_options.items():
                command += f" {_property} {value}"

        command += self._ip_options_builder(
            ipv4_addr=ipv4_addr,
            ipv4_gw=ipv4_gw,
            ipv4_method=ipv4_method,
            ipv6_addr=ipv6_addr,
            ipv6_gw=ipv6_gw,
            ipv6_method=ipv6_method,
        )

        return command
