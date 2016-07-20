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

