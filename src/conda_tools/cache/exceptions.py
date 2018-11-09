class InvalidCachePackage(Exception):
    pass


class BadLinkError(Exception):
    """
    Error raised when a symbolic link is bad.

    Can also arise when the link is possibly malicious.
    """
    pass


class BadPathError(Exception):
    pass