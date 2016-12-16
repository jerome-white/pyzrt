import random
import operator as op
from collections import OrderedDict

class RGBColor:
    def __init__(self, buff=0.3):
        self.rgb = 256
        self.buff = buff
        self.used = OrderedDict([ (x, []) for x in [ 'r', 'g', 'b' ]])

    def ball(self, center):
        plus_minus = self.rgb * self.buff
        rng = [ round(f(center, plus_minus)) for f in (op.add, op.sub) ]
        yield from range(*rng)

    def __next__(self):
        i = 0
        keys = list(self.used.keys())

        while i < len(keys):
            k = keys[i]
            v = random.randrange(self.rgb)

            exists = False
            for j in self.ball(v):
                if j in self.used[k]:
                    exists = True
                    break

            if not exists:
                self.used[k].append(v)
                i += 1

        return self.tostring(*[ self.used[x][-1] for x in keys ])

class HexColor(RGBColor):
    def tostring(self, r, g, b):
        return ('#' + '{:02X}' * 3).format(r, g, b)
