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
        self.set_logger(logger)

    @property
    def logger(self):
        return self._logger_adapter

    def set_logger(self, logger):
        if isinstance(logger, logging.Logger):
            self._logger_adapter = self.LoggerAdapter(logger, {'self': self})
        elif isinstance(logger, logging.LoggerAdapter):
            self._logger_adapter = logger
