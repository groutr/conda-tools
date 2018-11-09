"""
Adapted from conda/history.py
Licensed under BSD 3-clause license.
"""
from __future__ import print_function


import re
import time
from json import loads
from os.path import isfile, join
from functools import lru_cache

from ..common import lazyproperty

class CondaHistoryException(Exception):
    pass


class CondaHistoryWarning(Warning):
    pass


def dist2pair(dist):
    dist = str(dist)
    if dist.endswith(']'):
        dist = dist.split('[', 1)[0]
    if dist.endswith('.tar.bz2'):
        dist = dist[:-8]
    parts = dist.split('::', 1)
    return 'defaults' if len(parts) < 2 else parts[0], parts[-1]


def dist2quad(dist):
    channel, dist = dist2pair(dist)
    parts = dist.rsplit('-', 2) + ['', '']
    return (parts[0], parts[1], parts[2], channel)

def is_diff(content):
    return any(s.startswith(('-', '+')) for s in content)


def pretty_diff(diff):
    added = {}
    removed = {}
    for s in diff:
        fn = s[1:]
        name, version, _, channel = dist2quad(fn)
        if channel != 'defaults':
            version += ' (%s)' % channel
        if s.startswith('-'):
            removed[name.lower()] = version
        elif s.startswith('+'):
            added[name.lower()] = version
    changed = set(added) & set(removed)
    for name in sorted(changed):
        yield ' %s  {%s -> %s}' % (name, removed[name], added[name])
    for name in sorted(set(removed) - changed):
        yield '-%s-%s' % (name, removed[name])
    for name in sorted(set(added) - changed):
        yield '+%s-%s' % (name, added[name])


def pretty_content(content):
    if is_diff(content):
        return pretty_diff(content)
    else:
        return iter(sorted(content))


class History(object):

    def __init__(self, prefix):
        meta_dir = join(prefix, 'conda-meta')
        self.path = join(meta_dir, 'history')

    @lazyproperty
    def _parse(self):
        """
        parse the history file and return a list of
        tuples(datetime strings, set of distributions/diffs, comments)
        """
        res = []
        if not isfile(self.path):
            return res
        sep_pat = re.compile(r'==>\s*(.+?)\s*<==')
        with open(self.path, 'r') as f:
            lines = f.read().splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            m = sep_pat.match(line)
            if m:
                res.append((m.group(1), set(), []))
            elif line.startswith('#'):
                res[-1][2].append(line)
            else:
                res[-1][1].add(line)
        return res

    @lazyproperty
    def get_user_requests(self):
        """
        return a list of user requested items.  Each item is a dict with the
        following keys:
        'date': the date and time running the command
        'cmd': a list of argv of the actual command which was run
        'action': install/remove/update
        'specs': the specs being used
        """
        res = []
        com_pat = re.compile(r'#\s*cmd:\s*(.+)')
        spec_pat = re.compile(r'#\s*(\w+)\s*specs:\s*(.+)')
        for dt, unused_cont, comments in self._parse:
            item = {'date': dt}
            for line in comments:
                m = com_pat.match(line)
                if m:
                    argv = m.group(1).split()
                    if argv[0].endswith('conda'):
                        argv[0] = 'conda'
                    item['cmd'] = argv
                m = spec_pat.match(line)
                if m:
                    action, specs = m.groups()
                    item['action'] = action
                    item['specs'] = loads(specs.replace("'", "\""))
            if 'cmd' in item:
                res.append(item)
        return res

    @lazyproperty
    def construct_states(self):
        """
        return a list of tuples(datetime strings, set of distributions)
        """
        res = []
        cur = set([])
        for dt, cont, unused_com in self._parse:
            if not is_diff(cont):
                cur = cont
            else:
                for s in cont:
                    if s.startswith('-'):
                        cur.discard(s[1:])
                    elif s.startswith('+'):
                        cur.add(s[1:])
                    else:
                        raise CondaHistoryException('Did not expect: %s' % s)
            res.append((dt, cur.copy()))
        return res

    def get_state(self, rev=-1):
        """
        return the state, i.e. the set of distributions, for a given revision,
        defaults to latest (which is the same as the current state when
        the log file is up-to-date)
        """
        states = self.construct_states
        if not states:
            return set([])
        times, pkgs = zip(*states)
        return pkgs[rev]


    def print_log(self):
        for i, (date, content, unused_com) in enumerate(self._parse):
            print('%s  (rev %d)' % (date, i))
            for line in pretty_content(content):
                print('    %s' % line)
            print()

    @lazyproperty
    def object_log(self):
        result = []
        for i, (date, content, unused_com) in enumerate(self._parse):
            # Based on Mateusz's code; provides more details about the
            # history event
            event = {
                'date': date,
                'rev': i,
                'install': [],
                'remove': [],
                'upgrade': [],
                'downgrade': []
            }
            added = {}
            removed = {}
            if is_diff(content):
                for pkg in content:
                    name, version, build, channel = dist2quad(pkg[1:])
                    if pkg.startswith('+'):
                        added[name.lower()] = (version, build, channel)
                    elif pkg.startswith('-'):
                        removed[name.lower()] = (version, build, channel)

                changed = set(added) & set(removed)
                for name in sorted(changed):
                    old = removed[name]
                    new = added[name]
                    details = {
                        'old': '-'.join((name,) + old),
                        'new': '-'.join((name,) + new)
                    }

                    if new > old:
                        event['upgrade'].append(details)
                    else:
                        event['downgrade'].append(details)

                for name in sorted(set(removed) - changed):
                    event['remove'].append('-'.join((name,) + removed[name]))

                for name in sorted(set(added) - changed):
                    event['install'].append('-'.join((name,) + added[name]))
            else:
                for pkg in sorted(content):
                    event['install'].append(pkg)
            result.append(event)
        return result

        def __repr__(self):
            return 'History({}) @ {}'.format(self.path, hex(id(self)))

        def __str__(self):
            return 'History({})'.format(self.path)
