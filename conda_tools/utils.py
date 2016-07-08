import os


def is_hardlinked(f1, f2):
    """
    Determine if two files are hardlinks to the same inode.
    """
    try:
        s, d = os.stat(f1), os.stat(f2)
        return s.st_ino == d.st_ino and s.st_dev == d.st_dev
    except:
        return False

def is_softlinked(f):
    """
    Determine if two files are softlinked
    """
    return os.path.islink(f)
