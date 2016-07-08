import tarfile
import os
import json


class Package(object):

    def __init__(self, path, mode='r'):
        self.path = path
        self.mode = mode
        self._tarfile = tarfile.open(path, mode=mode)

