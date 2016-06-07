from functools import wraps


class lazyproperty(object):
    def __init__(self, func):
        self._func = func
        wraps(self._func,)(self)

    def __get__(self, instance, owner):
        if instance is None:
            return None

        result = instance.__dict__[self.__name__] = self._func(instance)
        return result
