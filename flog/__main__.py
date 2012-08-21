import os
import flask
import subprocess
import sys
import flog.config as config

if __name__ == '__main__':
  if 'source' in sys.argv:
    import flog.dev as dev
    dev.app.run()
  else:
    import flog.core as core
    if 'newcache' in sys.argv:
      subprocess.call(['rm', '-rf', core.CACHE_DIR])
      subprocess.call(['mkdir', core.CACHE_DIR])
    core.app.run(debug=True)
