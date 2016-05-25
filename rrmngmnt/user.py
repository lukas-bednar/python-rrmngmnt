from rrmngmnt.resource import Resource


class User(Resource):
    def __init__(self, name, password):
        """
        :param name: user name
        :type name: str
        :param password: password
        :type password: str
        """
        super(User, self).__init__()
        self.name = name
        self.password = password

    @property
    def full_name(self):
        return self.get_full_name()

    def get_full_name(self):
        return self.name


class RootUser(User):
    NAME = 'root'

    def __init__(self, password):
        super(RootUser, self).__init__(self.NAME, password)


class Domain(Resource):
    def __init__(self, name, provider=None, server=None):
        """
        :param name: name of domain
        :type name: str
        :param provider: name of provider / type of domain
        :type provider: str
        :param server: server address
        :type server: str
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
        :param name: user name
        :type name: str
        :param password: password
        :type password: str
        :param domain: user domain
        :type domain: instance of Domain
        """
        super(ADUser, self).__init__(name, password)
        self.domain = domain

    def get_full_name(self):
        return "%s@%s" % (self.name, self.domain.name)
