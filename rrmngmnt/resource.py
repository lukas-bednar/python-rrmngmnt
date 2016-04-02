import logging


class Resource(object):
    """
    Common base for any kind of resource across rhevm tests
    """
    class LoggerAdapter(logging.LoggerAdapter):
        def warn(self, *args, **kwargs):
            """
            Just alias for warning, the warn is provided by logger instance,
            but not by adapter.
            """
            self.warning(*args, **kwargs)

    def __init__(self):
        super(Resource, self).__init__()
        logger = logging.getLogger(self.__class__.__name__)
        self._logger_adapter = self.LoggerAdapter(logger, {'self': self})

    @property
    def logger(self):
        return self._logger_adapter
