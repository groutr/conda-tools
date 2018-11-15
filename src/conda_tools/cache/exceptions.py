
class CacheException(Exception):
    pass

class InvalidCachePackage(CacheException):
    pass


class BadLinkError(CacheException):
    """
    Error raised when a symbolic link is bad.

    Can also arise when the link is possibly malicious.
    """
    pass


class BadPathError(CacheException):
    pass