import urllib2
import time
import flask
import beaker.cache
import beaker.util
import os

class SourceError(Exception):
  def __init__(self, code):
    self.code = code

class Source:
  def __init__(self, cache_manager=None):
    if not cache_manager:
      raise Exception, 'No cache_manager.'
    self.etags = {}
    self.cache_manager = cache_manager
    self.cache = self.cache_manager.get_cache('processed')
    self.raw_caches = {}

  def raw_cache_get_or_abort(self, cache, key, code):
    try:
      val = cache._get_value(key)
      if val.has_value():
        ret = val._get_value()
        if ret:
          return ret
      raise SourceError(code)
    except Exception:
      raise SourceError(code)

  def raw_cache_get_or_raise(self, cache, key, error):
    val = cache._get_value(key)
    if val.has_value():
      val.namespace.acquire_read_lock()
      try:
        _stored, _expired, ret = val._get_value()
        if ret:
          return ret
      except Exception:
        raise error
      finally:
        val.namespace.release_read_lock()
    raise error

  def source(self, source_url, path):
    full_url = os.path.join(source_url, path)
    raw_cache = self.cache_manager.get_cache(source_url)
    def decorate(fn):
      def wrapper(*args, **kwargs):
        def create_raw_cache_value():
          headers = {}
          stored_etag = self.etags.get(full_url)
          if stored_etag:
            headers = {'If-None-Match': stored_etag}
          request = urllib2.Request(full_url, headers=headers)
          error = None
          error_code = None
          try:
            response = urllib2.urlopen(request)
          except urllib2.HTTPError, e:
            error_code = e.code
            error = e
          except urllib2.URLError, e:
            error = e
          if error_code == 304:
            return self.raw_cache_get_or_raise(raw_cache, path, error_code)
          if error_code in (404, 410, 451):
            return flask.abort(e.code)
          if error:
            return self.raw_cache_get_or_raise(raw_cache, path, error)
          etag = response.info().getheader('ETag', None)
          if etag:
            self.etags[full_url] = etag
          return response.read()

        def create_cache_value():
          if path is not None:
            val = raw_cache.get(key=str(path), createfunc=create_raw_cache_value)
            return fn(val, *args, **kwargs)
          else:
            return fn(*args, **kwargs)

        try:
          return self.cache.get(key=fn.__name__+str(path), createfunc=create_cache_value)
        except SourceError, e:
          return flask.abort(e.code)

      return wrapper

    return decorate
