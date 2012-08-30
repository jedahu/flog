import subprocess
import sys
import flog.core as core

if __name__ == '__main__':
    if 'newcache' in sys.argv:
      subprocess.call(['rm', '-rf', core.app.config.CACHE_PATH])
      subprocess.call(['mkdir', core.app.config.CACHE_PATH])
    core.app.run(debug=True)
