import shutil as sh

from pyzrt.indri.sys import Search

class IndriSearch(Search):
    def __init__(self, index, qrels, indri=None):
        super().__init__(qrels)

        self.index = index
        self.indri = sh.which('IndriRunQuery') if indri is None else str(indri)

    def execute(self, query, baseline=None):
        cmd = [
            self.indri,
            '-trecFormat=true',
            '-count={0}'.format(self.count),
            '-index={0}'.format(self.index),
            str(query),
        ]
        if baseline:
            cmd.insert(-1, '-baseline='.format(baseline))

        yield from self._shell(cmd)
