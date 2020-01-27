# -*- coding: utf-8 -*-
"""
Tests for the NMCLI service class.
"""
import pytest

from rrmngmnt import Host, RootUser
from rrmngmnt.errors import CommandExecutionFailure

from tests.common import FakeExecutorFactory

MOCK_ROOT_PASSWORD = "11111"

MOCK_IP = "1.1.1.1"


@pytest.fixture(scope="class")
def provision_host(request):
    """
    Provisions a mock host.
    """
    ip = getattr(request.cls, "host_ip")
    root_password = getattr(request.cls, "root_password")
    data = getattr(request.cls, "data")

    mock = Host(ip=ip)
    mock.add_user(RootUser(password=root_password))
    mock.executor_factory = FakeExecutorFactory(
        cmd_to_data=data, files_content=None
    )
    return mock


@pytest.fixture(scope="function")
def mock(provision_host):
    return provision_host


class NmcliBase(object):
    """
    Base class for tests
    """

    host_ip = MOCK_IP
    root_password = MOCK_ROOT_PASSWORD
    data = {}


class TestNmcliSanity(NmcliBase):
    """
    Testing basic scenarios for existing connections.
    """

    data = {
        "nmcli -g GENERAL.DEVICE device show": (
            0,
            "\n".join(["virbr0", "enp1s0f1", "enp2s0f0", "enp2s0f1"]),
            "",
        ),
        "nmcli -t connection show": (
            0,
            "\n".join(
                [
                    "virbr0:ba7aafc8-438e-4f8d-9f6e-3991fecebac0:bridge"
                    ":virbr0",
                    "enp1s0f1:702b48ac-750f-4856-8124-c8c55d8e3dda:"
                    "802-3-ethernet:",
                    "enp2s0f0:d2ee2c05-b28f-4529-8f42-ea4dbb17f308:"
                    "802-3-ethernet:",
                    "enp2s0f1:98e5c49f-bd72-45b4-b377-bfb74b6665ca:"
                    "802-3-ethernet:",
                    "enp2s0f2:a7199332-f99d-4152-babd-79d37d53478c:"
                    "802-3-ethernet:",
                    "enp2s0f3:86dbb462-6404-4444-8f4b-b78d045f4c9d:"
                    "802-3-ethernet:",
                ]
            ),
            "",
        ),
        "nmcli -e no -g GENERAL.TYPE,GENERAL.HWADDR,GENERAL.MTU device show "
        "virbr0": (0, "\n".join(["bridge", "52:54:00:9C:D2:15", "1500"]), ""),
        "nmcli -e no -g GENERAL.TYPE,GENERAL.HWADDR,GENERAL.MTU device show "
        "enp1s0f1": (
            0,
            "\n".join(["ethernet", "00:25:90:C6:D9:B1", "1500"]),
            "",
        ),
        "nmcli -e no -g GENERAL.TYPE,GENERAL.HWADDR,GENERAL.MTU device show "
        "enp2s0f0": (
            0,
            "\n".join(["ethernet", "00:E0:ED:33:3F:7E", "1500"]),
            "",
        ),
        "nmcli -e no -g GENERAL.TYPE,GENERAL.HWADDR,GENERAL.MTU device show "
        "enp2s0f1": (
            0,
            "\n".join(["ethernet", "00:E0:ED:33:3F:7F", "1500"]),
            "",
        ),
        "nmcli connection show ovirtmgmt": (0, "", ""),
        "nmcli connection show ovirtmgmtt": (
            10,
            "",
            "Error: ovirtmgmtt - no such connection profile.",
        ),
        "nmcli device show ovirtmgmt": (0, "", ""),
        "nmcli device show ovirtmgmtt": (
            10,
            "",
            "Error: Device 'ovirtmgmtt' not found.",
        ),
        "nmcli -g connection.uuid connection show ovirtmgmt": (
            0,
            "f142311f-9e79-4b9e-9d8a-f591e0cec44a",
            "",
        ),
        "nmcli -g connection.uuid connection show ovirtmgmtt": (
            10,
            "",
            "Error: ovirtmgmtt - no such connection profile",
        ),
        "nmcli -m multiline connection show": (
            0,
            "\n".join(
                [
                    "NAME:                                   ovirtmgmt",
                    "UUID:                                   f142311f-9e79-4b9e-9d8a-f591e0cec44a",  # noqa: E501
                    "TYPE:                                   bridge",
                    "DEVICE:                                 ovirtmgmt",
                    "NAME:                                   virbr0",
                    "UUID:                                   56d36466-2a58-4461-98ba-fbe11700955a",  # noqa: E501
                    "TYPE:                                   bridge",
                    "DEVICE:                                 virbr0",
                    "NAME:                                   enp8s0f0",
                    "UUID:                                   f58d1962-459d-47de-b090-55091dd3d702",  # noqa: E501
                    "TYPE:                                   ethernet",
                    "DEVICE:                                 enp8s0f0",
                ]
            ),
            "",
        ),
        "nmcli connection show virbr0": (0, "", ""),
        "nmcli connection show enp8s0f0": (0, "", ""),
        "nmcli -g connection.uuid connection show virbr0": (
            0,
            "56d36466-2a58-4461-98ba-fbe11700955a",
            "",
        ),
        "nmcli -g connection.uuid connection show enp8s0f0": (
            0,
            "f58d1962-459d-47de-b090-55091dd3d702",
            "",
        ),
        "nmcli -g GENERAL.TYPE device show enp8s0f0": (0, "ethernet", ""),
        "nmcli -g GENERAL.TYPE device show enp8s0f00": (
            10,
            "",
            "Error: Device 'enp8s0f00' not found.",
        ),
        "nmcli connection up ovirtmgmt": (
            0,
            "Connection successfully activated (D-Bus active path: "
            "/org/freedesktop/NetworkManager/ActiveConnection/1985)",
            "",
        ),
        "nmcli connection down ovirtmgmt": (
            0,
            "Connection successfully terminated (D-Bus active path: "
            "/org/freedesktop/NetworkManager/ActiveConnection/1985)",
            "",
        ),
        "nmcli connection up ovirtmgmtt": (
            10,
            "",
            "Error: unknown connection 'ovirtmgmtt'.",
        ),
        "nmcli connection down ovirtmgmtt": (
            10,
            "",
            "Error: unknown connection 'ovirtmgmtt'.",
        ),
        "nmcli connection delete ovirtmgmt": (
            0,
            "Connection successfully removed (D-Bus active path: "
            "/org/freedesktop/NetworkManager/ActiveConnection/1985)",
            "",
        ),
        "nmcli connection delete ovirtmgmtt": (
            10,
            "",
            "Error: unknown connection 'ovirtmgmtt'.",
        ),
        "nmcli connection modify ovirtmgmt autoconnect yes": (0, "", ""),
        "nmcli connection modify ovirtmgmt autoconnectt yes": (10, "", ""),
        "nmcli connection modify ovirtmgmtt autoconnect yes": (
            10,
            "",
            "Error: unknown connection 'ovirtmgmtt'.",
        ),
        "nmcli device modify em1 +ipv4.dns 8.8.4.4": (0, "", ""),
        'nmcli device modify em1 -ipv6.addr abbe::cafe/56': (0, "", "")
    }

    def test_modify_device_add_ipv4_dns(self, mock):
        mock.network.nmcli.modify_device(
            device="em1",
            properties={
                "+ipv4.dns": "8.8.4.4"
            }
        )

    def test_modify_device_remove_ipv6_address(self, mock):
        mock.network.nmcli.modify_device(
            device="em1",
            properties={
                "-ipv6.addr": "abbe::cafe/56"
            }
        )

    def test_get_all_connections(self, mock):
        connections = mock.network.nmcli.get_all_connections()
        assert connections == [
            {
                "device": "virbr0",
                "name": "virbr0",
                "type": "bridge",
                "uuid": "ba7aafc8-438e-4f8d-9f6e-3991fecebac0",
            },
            {
                "device": "",
                "name": "enp1s0f1",
                "type": "802-3-ethernet",
                "uuid": "702b48ac-750f-4856-8124-c8c55d8e3dda",
            },
            {
                "device": "",
                "name": "enp2s0f0",
                "type": "802-3-ethernet",
                "uuid": "d2ee2c05-b28f-4529-8f42-ea4dbb17f308",
            },
            {
                "device": "",
                "name": "enp2s0f1",
                "type": "802-3-ethernet",
                "uuid": "98e5c49f-bd72-45b4-b377-bfb74b6665ca",
            },
            {
                "device": "",
                "name": "enp2s0f2",
                "type": "802-3-ethernet",
                "uuid": "a7199332-f99d-4152-babd-79d37d53478c",
            },
            {
                "device": "",
                "name": "enp2s0f3",
                "type": "802-3-ethernet",
                "uuid": "86dbb462-6404-4444-8f4b-b78d045f4c9d",
            },
        ]

    def test_get_all_devices(self, mock):
        devices = mock.network.nmcli.get_all_devices()
        assert devices == [
            {
                "name": "virbr0",
                "type": "bridge",
                "mac": "52:54:00:9C:D2:15",
                "mtu": "1500",
            },
            {
                "name": "enp1s0f1",
                "type": "ethernet",
                "mac": "00:25:90:C6:D9:B1",
                "mtu": "1500",
            },
            {
                "name": "enp2s0f0",
                "type": "ethernet",
                "mac": "00:E0:ED:33:3F:7E",
                "mtu": "1500",
            },
            {
                "name": "enp2s0f1",
                "type": "ethernet",
                "mac": "00:E0:ED:33:3F:7F",
                "mtu": "1500",
            },
        ]

    def test_set_connection_up(self, mock):
        mock.network.nmcli.set_connection_state(
            connection="ovirtmgmt", state="up"
        )

    def test_set_connection_down(self, mock):
        mock.network.nmcli.set_connection_state(
            connection="ovirtmgmt", state="down"
        )

    def test_set_non_existing_connection_up(self, mock):
        with pytest.raises(
            expected_exception=CommandExecutionFailure,
            match=".*Error: unknown connection 'ovirtmgmtt'..*",
        ):
            mock.network.nmcli.set_connection_state(
                connection="ovirtmgmtt", state="up"
            )

    def test_set_non_existing_connection_down(self, mock):
        with pytest.raises(
            expected_exception=CommandExecutionFailure,
            match=".*Error: unknown connection 'ovirtmgmtt'..*",
        ):
            mock.network.nmcli.set_connection_state(
                connection="ovirtmgmtt", state="down"
            )

    def test_modify_connection_autoconnect(self, mock):
        mock.network.nmcli.modify_connection(
            connection="ovirtmgmt", properties={"autoconnect": "yes"}
        )

    def test_modify_connection_with_illegal_property(self, mock):
        with pytest.raises(expected_exception=CommandExecutionFailure):
            mock.network.nmcli.modify_connection(
                connection="ovirtmgmt", properties={"autoconnectt": "yes"}
            )

    def test_modify_non_existing_connection(self, mock):
        with pytest.raises(
            expected_exception=CommandExecutionFailure,
            match=".*Error: unknown connection 'ovirtmgmtt'..*",
        ):
            mock.network.nmcli.modify_connection(
                connection="ovirtmgmtt", properties={"autoconnect": "yes"}
            )

    def test_delete_connection(self, mock):
        mock.network.nmcli.delete_connection(connection="ovirtmgmt")

    def test_delete_non_existing_connection(self, mock):
        with pytest.raises(
            expected_exception=CommandExecutionFailure,
            match=".*Error: unknown connection 'ovirtmgmtt'..*",
        ):
            mock.network.nmcli.delete_connection(connection="ovirtmgmtt")


