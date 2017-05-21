from configparser import ConfigParser
from functools import singledispatch

class Comment:
    def __init__(self, fp, comment='#'):
        self.fp = fp
        self.comment = comment + ' '

class CommentReader(Comment):
    def __iter__(self):
        return self

    def __next__(self):
        line = self.fp.readline()
        if not line or line[:len(self.comment)] != self.comment:
            raise StopIteration

        return line[len(self.comment):].strip()

class CommentWriter(Comment):
    def write(self, s):
        return self.fp.write(self.comment + s) - len(self.comment)

@singledispatch
def tostring(value):
    return value if value is not None else ''

@tostring.register(list)
def _(value):
    return tostring(','.join(map(str, value)))

def save(fp, args):
    opts = { x: tostring(getattr(args, x)) for x in vars(args) }
    ConfigParser(opts).write(CommentWriter(fp))

def load(fp):
    cp = ConfigParser()
    cp.read_file(CommentReader(fp))

    sections = list(cp.keys())
    assert(len(sections) == 1)
    default_section = sections.pop()

    return cp[default_section]
