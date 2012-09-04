import dateutil.parser
import flog.app
import importlib
import mimetypes
import os
from StringIO import StringIO
from flask import Flask, Markup, render_template, send_file, abort
from flask import redirect, url_for, make_response
from flog.mime import mimetype
from os.path import abspath, dirname, join, isdir, isfile, getmtime
from os.path import normpath, commonprefix, splitext, split
from werkzeug.contrib.atom import AtomFeed

app = flog.app.Flog(__name__)
c = app.config

@app.cache()
def generate_feed(_latest): # phantom argument for caching purposes
  '''Generate an atom feed from latests posts'''
  feed = AtomFeed('Recent posts',
      feed_url=c.FEED_URL,
      url=c.ROOT_URL,
      subtitle='...')
  for n, meta in app.post_metas(c.FEED_SIZE):
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
  @app.source_index(join(c.SOURCE_URL, ''))
  def root_impl(src):
    content, meta = app.parse_page('')
    return render_template('index.html',
        posts=app.post_metas(c.FEED_SIZE),
        content=content,
        meta=meta)
  return root_impl()

@app.route(join('/', c.POSTS_PATH, '<int:n>') + '/')
@mimetype('text/html')
def post(n):
  '''Blog post'''
  url_path = join(c.POSTS_PATH, str(n))
  @app.source_index(join(c.SOURCE_URL, url_path))
  def post_impl(src):
    content, meta = app.parse_page(url_path)
    prev_meta = None
    next_meta = None
    if n > 1:
      prev_meta = app.post_meta(n - 1)
    if n < app.latest_post_n():
      next_meta = app.post_meta(n + 1)
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
  @app.cache()
  def posts_index_impl():
    prev_meta = app.latest_post_n() - c.FEED_SIZE
    if prev_meta <= 0:
      prev_meta = None
    return render_template('posts_index.html',
        posts=list(app.parse_posts(c.FEED_SIZE)),
        prev_meta=prev_meta)
  return posts_index_impl()

@app.route('/favicon.ico/')
@mimetype('image/x-icon')
def favicon():
  return abort(404)

@app.route(join('/', c.POSTS_PATH, 'feed') + '/')
@mimetype('application/atom+xml')
def posts_feed():
  '''Blog posts atom feed'''
  return generate_feed(app.latest_post_n())

@app.route('/<path:path>')
def catchall(path):
  if path.endswith('/'):
    return app.page(path)
  return redirect(url_for('catchall', path=path + '/'), code=301)


@app.context_processor
def inject_template_vars():
  '''Make these vars available to all templates'''
  return dict(len=len)


for mod_name, plug_conf in c.PLUGINS.items():
  module = importlib.import_module(mod_name)
  module.init_for_flog(app, plug_conf)
