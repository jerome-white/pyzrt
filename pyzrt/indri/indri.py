import shutil as sh
from tempfile import NamedTemporaryFile

from pyzrt.indri.sys import Search

class IndriSearch(Search):
    def __init__(self, index, qrels):
        super().__init__(qrels)

        self.index = index
        self.indri = sh.which('IndriRunQuery')

    def execute(self, query, baseline=None):
        '''Build/execute the Indri command

        '''

        with NamedTemporaryFile(mode='w') as fp:
            print(query, file=fp, flush=True)
            cmd = [
                self.indri,
                '-trecFormat=true',
                '-count={0}'.format(self.count),
                '-index={0}'.format(self.index),
                fp.name,
            ]
            if baseline:
                cmd.insert(-1, '-baseline='.format(baseline))
                
            yield from self._shell(cmd)
