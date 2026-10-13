"""Protected integration caller for both independently implemented formats."""
import argparse
import importlib
import sys


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('source', choices=('jsonl', 'csv'))
    parser.add_argument('target', choices=('jsonl', 'csv'))
    args = parser.parse_args(argv)
    source = importlib.import_module('ledgerfmt.formats.' + args.source)
    target = importlib.import_module('ledgerfmt.formats.' + args.target)
    try:
        records = source.load(sys.stdin)
        target.dump(records, sys.stdout)
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0

if __name__ == '__main__': raise SystemExit(main())
