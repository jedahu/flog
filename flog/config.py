import os

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
    PROJECTS_ROOT = 'docs',
    PROJECTS = {},
    STYLUS_PATH = 'stylus')

def file_path():
  return os.environ.get('FLOG_CONF') or os.path.join(os.getcwd(), 'flogrc')

def apply_defaults(app):
  for key in CONFIG_DEFAULTS:
    if key not in app.config:
      app.config[key] = CONFIG_DEFAULTS[key]
