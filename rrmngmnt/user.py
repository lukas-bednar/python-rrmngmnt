import os
from rrmngmnt.resource import Resource


class User(Resource):
    def __init__(self, name, password):
        """
        Args:
            password (str): Password
            name (str): User name
        """
        super(User, self).__init__()
        self.name = name
        self.password = password

    @property
    def full_name(self):
        return self.get_full_name()

    def get_full_name(self):
        return self.name

    @property
    def credentials(self):
        return self.get_credentials()

    def get_credentials(self):
        return self.password


class UserWithPKey(User):
    def __init__(self, name, private_key):
        """
        Args:
            private_key (str): Path to private key
            name (str): User name
        """
        super(UserWithPKey, self).__init__(name, None)
        self.private_key = os.path.expanduser(private_key)

    def get_credentials(self):
        return self.private_key


class RootUser(User):
    NAME = 'root'

    def __init__(self, password):
        super(RootUser, self).__init__(self.NAME, password)


class Domain(Resource):
    def __init__(self, name, provider=None, server=None):
        """
        Args:
            server (str): Server address
            name (str): Name of domain
            provider (str): Name of provider / type of domain
        """
        super(Domain, self).__init__()
        self.name = name
        self.provider = provider
        self.server = server


class InternalDomain(Domain):
    NAME = 'internal'

    def __init__(self):
        super(InternalDomain, self).__init__(self.NAME)


class ADUser(User):
    def __init__(self, name, password, domain):
        """
        Args:
            domain (instance of Domain): User domain
            password (str): Password
            name (str): User name
        """
        super(ADUser, self).__init__(name, password)
        self.domain = domain

    def get_full_name(self):
        return "%s@%s" % (self.name, self.domain.name)
