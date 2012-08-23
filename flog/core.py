import codecs
import dateutil.parser
import flog.config
import flog.route_helpers as helper
import importlib
import mimetypes
import os
import re
import sys
import urllib2
from StringIO import StringIO
from flask import Flask, Markup, render_template, send_file, abort
from flask import redirect, url_for, make_response
from flog.mime import mimetype
from os.path import abspath, dirname, join, isdir, isfile, getmtime
from os.path import normpath, commonprefix, splitext, split
from werkzeug.contrib.atom import AtomFeed

app = Flask(__name__)
c = flog.config.Config(app.config)
app.config = c

app.static_folder = join(c.THEME_PATH, 'static')
app.template_folder = c.THEME_PATH

# Config checks
if not c.ROOT_URL:
  raise Exception('ROOT_URL not set')
if not c.SOURCE_URL:
  raise Exception('SOURCE_URL not set')
if not isfile(c.FLOG_CONF):
  raise Exception('FLOG_CONF not found: ' + c.FLOG_CONF)
if not isdir(c.THEME_PATH):
  raise Exception('Theme not found: ' + c.THEME_PATH)


# Source and cache
def source_url(url, index=None):
  if index is None:
    return c.SOURCE.source(url)
  return c.SOURCE.source(join(url, index))

def source(path, index='index'):
  return source_url(join(c.SOURCE_URL, path), index=index)

def cache():
  return c.SOURCE.cache()


@helper.cache(app)
def generate_feed(_latest): # phantom argument for caching purposes
  '''Generate an atom feed from latests posts'''
  feed = AtomFeed('Recent posts',
      feed_url=c.FEED_URL,
      url=c.ROOT_URL,
      subtitle='...')
  for n, meta in helper.post_metas(app, c.FEED_SIZE):
    post_url = c.ROOT_URL + '/' + c.POSTS_PATH + '/' + str(n) + '/'
    post_id = c.TAG_URI.format(n=n) if c.TAG_URI else post_url
    feed.add(meta['title'],
        title_type='text',
        summary=meta.get('summary'),
        summary_type='html',
        author=meta['authors'],
        url=post_url,
        id=post_id,
        published=dateutil.parser.parse(meta['revisions'][0]['date']),
        updated=dateutil.parser.parse(meta['revisions'][-1]['date']))
  return feed.get_response()





# Routes
@app.route('/')
@mimetype('text/html')
def root():
  '''Site index'''
  @helper.source_index(app, join(c.SOURCE_URL, ''))
  def root_impl(src):
    content, meta = helper.parse_page(app, '')
    return render_template('index.html',
        posts=helper.post_metas(app, c.FEED_SIZE),
        content=content,
        meta=meta)
  return root_impl()

@app.route(join('/', c.POSTS_PATH, '<int:n>') + '/')
@mimetype('text/html')
def post(n):
  '''Blog post'''
  url_path = join(c.POSTS_PATH, str(n))
  @helper.source_index(app, join(c.SOURCE_URL, url_path))
  def post_impl(src):
    content, meta = helper.parse_page(app, url_path)
    prev_meta = None
    next_meta = None
    if n > 1:
      prev_meta = post_meta(app, n - 1)
    if n < latest_post_n(app):
      next_meta = post_meta(app, n + 1)
    return render_template('post.html',
        n=n,
        meta=meta,
        prev_meta=prev_meta,
        next_meta=next_meta,
        content=content)
  return post_impl()

@app.route(join('/', c.POSTS_PATH) + '/')
@mimetype('text/html')
def posts_index():
  '''Blog post index'''
  @helper.cache(app)
  def posts_index_impl():
    prev_meta = helper.latest_post_n(app) - c.FEED_SIZE
    if prev_meta <= 0:
      prev_meta = None
    return render_template('posts_index.html',
        posts=helper.parse_posts(app, c.FEED_SIZE),
        prev_meta=prev_meta)
  return posts_index_impl()

@app.route(join('/', c.JS_APPS_ROOT, '<path:path>'))
def js_apps(path):
  if not path:
    return catchall(c.JS_APPS_ROOT + '/')
  name_matches = [x for x in c.JS_APPS if path.startswith(x)]
  if not name_matches:
    return abort(404)
  name = max(name_matches, key=len)
  name_slash = name + '/'
  url = c.JS_APPS[name]
  @helper.source(app, url)
  def js_apps_impl(src):
    return src
  if path == name:
    return redirect(url_for('js_apps', path=path + '/'), code=301)
  if path not in (name, name_slash):
    src_url = join(split(url)[0], path[len(name_slash):])
    try:
      urllib2.urlopen(src_url)
      return redirect(src_url)
    except urllib2.URLError:
      return js_apps_impl()
  return js_apps_impl()

@app.route('/favicon.ico/')
@mimetype('image/x-icon')
def favicon():
  return abort(404)

@app.route(join('/', c.POSTS_PATH, 'feed') + '/')
@mimetype('application/atom+xml')
def posts_feed():
  '''Blog posts atom feed'''
  return generate_feed(latest_postn(app))

@app.route('/<path:path>')
def catchall(path):
  if path.endswith('/'):
    return helper.page(app, path)
  return redirect(url_for('catchall', path=path + '/'), code=301)


@app.context_processor
def inject_template_vars():
  '''Make these vars available to all templates'''
  return dict(len=len)


for mod_name, plug_conf in c.PLUGINS.items():
  module = importlib.import_module(mod_name)
  module.init_for_flog(app, plug_conf)
