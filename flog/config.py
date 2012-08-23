import os
import flask.config
import flog.source

CONFIG_DEFAULTS = dict(
    SRC_DIR = '.',
    POSTS_PATH = 'posts',
    THEME_PATH = 'spartan',
    FEED_SIZE = 10,
    ASCIIDOC_CONF = None,
    TAG_URI = None,
    ROOT_URL = None,
    SOURCE_URL = None,
    FEED_URL = None,
    JS_APPS_ROOT = 'apps',
    JS_APPS = {},
    STYLUS_PATH = 'stylus',
    CACHE_PATH = '/tmp/flog-cache',
    CACHE_EXPIRE = 300,
    INDEX_NAME = 'index',
    PLUGINS = {}
    )

class Config(flask.config.Config):
  def __init__(self, defaults):
    defaults.update(CONFIG_DEFAULTS)
    flask.config.Config.__init__(self, defaults.root_path, defaults=defaults)
    self['FLOG_CONF'] = os.environ.get('FLOG_CONF') or os.path.join(os.getcwd(), 'flogrc')
    self.from_pyfile(self.FLOG_CONF)

    self['FLOG_DIR'] = os.path.dirname(self.FLOG_CONF)
    self['SOURCE_URL'] = os.environ.get('SOURCE_URL') or self.SOURCE_URL
    theme_path = self.THEME_PATH
    self['THEME_PATH'] = os.path.join(self.FLOG_DIR, theme_path)
    if not os.path.isdir(self.THEME_PATH):
      self['THEME_PATH'] = os.path.join(self.root_path, 'themes', theme_path)
    if not self.FEED_URL:
      self['FEED_URL'] = self.ROOT_URL + '/' + self.POSTS_PATH + '/feed/'
    self['ASCIIDOC_FLOG_CONF'] = os.path.join(self.root_path, 'asciidoc-html5.conf')

    self['CACHE_PATH'] = os.environ.get('FLOG_CACHE') or self.CACHE_PATH
    self['CACHE_EXPIRE'] = os.environ.get('FLOG_CACHE_EXPIRE') or self.CACHE_EXPIRE

    self['SOURCE'] = flog.source.Source(self.CACHE_PATH, self.CACHE_EXPIRE)

  def __getattr__(self, name):
    return self.get(name)
