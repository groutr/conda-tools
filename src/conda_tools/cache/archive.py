from os.path import realpath, normpath, join
from pathlib import PurePath

def sane_members(members, destination):
    resolve = lambda path: realpath(normpath(join(destination, path)))

    destination = PurePath(destination)

    for member in members:
        mpath = PurePath(resolve(member.path))

        # Check if mpath is under destination
        if destination not in mpath.parents:
            raise BadPathError("Bad path to outside destination directory: {}".format(mpath))
        elif member.issym() or member.islnk():
            # Check link to make sure it resolves under destination
            lnkpath = PurePath(member.linkpath)
            if lnkpath.is_absolute() or lnkpath.is_reserved():
                raise BadLinkError("Bad link: {}".format(lnkpath))

            # resolve the link to an absolute path
            lnkpath = PurePath(resolve(lnkpath))
            if destination not in lnkpath.parents:
                raise BadLinkError("Bad link to outside destination directory: {}".format(lnkpath))

        yield member