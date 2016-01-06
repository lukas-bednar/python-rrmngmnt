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

    @property
    def logger(self):
        logger = logging.getLogger(self.__class__.__name__)
        return self.LoggerAdapter(logger, {'self': self})
