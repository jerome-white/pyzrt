class Segmenter(list):
    def __init__(self, distance_string_constructor, rate=1):
        self.mkstr = distance_string_constructor
        self.rate = rate

    def segment(self, data):
        raise NotImplementedError

class Slicer(Segmenter):
    def segment(self, data):
        for i in range(0, len(data), self.rate):
            yield self.mkstr(data[i:i+self.rate])
            
