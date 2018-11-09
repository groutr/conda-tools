from __future__ import print_function

import json
import os
import bz2
from tarfile import (open as topen, TarFile, is_tarfile)
from os.path import (join, exists, isdir, realpath, normpath, split)
from tempfile import mkstemp
from hashlib import md5
try:
    from pathlib import PurePath
except:
    from pathlib2 import PurePath

from .common import lazyproperty, lru_cache
from .config import config
from .compat import dkeys, ditems, dvalues, intern