class NmcliConnectionTypeBase(NmcliBase):
    """
    Base class for testing different connection types.
    """

    def test_add_connection_defaults(self, mock):
        pass

    def test_add_connection_with_autoconnect(self, mock):
        pass

    def test_add_connection_with_save(self, mock):
        pass


class NmcliConnectionTypeIPConfigurable(NmcliConnectionTypeBase):
    """
    Base class for testing connection types where IPv4/6 can be configured.
    """

    def test_add_connection_with_static_ips(self, mock):
        pass

    def test_add_connection_with_invalid_ipv4_address(self, mock):
        pass

    def test_add_connection_with_invalid_ipv6_address(self, mock):
        pass

    def test_add_connection_with_invalid_ipv4_gateway(self, mock):
        pass

    def test_add_connection_with_invalid_ipv6_gateway(self, mock):
        pass


class TestNmcliEthernetConnection(NmcliConnectionTypeIPConfigurable):
    """
    Testing scenarios for ethernet type connections.
    """

    data = {
        (
            "nmcli connection add type ethernet con-name ethernet_con ifname "
            "enp8s0f0"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type ethernet con-name ethernet_con ifname enp8s0f0 autoconnect "
            "yes"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type ethernet con-name ethernet_con ifname enp8s0f0 autoconnect "
            "yes save yes"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type ethernet con-name ethernet_con ifname enp8s0f0 autoconnect "
            "no save no"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type ethernet con-name ethernet_con ifname enp8s0f0 save yes"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type ethernet con-name ethernet_con ifname enp8s0f0 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2 "
            "ipv4.gateway 192.168.23.254 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573:5984 "
            "ipv6.gateway 2a02:ed0:52fe:ec00::"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type ethernet con-name ethernet_con ifname enp8s0f0 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2.2 "
            "ipv4.gateway 192.168.23.254 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573:5984 "
            "ipv6.gateway 2a02:ed0:52fe:ec00::"
        ): (
            10,
            "",
            "Error: failed to modify ipv4.addresses: invalid IP address: "
            "Invalid IPv4 address '192.186.23.2.2'.",
        ),
        (
            "nmcli connection add "
            "type ethernet con-name ethernet_con ifname enp8s0f0 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2 "
            "ipv4.gateway 192.168.23.254 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573 "
            "ipv6.gateway 2a02:ed0:52fe:ec00::"
        ): (
            10,
            "",
            "Error: failed to modify ipv6.addresses: invalid IP address: "
            "Invalid IPv6 address '2a02:ed0:52fe:ec00:dc3f:f939:a573'.",
        ),
        (
            "nmcli connection add "
            "type ethernet con-name ethernet_con ifname enp8s0f0 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2 "
            "ipv4.gateway 192.168.23.254.2 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573:5984 "
            "ipv6.gateway 2a02:ed0:52fe:ec00::"
        ): (
            10,
            "",
            "Error: failed to modify ipv4.gateway: invalid IP address: "
            "Invalid IPv4 address '192.168.23.254.2'.",
        ),
        (
            "nmcli connection add "
            "type ethernet con-name ethernet_con ifname enp8s0f0 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2 "
            "ipv4.gateway 192.168.23.254 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573:5984 "
            "ipv6.gateway 2a02:ed0:52fe:ec00:"
        ): (
            10,
            "",
            "Error: failed to modify ipv6.gateway: invalid IP address: "
            "Invalid IPv6 address '2a02:ed0:52fe:ec00:'.",
        ),
        (
            "nmcli connection add "
            "type ethernet con-name ethernet_con ifname enp8s0f0 "
            "mac e8:6a:64:7d:d3:b1"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type ethernet con-name ethernet_con ifname enp8s0f0 "
            "mac e8:6a:64:7d:d3"
        ): (
            10,
            "",
            "Error: failed to modify 802-3-ethernet.mac-address: "
            "'e8:6a:64:7d:d3' is not a valid Ethernet MAC.",
        ),
        (
            "nmcli connection add "
            "type ethernet con-name ethernet_con ifname enp8s0f0 "
            "mtu 1600"
        ): (0, "", ""),
    }

    def test_add_connection_defaults(self, mock):
        mock.network.nmcli.add_ethernet_connection(
            name="ethernet_con", ifname="enp8s0f0"
        )

    def test_add_connection_with_autoconnect(self, mock):
        mock.network.nmcli.add_ethernet_connection(
            name="ethernet_con", ifname="enp8s0f0", auto_connect=True
        )

    def test_add_connection_with_save(self, mock):
        mock.network.nmcli.add_ethernet_connection(
            name="ethernet_con", ifname="enp8s0f0", save=True
        )

    def test_add_connection_with_autoconnect_and_save(self, mock):
        mock.network.nmcli.add_ethernet_connection(
            name="ethernet_con",
            ifname="enp8s0f0",
            auto_connect=True,
            save=True,
        )

    def test_add_connection_with_no_autoconnect_and_no_save(self, mock):
        mock.network.nmcli.add_ethernet_connection(
            name="ethernet_con",
            ifname="enp8s0f0",
            auto_connect=False,
            save=False,
        )

    def test_add_connection_with_static_ips(self, mock):
        mock.network.nmcli.add_ethernet_connection(
            name="ethernet_con",
            ifname="enp8s0f0",
            ipv4_method="manual",
            ipv4_addr="192.168.23.2",
            ipv4_gw="192.168.23.254",
            ipv6_method="manual",
            ipv6_addr="2a02:ed0:52fe:ec00:dc3f:f939:a573:5984",
            ipv6_gw="2a02:ed0:52fe:ec00::",
        )

    def test_add_connection_with_invalid_ipv4_address(self, mock):
        with pytest.raises(
            expected_exception=CommandExecutionFailure,
            match=".*Error: failed to modify ipv4.addresses: "
            "invalid IP address: "
            "Invalid IPv4 address '192.186.23.2.2'..*",
        ):
            mock.network.nmcli.add_ethernet_connection(
                name="ethernet_con",
                ifname="enp8s0f0",
                ipv4_method="manual",
                ipv4_addr="192.168.23.2.2",
                ipv4_gw="192.168.23.254",
                ipv6_method="manual",
                ipv6_addr="2a02:ed0:52fe:ec00:dc3f:f939:a573:5984",
                ipv6_gw="2a02:ed0:52fe:ec00::",
            )

    def test_add_connection_with_invalid_ipv6_address(self, mock):
        with pytest.raises(
            expected_exception=CommandExecutionFailure,
            match=".*Error: failed to modify ipv6.addresses: "
            "invalid IP address: "
            "Invalid IPv6 address "
            "'2a02:ed0:52fe:ec00:dc3f:f939:a573'..*",
        ):
            mock.network.nmcli.add_ethernet_connection(
                name="ethernet_con",
                ifname="enp8s0f0",
                ipv4_method="manual",
                ipv4_addr="192.168.23.2",
                ipv4_gw="192.168.23.254",
                ipv6_method="manual",
                ipv6_addr="2a02:ed0:52fe:ec00:dc3f:f939:a573",
                ipv6_gw="2a02:ed0:52fe:ec00::",
            )

    def test_add_connection_with_invalid_ipv4_gateway(self, mock):
        with pytest.raises(
            expected_exception=CommandExecutionFailure,
            match=".*Error: failed to modify ipv4.gateway: "
            "invalid IP address: "
            "Invalid IPv4 address '192.168.23.254.2'.*",
        ):
            mock.network.nmcli.add_ethernet_connection(
                name="ethernet_con",
                ifname="enp8s0f0",
                ipv4_method="manual",
                ipv4_addr="192.168.23.2",
                ipv4_gw="192.168.23.254.2",
                ipv6_method="manual",
                ipv6_addr="2a02:ed0:52fe:ec00:dc3f:f939:a573:5984",
                ipv6_gw="2a02:ed0:52fe:ec00::",
            )

    def test_add_connection_with_invalid_ipv6_gateway(self, mock):
        with pytest.raises(
            expected_exception=CommandExecutionFailure,
            match=".*Error: failed to modify ipv6.gateway: "
            "invalid IP address: "
            "Invalid IPv6 address '2a02:ed0:52fe:ec00:'..*",
        ):
            mock.network.nmcli.add_ethernet_connection(
                name="ethernet_con",
                ifname="enp8s0f0",
                ipv4_method="manual",
                ipv4_addr="192.168.23.2",
                ipv4_gw="192.168.23.254",
                ipv6_method="manual",
                ipv6_addr="2a02:ed0:52fe:ec00:dc3f:f939:a573:5984",
                ipv6_gw="2a02:ed0:52fe:ec00:",
            )

    def test_add_ethernet_with_mac(self, mock):
        mock.network.nmcli.add_ethernet_connection(
            name="ethernet_con", ifname="enp8s0f0", mac="e8:6a:64:7d:d3:b1"
        )

    def test_add_ethernet_with_invalid_mac(self, mock):
        with pytest.raises(
            expected_exception=CommandExecutionFailure,
            match=".*Error: failed to modify 802-3-ethernet.mac-address: "
            "'e8:6a:64:7d:d3' is not a valid Ethernet MAC..*",
        ):
            mock.network.nmcli.add_ethernet_connection(
                name="ethernet_con", ifname="enp8s0f0", mac="e8:6a:64:7d:d3"
            )

    def test_add_ethernet_with_mtu(self, mock):
        mock.network.nmcli.add_ethernet_connection(
            name="ethernet_con", ifname="enp8s0f0", mtu=1600
        )


