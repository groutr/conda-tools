import stat
from os import lstat, error


def is_hardlinked(f1, f2):
    """
    Determine if two files are hardlinks to the same inode.
    """
    try:
        s, d = lstat(f1), lstat(f2)
        return s.st_ino == d.st_ino and s.st_dev == d.st_dev
    except error:
        return False

def is_executable(mode):
    """
    Check if mode is executable

    Mode can be specified in octal or as an int.
    """
    if isinstance(mode, str) and mode.startswith('0o'):
        mode = int(mode, 8)
    
    ux, gx, ox = stat.S_IXUSR, stat.S_IXGRP, stat.S_IXOTH

    return ((mode & ux) or (mode & gx) or (mode & ox)) > 0
