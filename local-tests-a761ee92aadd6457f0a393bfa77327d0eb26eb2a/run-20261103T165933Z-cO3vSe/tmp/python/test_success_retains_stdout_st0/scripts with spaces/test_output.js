import sys
from pathlib import Path
print('stdout marker')
print('stderr marker', file=sys.stderr)
print('cwd=' + str(Path.cwd()))
