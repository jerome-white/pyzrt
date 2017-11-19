from operator import methodcaller

class Ledger(set):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.fp.close()
        
    def __init__(self, ledger, node):
        super().__init__()

        suffix = '.dat'
        if ledger.is_dir():
            for i in ledger.glob('*' + suffix):
                with i.open() as fp:
                    self.update(map(methodcaller('strip'), fp.readlines()))
        else:
            ledger.mkdir(parents=True, exist_ok=True)

        output = ledger.joinpath(str(node)).with_suffix(suffix)
        self.fp = output.open('a')
        
    def record(self, key):
        print(key, file=self.fp, flush=True)
