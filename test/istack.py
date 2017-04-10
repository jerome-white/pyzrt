import string
import itertools

from zrtlib.selector.strategy import IterableStack

stack = IterableStack()
stack.push(range(10))
stack.push(map(lambda x: '.' + x, string.ascii_lowercase))

for (i, item) in enumerate(stack):
    print(i, item)
    if i == 5:
        stack.push(map(lambda x: '+' + x, string.ascii_lowercase))