class TestNmcliBondConnection(NmcliConnectionTypeIPConfigurable):
    """
    Testing scenarios for bond type connections.
    """

    data = {
        "nmcli connection add "
        "type bond con-name bond_con ifname bond0": (0, "", ""),
        (
            "nmcli connection add "
            "type bond con-name bond_con ifname bond0 "
            "autoconnect yes"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type bond con-name bond_con ifname bond0 "
            "save yes"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type bond con-name bond_con ifname bond0 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2 ipv4.gateway 192.168.23.254 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573:5984 "
            "ipv6.gateway 2a02:ed0:52fe:ec00::"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type bond con-name bond_con ifname bond0 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2.2 ipv4.gateway 192.168.23.254 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573:5984 "
            "ipv6.gateway 2a02:ed0:52fe:ec00::"
        ): (10, "", ""),
        (
            "nmcli connection add "
            "type bond con-name bond_con ifname bond0 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2 ipv4.gateway 192.168.23.254.2 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573:5984 "
            "ipv6.gateway 2a02:ed0:52fe:ec00::"
        ): (10, "", ""),
        (
            "nmcli connection add "
            "type bond con-name bond_con ifname bond0 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2 ipv4.gateway 192.168.23.254 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573 "
            "ipv6.gateway 2a02:ed0:52fe:ec00::"
        ): (10, "", ""),
        (
            "nmcli connection add "
            "type bond con-name bond_con ifname bond0 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2 ipv4.gateway 192.168.23.254 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573:5984 "
            "ipv6.gateway 2a02:ed0:52fe:ec00:"
        ): (10, "", ""),
        (
            "nmcli connection add "
            "type bond con-name bond_con ifname bond0 "
            "mode balance-rr"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type bond con-name bond_con ifname bond0 "
            "mode active-backup"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type bond con-name bond_con ifname bond0 "
            "mode balance-xor"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type bond con-name bond_con ifname bond0 "
            "mode broadcast"
        ): (0, "", ""),
        "nmcli connection add "
        "type bond con-name bond_con ifname bond0 "
        "mode 802.3ad": (0, "", ""),
        (
            "nmcli connection add "
            "type bond con-name bond_con ifname bond0 "
            "mode balance-tlb"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type bond con-name bond_con ifname bond0 "
            "mode balance-alb"
        ): (0, "", ""),
        "nmcli connection add "
        "type bond con-name bond_con ifname bond0 "
        "miimon 50": (0, "", ""),
    }

    def test_add_connection_defaults(self, mock):
        mock.network.nmcli.add_bond(con_name="bond_con", ifname="bond0")

    def test_add_connection_with_autoconnect(self, mock):
        mock.network.nmcli.add_bond(
            con_name="bond_con", ifname="bond0", auto_connect=True
        )

    def test_add_connection_with_save(self, mock):
        mock.network.nmcli.add_bond(
            con_name="bond_con", ifname="bond0", save=True
        )

    def test_add_connection_with_static_ips(self, mock):
        mock.network.nmcli.add_bond(
            con_name="bond_con",
            ifname="bond0",
            ipv4_method="manual",
            ipv4_addr="192.168.23.2",
            ipv4_gw="192.168.23.254",
            ipv6_method="manual",
            ipv6_addr="2a02:ed0:52fe:ec00:dc3f:f939:a573:5984",
            ipv6_gw="2a02:ed0:52fe:ec00::",
        )

    @pytest.mark.parametrize(
        "bond_mode",
        [
            "balance-rr",
            "active-backup",
            "balance-xor",
            "broadcast",
            "802.3ad",
            "balance-tlb",
            "balance-alb",
        ],
    )
    def test_add_bond_with_mode(self, mock, bond_mode):
        mock.network.nmcli.add_bond(
            con_name="bond_con", ifname="bond0", mode=bond_mode
        )

    def test_add_bond_with_miimon(self, mock):
        mock.network.nmcli.add_bond(
            con_name="bond_con", ifname="bond0", miimon=50
        )

    def test_add_connection_with_invalid_ipv4_address(self, mock):
        with pytest.raises(expected_exception=CommandExecutionFailure):
            mock.network.nmcli.add_bond(
                con_name="bond_con",
                ifname="bond0",
                ipv4_method="manual",
                ipv4_addr="192.168.23.2.2",
                ipv4_gw="192.168.23.254",
                ipv6_method="manual",
                ipv6_addr="2a02:ed0:52fe:ec00:dc3f:f939:a573:5984",
                ipv6_gw="2a02:ed0:52fe:ec00::",
            )

    def test_add_connection_with_invalid_ipv6_address(self, mock):
        with pytest.raises(expected_exception=CommandExecutionFailure):
            mock.network.nmcli.add_bond(
                con_name="bond_con",
                ifname="bond0",
                ipv4_method="manual",
                ipv4_addr="192.168.23.2",
                ipv4_gw="192.168.23.254",
                ipv6_method="manual",
                ipv6_addr="2a02:ed0:52fe:ec00:dc3f:f939:a573",
                ipv6_gw="2a02:ed0:52fe:ec00::",
            )

    def test_add_connection_with_invalid_ipv4_gateway(self, mock):
        with pytest.raises(expected_exception=CommandExecutionFailure):
            mock.network.nmcli.add_bond(
                con_name="bond_con",
                ifname="bond0",
                ipv4_method="manual",
                ipv4_addr="192.168.23.2",
                ipv4_gw="192.168.23.254.2",
                ipv6_method="manual",
                ipv6_addr="2a02:ed0:52fe:ec00:dc3f:f939:a573:5984",
                ipv6_gw="2a02:ed0:52fe:ec00::",
            )

    def test_add_connection_with_invalid_ipv6_gateway(self, mock):
        with pytest.raises(expected_exception=CommandExecutionFailure):
            mock.network.nmcli.add_bond(
                con_name="bond_con",
                ifname="bond0",
                ipv4_method="manual",
                ipv4_addr="192.168.23.2",
                ipv4_gw="192.168.23.254",
                ipv6_method="manual",
                ipv6_addr="2a02:ed0:52fe:ec00:dc3f:f939:a573:5984",
                ipv6_gw="2a02:ed0:52fe:ec00:",
            )


