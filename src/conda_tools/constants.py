try:
    import enum
except ImportError:
    import enum34 as enum

class LINK_TYPE(enum.Enum):
    hardlink = 1
    softlink = 2
    copy = 3
    directory = 4

def cast_link_type(value):
    if isinstance(value, str):
        if value == 'hard-link':
            return LINK_TYPE.hardlink
        elif value == 'soft-link':
            return LINK_TYPE.softlink
        elif value == 'copy':
            return LINK_TYPE.copy
        elif value == 'directory':
            return LINK_TYPE.directory
        else:
            raise ValueError("Unknown value: " + value)
    else:
        return LINK_TYPE(value)
