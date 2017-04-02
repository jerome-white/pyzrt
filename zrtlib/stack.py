class IterableStack:
    def __init__(self):
        self.stack = []

    def __bool__:
        return bool(self.stack)
    
    def push(self, item):
        self.stack.append(list(item))

    def pop(self):
        if not self:
            raise BufferError()

        last = self.stack[-1]
        item = last.pop(0)
        if not last:
            self.peel()

        return item

    def peel(self):
        if self:
            self.stack.pop()