class TestNmcliSlaveConnection(NmcliConnectionTypeBase):
    """
    Testing scenarios for bond type connections.
    """

    data = {
        (
            "nmcli connection add "
            "type ethernet con-name bond0_slave ifname enp8s0f0 master bond0"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type ethernet con-name bond0_slave ifname enp8s0f0 "
            "autoconnect yes master bond0"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type ethernet con-name bond0_slave ifname enp8s0f0 "
            "save yes master bond0"
        ): (0, "", ""),
        "nmcli -g GENERAL.TYPE device show enp8s0f0": (0, "ethernet", ""),
    }

    def test_add_connection_defaults(self, mock):
        mock.network.nmcli.add_slave(
            con_name="bond0_slave",
            slave_type="ethernet",
            ifname="enp8s0f0",
            master="bond0",
        )

    def test_add_connection_with_autoconnect(self, mock):
        mock.network.nmcli.add_slave(
            con_name="bond0_slave",
            slave_type="ethernet",
            ifname="enp8s0f0",
            master="bond0",
            auto_connect=True,
        )

    def test_add_connection_with_save(self, mock):
        mock.network.nmcli.add_slave(
            con_name="bond0_slave",
            slave_type="ethernet",
            ifname="enp8s0f0",
            master="bond0",
            save=True,
        )


