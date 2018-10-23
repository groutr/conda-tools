from __future__ import print_function, absolute_import, division

import sys
import operator

PY2 = sys.version_info.major == 2 and sys.version_info.minor == 7
PY3 = sys.version_info.major == 3 and sys.version_info.minor > 3

if PY2:
    from itertools import (imap as map, ifilter as filter, izip as zip)
    
    reduce = reduce
    range = xrange
    intern = intern

    keys = 'viewkeys'
    items = 'viewitems'
    values = 'viewvalues'

else:
    map = map
    filter = filter
    zip = zip

    from functools import reduce
    intern = sys.intern

    range = range

    keys = 'keys'
    items = 'items'
    values = 'values'

dkeys = operator.methodcaller(keys)
dvalues = operator.methodcaller(values)
ditems = operator.methodcaller(items)

# Standard library mappings
try:
    from urllib.request import urlopen
    from urllib.parse import urlparse
except ImportError:
    from urllib2 import urlopen
    from urlparse import urlparse
