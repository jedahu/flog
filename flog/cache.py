import urllib2
import os
import hashlib
import flask
from contextlib import contextmanager

class Locked(Exception):
  def __init__(self, lock_file):
    self.lock_file = lock_file

@contextmanager
def file_lock(lock_file):
  if os.path.exists(lock_file):
    raise Locked(lock_file)
  else:
    open(lock_file, 'w').write('1')
    try:
      yield
    finally:
      os.remove(lock_file)


class Cache:
  def __init__(self, cache_dir=None, source_url=None, on=True):
    if not cache_dir:
      raise Exception, 'No cache_dir given.'
    if not source_host:
      raise Exception, 'No source_host given.'
    self.ison = on
    self.cache_dir = cache_dir
    self.source_url = source_url
    if not os.path.isdir(cache_dir) and self.ison:
      os.mkdirs(cache_dir)

  def cache_paths(self, path):
    sha1 = hashlib.sha1()
    sha1.update(path)
    fname = sha1.hexdigest()
    data_path = os.path.join(self.cache_dir, fname)
    etag_path = data_path + '.etag'
    lock_path = data_path + '.lock'
    return (data_path, etag_path, lock_path)

  def get_etag(self, path):
    data_path, etag_path, _ = self.cache_paths(path)
    if os.path.isfile(data_path) and os.path.isfile(etag_path):
      with open(etag_path) as ef:
        return ef.read()
    return None

  def write_cache_files(self, paths, data, etag):
    data_path, etag_path, lock_path = paths
    try:
      with file_lock(lock_path):
        with NamedTemporaryFile(mode='w', dir=self.cache_dir) as tmp_df:
          tmp_df.write(data)
          tmp_df.flush()
          os.rename(tmp_df.name, data_path)
        if etag:
          with NamedTemporaryFile(mode='w', dir=self.cache_dir) as tmp_ef:
            tmp_ef.write(etag)
            tmp_ef.flush()
            os.rename(tmp_ef.name, etag_path)
    except Locked, e:
      print 'File locked:', e.lock_file

  def cache(self, path, mimetype='text/html'):
    full_url = os.path.join(self.source_url, path)
    paths = self.cache_paths(path)
    data_path, etag_path, lock_path = paths
    def decorate(fn):
      def wrapper(*args, **kwargs):
        request = None
        if self.ison:
          etag = self.get_etag(path)
          request = urllib2.Request(full_url, headers={'If-None-Match': etag})
        else:
          request = urllib2.Request(full_url)
        use_cache = False
        error_code = None
        try:
          response = urllib2.urlopen(request)
        except HTTPError, e:
          error_code = e.code
          if e.code == 304:
            use_cache = True
        except URLError:
          error_code = e.code
          use_cache = True
        response_info = response.info()
        if self.ison and not error_code:
          data = fn(*args, **kwargs)
          etag = response.getheader('ETag', None)
          self.write_cache_files(paths, data, etag)
        if self.ison and (use_cache or not error_code):
          if error_code:
            if os.path.isfile(data_path):
              return flask.send_file(data_path, mimetype=mimetype)
            else:
              return flask.abort(error_code)
          else:
            return flask.send_file(data_path, mimetype=mimetype)
        elif self.ison:
          return flask.abort(error_code)
        else:
          data = fn(*args, **kwargs)
          resp = flask.make_response(data)
          resp.mimetype=mimetype
          return resp
      return wrapper
    return decorate
