import sys
from functools import singledispatch

__all__ = [
    'walk'
]

@singledispatch
def walk(path):
    if path.is_dir():
        for i in path.iterdir():
            yield from walk(i)
    else:
        yield path

@walk.register(str)
def _(path):
    yield from walk(Path(path))

@walk.register(type(None))
def _(path):
    for i in sys.stdin:
        yield from walk(Path(i.strip()))
