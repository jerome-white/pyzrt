class IterableStack:
    def __init__(self):
        self.stack = []

    def push(self, item):
        self.stack.append(list(item))

    def pop(self):
        if not self.stack:
            raise BufferError()

        last = self.stack[-1]
        item = last.pop(0)
        if not last:
            self.stack.pop()

        return item
