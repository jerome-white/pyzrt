import string
import itertools

from zrtlib.stack import IterableStack

stack = IterableStack()
stack.push(range(10))
stack.push(map(lambda x: '.' + x, string.ascii_lowercase))

for i in itertools.count():
    item = stack.pop()
    if item is None:
        break
    print(i, item)
    if i == 5:
        stack.push(map(lambda x: '+' + x, string.ascii_lowercase))