class TestNmcliVlanConnection(NmcliConnectionTypeIPConfigurable):
    """
    Testing scenarios for VLAN type connections.
    """

    data = {
        (
            "nmcli connection add "
            "type vlan con-name vlan_con id 163 dev enp8s0f0"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type vlan con-name vlan_con dev enp8s0f0 id 163"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type vlan con-name vlan_con "
            "autoconnect yes id 163 dev enp8s0f0"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type vlan con-name vlan_con "
            "autoconnect yes dev enp8s0f0 id 163"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type vlan con-name vlan_con "
            "save yes id 163 dev enp8s0f0"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type vlan con-name vlan_con "
            "save yes dev enp8s0f0 id 163"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type vlan con-name vlan_con "
            "id 163 dev enp8s0f0 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2 ipv4.gateway 192.168.23.254 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573:5984 "
            "ipv6.gateway 2a02:ed0:52fe:ec00::"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type vlan con-name vlan_con "
            "dev enp8s0f0 id 163 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2 ipv4.gateway 192.168.23.254 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573:5984 "
            "ipv6.gateway 2a02:ed0:52fe:ec00::"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type vlan con-name vlan_con "
            "id 163 dev enp8s0f0 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2.2 ipv4.gateway 192.168.23.254 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573:5984 "
            "ipv6.gateway 2a02:ed0:52fe:ec00::"
        ): (10, "", ""),
        (
            "nmcli connection add "
            "type vlan con-name vlan_con "
            "dev enp8s0f0 id 163 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2.2 ipv4.gateway 192.168.23.254 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573:5984 "
            "ipv6.gateway 2a02:ed0:52fe:ec00::"
        ): (10, "", ""),
        (
            "nmcli connection add "
            "type vlan con-name vlan_con "
            "id 163 dev enp8s0f0 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2 "
            "ipv4.gateway 192.168.23.254.2 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573:5984 "
            "ipv6.gateway 2a02:ed0:52fe:ec00::"
        ): (10, "", ""),
        (
            "nmcli connection add "
            "type vlan con-name vlan_con "
            "dev enp8s0f0 id 163 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2 "
            "ipv4.gateway 192.168.23.254.2 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573:5984 "
            "ipv6.gateway 2a02:ed0:52fe:ec00::"
        ): (10, "", ""),
        (
            "nmcli connection add "
            "type vlan con-name vlan_con "
            "id 163 dev enp8s0f0 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2 "
            "ipv4.gateway 192.168.23.254 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573 "
            "ipv6.gateway 2a02:ed0:52fe:ec00::"
        ): (10, "", ""),
        (
            "nmcli connection add "
            "type vlan con-name vlan_con "
            "dev enp8s0f0 id 163 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2 "
            "ipv4.gateway 192.168.23.254 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573 "
            "ipv6.gateway 2a02:ed0:52fe:ec00::"
        ): (10, "", ""),
        (
            "nmcli connection add "
            "type vlan con-name vlan_con "
            "id 163 dev enp8s0f0 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2 "
            "ipv4.gateway 192.168.23.254 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573:5984 "
            "ipv6.gateway 2a02:ed0:52fe:ec00:"
        ): (10, "", ""),
        (
            "nmcli connection add "
            "type vlan con-name vlan_con "
            "dev enp8s0f0 id 163 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2 "
            "ipv4.gateway 192.168.23.254 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573:5984 "
            "ipv6.gateway 2a02:ed0:52fe:ec00:"
        ): (10, "", ""),
        (
            "nmcli connection add "
            "type vlan con-name vlan_con "
            "id 163 dev enp8s0f0 mtu 1600"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type vlan con-name vlan_con "
            "mtu 1600 id 163 dev enp8s0f0"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type vlan con-name vlan_con "
            "dev enp8s0f0 id 163 mtu 1600"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type vlan con-name vlan_con "
            "dev enp8s0f0 mtu 1600 id 163"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type vlan con-name vlan_con "
            "mtu 1600 dev enp8s0f0 id 163"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type vlan con-name vlan_con "
            "id 163 mtu 1600 dev enp8s0f0"
        ): (0, "", ""),
        "nmcli device show enp8s0f0": (0, "ethernet", ""),
        "nmcli device show enp8s0f00": (
            10,
            "",
            "Error: Device 'enp8s0f00' not found.",
        ),
        "nmcli connection add type vlan con-name vlan_con "
        "id 163 dev enp8s0f00": (10, "", ""),
        "nmcli connection add type vlan con-name vlan_con "
        "dev enp8s0f00 id 163": (10, "", ""),
    }

    def test_add_connection_defaults(self, mock):
        mock.network.nmcli.add_vlan(
            con_name="vlan_con", dev="enp8s0f0", vlan_id=163
        )

    def test_add_connection_with_autoconnect(self, mock):
        mock.network.nmcli.add_vlan(
            con_name="vlan_con", dev="enp8s0f0", vlan_id=163, auto_connect=True
        )

    def test_add_connection_with_save(self, mock):
        mock.network.nmcli.add_vlan(
            con_name="vlan_con", dev="enp8s0f0", vlan_id=163, save=True
        )

    def test_add_connection_with_static_ips(self, mock):
        mock.network.nmcli.add_vlan(
            con_name="vlan_con",
            dev="enp8s0f0",
            vlan_id=163,
            ipv4_method="manual",
            ipv4_addr="192.168.23.2",
            ipv4_gw="192.168.23.254",
            ipv6_method="manual",
            ipv6_addr="2a02:ed0:52fe:ec00:dc3f:f939:a573:5984",
            ipv6_gw="2a02:ed0:52fe:ec00::",
        )

    def test_add_vlan_with_invalid_dev(self, mock):
        with pytest.raises(expected_exception=CommandExecutionFailure):
            mock.network.nmcli.add_vlan(
                con_name="vlan_con", dev="enp8s0f00", vlan_id=163
            )

    def test_add_vlan_with_mtu(self, mock):
        mock.network.nmcli.add_vlan(
            con_name="vlan_con", dev="enp8s0f0", vlan_id=163, mtu=1600
        )

    def test_add_connection_with_invalid_ipv4_address(self, mock):
        with pytest.raises(expected_exception=CommandExecutionFailure):
            mock.network.nmcli.add_vlan(
                con_name="vlan_con",
                dev="enp8s0f0",
                vlan_id=163,
                ipv4_method="manual",
                ipv4_addr="192.168.23.2.2",
                ipv4_gw="192.168.23.254",
                ipv6_method="manual",
                ipv6_addr="2a02:ed0:52fe:ec00:dc3f:f939:a573:5984",
                ipv6_gw="2a02:ed0:52fe:ec00::",
            )

    def test_add_connection_with_invalid_ipv6_address(self, mock):
        with pytest.raises(expected_exception=CommandExecutionFailure):
            mock.network.nmcli.add_vlan(
                con_name="vlan_con",
                dev="enp8s0f0",
                vlan_id=163,
                ipv4_method="manual",
                ipv4_addr="192.168.23.2",
                ipv4_gw="192.168.23.254",
                ipv6_method="manual",
                ipv6_addr="2a02:ed0:52fe:ec00:dc3f:f939:a573",
                ipv6_gw="2a02:ed0:52fe:ec00::",
            )

    def test_add_connection_with_invalid_ipv4_gateway(self, mock):
        with pytest.raises(expected_exception=CommandExecutionFailure):
            mock.network.nmcli.add_vlan(
                con_name="vlan_con",
                dev="enp8s0f0",
                vlan_id=163,
                ipv4_method="manual",
                ipv4_addr="192.168.23.2",
                ipv4_gw="192.168.23.254.2",
                ipv6_method="manual",
                ipv6_addr="2a02:ed0:52fe:ec00:dc3f:f939:a573:5984",
                ipv6_gw="2a02:ed0:52fe:ec00::",
            )

    def test_add_connection_with_invalid_ipv6_gateway(self, mock):
        with pytest.raises(expected_exception=CommandExecutionFailure):
            mock.network.nmcli.add_vlan(
                con_name="vlan_con",
                dev="enp8s0f0",
                vlan_id=163,
                ipv4_method="manual",
                ipv4_addr="192.168.23.2",
                ipv4_gw="192.168.23.254",
                ipv6_method="manual",
                ipv6_addr="2a02:ed0:52fe:ec00:dc3f:f939:a573:5984",
                ipv6_gw="2a02:ed0:52fe:ec00:",
            )


