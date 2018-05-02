try:
    import enum
except ImportError:
    import enum34 as enum

class LINK_TYPE(enum.Enum):
    hardlink = 1
    softlink = 2
    copy = 3
    directory = 4

