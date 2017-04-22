import unittest
from pathlib import Path

from zrtlib import zutils

class TestStringMethods(unittest.TestCase):
    def setUp(self):
        self.fp = Path('evals/progressive/04/ua/WSJQ00251-0000').open()

    def tearDown(self):
        self.fp.close()

    def test_summaryNotReported(self):
        for (i, _) in zutils.read_trec(self.fp):
            self.assertFalse(i < 0)

    def test_summaryReported(self):
        negatives = []
        for (i, _) in zutils.read_trec(self.fp, True):
            if i < 0:
                negatives.append(i)

        self.assertTrue(len(negatives) == 1)

    def test_summaryReportedOnce(self):
        negatives = []
        for (i, _) in zutils.read_trec(self.fp, True):
            if i < 0:
                negatives.append(i)
        val = negatives.pop()
        
        self.assertEqual(val, -1)

    def allComplete(self, summary):
        keys = None
        for (_, results) in zutils.read_trec(self.fp, summary):
            if keys is None:
                keys = set(results.keys())
            else:
                current = set(results.keys())
                self.assertFalse(keys.isdisjoint(current))

    def test_allCompleteWithSummary(self):
        self.allComplete(True)

    def test_allCompleteWithoutSummary(self):
        self.allComplete(False)
            
unittest.main()
