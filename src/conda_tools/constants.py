import enum


class LINK_TYPE(enum.Enum):
    hardlink = 1
    softlink = 2
    copy = 3
    directory = 4

_LINK_MAP = {'hard-link': LINK_TYPE.hardlink,
            'soft-link': LINK_TYPE.softlink,
            'copy': LINK_TYPE.copy,
            'directory': LINK_TYPE.directory}

def cast_link_type(value):
    if isinstance(value, str):
        return _LINK_MAP[value]
    else:
        return LINK_TYPE(value)
