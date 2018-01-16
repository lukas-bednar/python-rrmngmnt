from rrmngmnt.service import Service

IPTABLES = 'iptables'


class Firewall(Service):
    """
    Class for firewall services
    """
    def __init__(self, host):
        """
        Args:
            host (host): Host object to run commands on
        """
        super(Firewall, self).__init__(host)
        self.host = host

    def is_active(self, firewall_service):
        """
        Check if the relevant firewall service is active on the host

        Args:
            firewall_service (str): Service name

        Returns:
            bool: True if the service is active on host, False if not

        """
        return self.host.service(firewall_service).status()

    def chain(self, chain_name):
        """
        Return Chain class to run commands on specefic firewall chain
        Args:
            chain_name (str): Name of chain to make changes

        Returns:
            chain: Chain class object

        """
        return Chain(self.host, chain_name)


class Chain(Service):
    """
    Class for Firewall specific chain commands
    """
    def __init__(self, host, chain_name):
        """
        Args:
            host (host): Host object to run commands on
            chain_name (str): Name of the firewall chain
        """
        super(Chain, self).__init__(host)
        self.host = host
        self.firewall_service = IPTABLES
        self.chain_name = chain_name.upper()
        if self.chain_name == 'OUTPUT':
            self.address_type = '--destination'
        elif self.chain_name == 'INPUT':
            self.address_type = '--source'
        else:
            raise NotImplementedError("only INPUT/OUTPUT chains are supported")

    def edit_chain(
        self, action, chain_name, address_type, dest, target, protocol='all',
        ports=None, rule_num=None
    ):
        """
        Changes firewall configuration

        Args:
           action (str): action to perform
           chain_name (str): affected chain name
           address_type (str): '--destination' for outgoing rules,
               '--source' for incoming
           dest (dict): 'address' key and value containing destination host or
               list of destination hosts
           target (str): target rule to apply
           protocol (str): affected network protocol, Default is 'all'
           ports (list): list of ports to configure
           rule_num (str): the number given after the chain name indicates the
           position where the rule will be inserted

       Returns:
           bool: True if configuration change succeeded, False otherwise

       Raises:
           NotImplementedError: In case the users specifies more than 15 ports
                to block

       Example:
           edit_chain(
                action='--append',chain='OUTPUT',
                rule_num='1',
                address_type='--destination',
                dest={'address': nfs_server},
                target='DROP'
            )
        """
        cmd = [
            self.firewall_service, action, chain_name
        ]

        if rule_num:
            cmd.extend([rule_num])

        dest = ",".join(dest['address'])
        cmd.extend(
            [
                address_type, dest, '--jump', target.upper(),
                '--protocol', protocol
            ]
        )

        if ports:
            # Iptables multiport module accepts up to 15 ports
            if len(ports) > 15:
                raise NotImplementedError("Up to 15 ports can be specified")
            ports = ",".join(ports)

            if protocol.lower() == 'all':
                # Adjust the protocol type, '--dports' option requires specific
                # type
                cmd[-1] = 'tcp'

            cmd.extend(['--match', 'multiport', '--dports', ports])

        return not self.host.executor().run_cmd(cmd)[0]

    def list_rules(self):
        """
        List all existing rules in a specific Chain

        Returns:
            list: List of existing rules
        """
        cmd = [self.firewall_service, '--list-rules', self.chain_name]
        rules = self.host.executor().run_cmd(cmd)[1]
        return rules.splitlines()

    def add_rule(self, dest, target, protocol='all', ports=None):
        """
        Add new firewall rule to a specific chain

        Args:
            dest (dict): 'address' key and value containing destination host or
               list of destination hosts
            target (str): Target rule to apply
            protocol (str): affected network protocol, Default is 'all'
            ports (list): list of ports to configure

        Returns:
            bool: False if adding new rule failed, True if it succeeded
        """
        return self.edit_chain(
            '--append', self.chain_name, self.address_type, dest, target,
            protocol, ports
        )

    def insert_rule(self, dest, target, protocol='all', ports=None,
                    rule_num=None):
        """
        Insert new firewall rule to a specific chain

        Args:
            dest (dict): 'address' key and value containing destination host or
               list of destination hosts
            target (str): Target rule to apply
            protocol (str): affected network protocol, Default is 'all'
            ports (list): list of ports to configure
            rule_num (str): the number given after the chain name indicates
            the position where the rule will be inserted. If the rule_num is
            not given , the new rule is inserted in the line 1.

        Returns:
            bool: False if inserting new rule failed, True if it succeeded
        """
        return self.edit_chain(
            '--insert', self.chain_name, self.address_type, dest, target,
            protocol, ports, rule_num
        )

    def delete_rule(self, dest, target, protocol='all', ports=None):
        """
        Delete existing firewall rule from a specific chain

        Args:
            dest (dict): 'address' key and value containing destination host or
               list of destination hosts
            target (str): Target rule to apply
            protocol (str): affected network protocol, Default is 'all'
            ports (list): list of ports to configure

        Returns:
            bool: False if deleting rule failed, True if it succeeded
        """
        return self.edit_chain(
            '--delete', self.chain_name, self.address_type, dest, target,
            protocol, ports
        )

    def clean_rules(self):
        """
        Delete all rules in a specific chain

        Returns:
            bool: True if succeeded, False otherwise
        """
        cmd = [self.firewall_service, '--flush', self.chain_name]
        return not self.host.executor().run_cmd(cmd)[0]
