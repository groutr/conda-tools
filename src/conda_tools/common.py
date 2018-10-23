from __future__ import print_function

try:
    from functools import lru_cache
except ImportError:
    from .lru_cache import lru_cache

from functools import wraps

from .compat import ditems, dvalues, intern

class lazyproperty(object):
    def __init__(self, func):
        self._func = func
        wraps(self._func,)(self)

    def __get__(self, instance, owner):
        if instance is None:
            return None

        class Sentinel(object):
            __slots__ = []

        result = instance.__dict__.get(self.__name__, Sentinel())
        if isinstance(result, Sentinel):
            result = instance.__dict__[self.__name__] = self._func(instance)
        return result
    

    def __set__(self, instance, value):
        raise AttributeError('Cannot set read-only attribute on {}'.format(type(instance)))


def intern_keys(d):
    """
    Intern the string keys of d
    """
    for k, v in ditems(d):
        try:
            d[intern(k)] = v
        except TypeError:
            d[k] = v

        if isinstance(v, dict):
            d[k] = intern_keys(v)
    return d