class TestNmcliDummyConnection(NmcliConnectionTypeIPConfigurable):
    """
    Testing scenarios for dummy type connections.
    """

    data = {
        "nmcli connection add "
        "type dummy con-name dummy_con ifname dummy_0": (0, "", ""),
        (
            "nmcli connection add "
            "type dummy con-name dummy_con ifname dummy_0 "
            "autoconnect yes"
        ): (0, "", ""),
        "nmcli connection add "
        "type dummy con-name dummy_con ifname dummy_0 "
        "save yes": (0, "", ""),
        (
            "nmcli connection add "
            "type dummy con-name dummy_con ifname dummy_0 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2 "
            "ipv4.gateway 192.168.23.254 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573:5984 "
            "ipv6.gateway 2a02:ed0:52fe:ec00::"
        ): (0, "", ""),
        (
            "nmcli connection add "
            "type dummy con-name dummy_con ifname dummy_0 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2.2 "
            "ipv4.gateway 192.168.23.254 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573:5984 "
            "ipv6.gateway 2a02:ed0:52fe:ec00::"
        ): (10, "", ""),
        (
            "nmcli connection add "
            "type dummy con-name dummy_con ifname dummy_0 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2 "
            "ipv4.gateway 192.168.23.254.2 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573:5984 "
            "ipv6.gateway 2a02:ed0:52fe:ec00::"
        ): (10, "", ""),
        (
            "nmcli connection add "
            "type dummy con-name dummy_con ifname dummy_0 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2 "
            "ipv4.gateway 192.168.23.254 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573 "
            "ipv6.gateway 2a02:ed0:52fe:ec00::"
        ): (10, "", ""),
        (
            "nmcli connection add "
            "type dummy con-name dummy_con ifname dummy_0 "
            "ipv4.method manual ipv6.method manual "
            "ipv4.addresses 192.168.23.2 "
            "ipv4.gateway 192.168.23.254 "
            "ipv6.addresses 2a02:ed0:52fe:ec00:dc3f:f939:a573:5984 "
            "ipv6.gateway 2a02:ed0:52fe:ec00:"
        ): (10, "", ""),
    }

    def test_add_connection_defaults(self, mock):
        mock.network.nmcli.add_dummy(con_name="dummy_con", ifname="dummy_0")

    def test_add_connection_with_autoconnect(self, mock):
        mock.network.nmcli.add_dummy(
            con_name="dummy_con", ifname="dummy_0", auto_connect=True
        )

    def test_add_connection_with_save(self, mock):
        mock.network.nmcli.add_dummy(
            con_name="dummy_con", ifname="dummy_0", save=True
        )

    def test_add_connection_with_static_ips(self, mock):
        mock.network.nmcli.add_dummy(
            con_name="dummy_con",
            ifname="dummy_0",
            ipv4_method="manual",
            ipv4_addr="192.168.23.2",
            ipv4_gw="192.168.23.254",
            ipv6_method="manual",
            ipv6_addr="2a02:ed0:52fe:ec00:dc3f:f939:a573:5984",
            ipv6_gw="2a02:ed0:52fe:ec00::",
        )

    def test_add_connection_with_invalid_ipv4_address(self, mock):
        with pytest.raises(expected_exception=CommandExecutionFailure):
            mock.network.nmcli.add_dummy(
                con_name="dummy_con",
                ifname="dummy_0",
                ipv4_method="manual",
                ipv4_addr="192.168.23.2.2",
                ipv4_gw="192.168.23.254",
                ipv6_method="manual",
                ipv6_addr="2a02:ed0:52fe:ec00:dc3f:f939:a573:5984",
                ipv6_gw="2a02:ed0:52fe:ec00::",
            )

    def test_add_connection_with_invalid_ipv6_address(self, mock):
        with pytest.raises(expected_exception=CommandExecutionFailure):
            mock.network.nmcli.add_dummy(
                con_name="dummy_con",
                ifname="dummy_0",
                ipv4_method="manual",
                ipv4_addr="192.168.23.2",
                ipv4_gw="192.168.23.254",
                ipv6_method="manual",
                ipv6_addr="2a02:ed0:52fe:ec00:dc3f:f939:a573",
                ipv6_gw="2a02:ed0:52fe:ec00::",
            )

    def test_add_connection_with_invalid_ipv4_gateway(self, mock):
        with pytest.raises(expected_exception=CommandExecutionFailure):
            mock.network.nmcli.add_dummy(
                con_name="dummy_con",
                ifname="dummy_0",
                ipv4_method="manual",
                ipv4_addr="192.168.23.2",
                ipv4_gw="192.168.23.254.2",
                ipv6_method="manual",
                ipv6_addr="2a02:ed0:52fe:ec00:dc3f:f939:a573:5984",
                ipv6_gw="2a02:ed0:52fe:ec00::",
            )

    def test_add_connection_with_invalid_ipv6_gateway(self, mock):
        with pytest.raises(expected_exception=CommandExecutionFailure):
            mock.network.nmcli.add_dummy(
                con_name="dummy_con",
                ifname="dummy_0",
                ipv4_method="manual",
                ipv4_addr="192.168.23.2",
                ipv4_gw="192.168.23.254",
                ipv6_method="manual",
                ipv6_addr="2a02:ed0:52fe:ec00:dc3f:f939:a573:5984",
                ipv6_gw="2a02:ed0:52fe:ec00:",
            )
