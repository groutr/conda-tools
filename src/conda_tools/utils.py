from __future__ import print_function

import stat
import io
import platform
from collections import defaultdict
from os.path import exists, join
from os import lstat, error, walk

def index_inodes(root):
    index = defaultdict(list)
    for root, dirs, files in walk(root):
        for f in files:
            path = join(root, f)
            fstat = lstat(path)
            index[(fstat.st_dev, fstat.st_ino)].append(path)
    return dict(index)

def is_hardlinked(f1, f2):
    """
    Determine if two files are hardlinks to the same inode.
    """
    try:
        s, d = lstat(f1), lstat(f2)
        return s.st_ino == d.st_ino and s.st_dev == d.st_dev
    except:
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

def is_macho(file):
    """
    Check if file is a valid Mach O binary (OS X).
    """
    magic = _get_magic(file, 4)
    if (magic == b'\xcf\xfa\xed\xfe' or magic == b'\xfe\xed\xfa\xcf' or
        magic == b'\xce\xfa\xed\xfe' or magic == b'\xfe\xed\xfa\xce'):
        return True
    return False

def is_pe(file):
    """
    Check if file is valid Windows PE binary.
    """
    if _get_magic(file, 2) == b'MZ':
        return True
    return False

def is_elf(file):
    """
    Check if file is valid ELF binary.
    """

    if _get_magic(file, 4) == b'\x7fELF':
        return True
    return False

def _get_magic(file, length):
    """
    Read magic number of file.

    file: Either file object or path to file
    length: number of bytes to read from beginning.
        Windows: first 2 bytes are magic number
        Linux, OS X: first 4 bytes are magic number

    Returns a byte string

    Raise errors if file is not readable or opened in binary on Windows.

    """
    always_bytes = lambda x: x if isinstance(x, bytes) else x.encode()

    try:
        if file.readable():
            if platform.system() == 'Windows' and 'b' not in file.mode:
                raise IOError("File object must be opened in binary mode")

            if file.seekable():
                old_pos = file.tell()
                file.seek(0)
                magic = always_bytes(file.read(length))
                file.seek(old_pos)
                return magic
            else:
                # Non seekable file, like ExFileObject from tarfiles
                raise IOError("Unable to seek 0 and read")
        else:
            raise IOError("File not readable")
    except AttributeError:
        # Hope that file is a path to the file in question
        if isinstance(file, str) and exists(file):
            with open(file, 'rb') as fi:
                magic = fi.read(length)
            return magic

        # Raise exception as last resort
        raise

def block_iter(fileobj, blocksize=io.DEFAULT_BUFFER_SIZE):
    """Iterate over fileobj and yield blocks up to size of blocksize.

    Arguments:
        fileobj {[type]} -- Any object supporting .read() method.

    Notes:
        Iteration will attempt to find EOF position and iterate till EOF.
        Otherwise, iteration will terminate on the first empty string.
    """
    if fileobj.seekable():
        # Discover the end of the file
        pos = fileobj.tell()
        final_size = fileobj.seek(0, io.SEEK_END)
        fileobj.seek(pos)

        while fileobj.tell() < final_size:
            yield fileobj.read(blocksize)
    else:
        while True:
            blk = fileobj.read(blocksize)
            if blk:
                yield blk
            else:
                break
