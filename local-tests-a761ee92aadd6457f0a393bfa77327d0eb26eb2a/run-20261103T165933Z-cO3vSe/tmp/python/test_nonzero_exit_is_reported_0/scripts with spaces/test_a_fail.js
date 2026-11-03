import sys
print('before failure', flush=True)
print('failure stderr', file=sys.stderr)
sys.exit(7)
