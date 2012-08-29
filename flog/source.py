import urllib2
import time
import flask
import os
from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

class SourceError(Exception):
  def __init__(self, code):
    self.code = code

class Source:
  def __init__(self, path, expire):
    cache_opts = {
        'cache.type': 'dbm',
        'cache.data_dir': path,
        'cache.expire': expire
        }
    self.cache_manager = CacheManager(**parse_cache_config_options(cache_opts))
    self.etag_cache = self.cache_manager.get_cache('etags', expire=365*24*60*60)
    self.fn_cache = self.cache_manager.get_cache('processed')
    self.url_cache = self.cache_manager.get_cache('urls')

  def url_cache_get_or_abort(self, url, code):
    try:
      val = self.url_cache._get_value(url)
      if val.has_value():
        ret = val._get_value()
        if ret:
          return ret
      raise SourceError(code)
    except Exception:
      raise SourceError(code)

  def url_cache_get_or_raise(self, url, error):
    val = self.url_cache._get_value(url)
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

  def cache(self, *args, **kwargs):
    return self.cache_manager.cache(*args, **kwargs)

  def source(self, url):
    def decorate(fn):
      def wrapper(*args, **kwargs):
        def create_url_cache_value():
          headers = {}
          stored_etag = self.etag_cache.get(key=url, createfunc=lambda:None)
          if stored_etag:
            headers = {'If-None-Match': stored_etag}
          request = urllib2.Request(url, headers=headers)
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
            return self.url_cache_get_or_raise(url, error)
          if error_code in (404, 410, 451):
            return flask.abort(e.code)
          if error:
            return self.url_cache_get_or_raise(url, error)
          etag = response.info().getheader('ETag', None)
          if etag:
            self.etag_cache.put(key=url, value=etag)
          return response.read()

        def create_fn_cache_value():
          if url:
            val = self.url_cache.get(key=url, createfunc=create_url_cache_value)
            return fn(val, *args, **kwargs)
          else:
            return fn(*args, **kwargs)

        try:
          return self.fn_cache.get(key=fn.__name__+url, createfunc=create_fn_cache_value)
        except SourceError, e:
          return flask.abort(e.code)

      return wrapper

    return decorate
