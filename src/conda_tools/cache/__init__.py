import os


def init_cache(prefix: str, name: str, mode: int=0o777) -> None:
    os.mkdir(os.path.join(prefix, name), mode)
