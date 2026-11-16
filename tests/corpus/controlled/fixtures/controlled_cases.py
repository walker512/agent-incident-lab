import sys, json, subprocess
from pathlib import Path
mode = sys.argv[1]
if mode == 'missing': Path('deliberately_absent.txt').read_text()
elif mode == 'invalid-json': json.loads('{invalid')
elif mode == 'timeout': subprocess.run([sys.executable, '-c', 'import time; time.sleep(2)'], timeout=0.1, check=True)
elif mode == 'success': print('CONTROL_SUCCESS')
else: raise ValueError('unsupported scenario')
