from functools import wraps
from sys import intern

class lazyproperty(object):
    class Sentinel:
        __slots__ = []

    def __init__(self, func):
        self._func = func
        wraps(self._func,)(self)

    def __get__(self, instance, owner):
        if instance is None:
            return None

        result = instance.__dict__.get(self.__name__, self.Sentinel())
        if isinstance(result, self.Sentinel):
            result = instance.__dict__[self.__name__] = self._func(instance)
        return result


    def __set__(self, instance, value):
        raise AttributeError('Cannot set read-only attribute on {}'.format(type(instance)))


def intern_keys(d):
    """
    Intern the string keys of d
    """
    for k, v in d.items():
        try:
            d[intern(k)] = v
        except TypeError:
            d[k] = v

        if isinstance(v, dict):
            d[k] = intern_keys(v)
    return d