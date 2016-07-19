class Segmenter:
    def __init__(self, rate=1):
        self.rate = rate

    def segment(self, data):
        raise NotImplementedError

class Slicer(Segmenter):
    def segment(self, data):
        return [ data[i:i+self.rate] for i in range(0, len(data), self.rate) ]
