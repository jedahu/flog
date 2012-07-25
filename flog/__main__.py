import flog
import subprocess
import sys

if __name__ == '__main__':
  if 'newcache' in sys.argv and flog.CACHE_DIR != 'nocache':
    subprocess.call(['rm', '-rf', flog.CACHE_DIR])
  flog.app.run(debug=True)
