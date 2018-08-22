import six
import socket


def fqdn2ip(fqdn):
    """
    translate fqdn to IP

    Args:
        fqdn (str): host name

    Returns:
        str: IP address
    """
    try:
        return socket.gethostbyname(fqdn)
    except (socket.gaierror, socket.herror) as ex:
        args = list(ex.args)
        message = "%s: %s" % (fqdn, args[1])
        args[1] = message
        ex.strerror = message
        ex.args = tuple(args)
        raise


def normalize_string(data):
    """
    get normalized string

    Args:
        data (object): data to process
    Returns:
        object: normalized string
    """
    if isinstance(data, six.binary_type):
        data = data.decode('utf-8', errors='replace')
    if isinstance(data, six.text_type):
        data = data.encode('utf-8', errors='replace')
    return data
