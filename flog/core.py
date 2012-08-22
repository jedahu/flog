import os
from os.path import abspath, dirname, join, isdir, isfile, getmtime
from os.path import normpath, commonprefix, splitext
import sys
import re
from StringIO import StringIO
from werkzeug.contrib.atom import AtomFeed
import dateutil.parser
import mimetypes
import asciicode
import codecs
from itertools import islice
from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options
from flask import Flask, Markup, render_template, send_file, abort
from flask import redirect, url_for, make_response
from flog.source import Source
import flog.config as config
from flog.mime import mimetype

FLOG_CONF = config.file_path()

app = Flask(__name__)
app.config.from_pyfile(FLOG_CONF)

config.apply_defaults(app)

THIS_DIR = app.config.root_path
FLOG_DIR = dirname(FLOG_CONF)
SRC_DIR = join(FLOG_DIR, app.config['SRC_DIR'])
POSTS_PATH = app.config['POSTS_PATH']
ROOT_URL = app.config['ROOT_URL']
SOURCE_URL = os.environ.get('SOURCE_URL') or app.config['SOURCE_URL']
app.config['SOURCE_URL'] = SOURCE_URL
TAG_URI = app.config['TAG_URI']
THEME_PATH = join(FLOG_DIR, app.config['THEME_PATH'])
if not isdir(THEME_PATH):
  THEME_PATH = join(THIS_DIR, 'themes', app.config['THEME_PATH'])
FEED_SIZE = app.config['FEED_SIZE']
FEED_URL = app.config['FEED_URL']
if not FEED_URL:
  FEED_URL = ROOT_URL + '/' + POSTS_PATH + '/feed/'
ASCIIDOC_CONF = join(THIS_DIR, 'asciidoc-html5.conf')
ASCIIDOC_USER_CONF = app.config['ASCIIDOC_CONF']
STYLUS_PATH = app.config['STYLUS_PATH']
PROJECTS_ROOT = app.config['PROJECTS_ROOT']
PROJECTS = app.config['PROJECTS']
DEBUG = __name__ == '__main__' and 'nodebug' not in sys.argv

app.static_folder = join(THEME_PATH, 'static')
app.template_folder = THEME_PATH

# Config checks
if not ROOT_URL:
  raise Exception('ROOT_URL not set')
if not SOURCE_URL:
  raise Exception('SOURCE_URL not set')
if not isfile(FLOG_CONF):
  raise Exception('FLOG_CONF not found: ' + FLOG_CONF)
if not isdir(THEME_PATH):
  raise Exception('Theme not found: ' + THEME_PATH)


# Cache
CACHE_DIR = os.environ.get('FLOG_CACHE') or '/tmp/flog-cache'
CACHE_EXPIRE = os.environ.get('FLOG_CACHE_EXPIRE') or 300

CACHE_OPTS = {
    'cache.type': 'dbm',
    'cache.data_dir': CACHE_DIR,
    'cache.expire': CACHE_EXPIRE
    }

CACHE_MANAGER = CacheManager(**parse_cache_config_options(CACHE_OPTS))

SOURCE = Source(cache_manager=CACHE_MANAGER)

def source(path, root=SOURCE_URL, index='index'):
  if index is None:
    return SOURCE.source(root, path)
  return SOURCE.source(root, join(path, index))

def cache():
  return CACHE_MANAGER.cache()


# Helper functions
@mimetype('text/html')
def page(url_path):
  '''Render page from path'''
  @source(url_path)
  def page_impl(src):
    content, meta = parse_page(url_path)
    return render_template('page.html', meta=meta, content=content)
  return page_impl()

def asciicode_or_redirect(url_path, project=None):
  full_url = join(project['source'], url_path)
  index = None
  if url_path == '' or url_path.endswith('/'):
    index = project['index'] or 'README'
  @mimetype('text/html')
  @source(url_path, root=project['source'], index=index)
  def asciicode_impl(src):
    asciidoc_fn = asciicode_asciidoc(project)
    args = dict(inpath=full_url)
    return asciicode.process_string(asciidoc_fn, StringIO(src), asciidoc_args=args).getvalue()
  mime, _ = mimetypes.guess_type(url_path, strict=False)
  if (mime and mime.startswith('text')) or not splitext(url_path)[1]:
    return asciicode_impl()
  return redirect(full_url)

def parse_page(url_path):
  '''Return html content and meta information from src from url_path'''
  content = asciidoc_html(url_path)
  meta = asciidoc_meta(url_path)
  return content, meta

def parse_post(n):
  url_path = join(POSTS_PATH, str(n))
  return parse_page(url_path)

def post_exists(n):
  '''Check if post n exists in filesystem'''
  url_path = join(POSTS_PATH, str(n))
  @source(url_path)
  def post_exists_impl(src):
    return True
  ret = post_exists_impl()
  return ret is True

def post_meta(n):
  '''Return meta information from post n'''
  url_path = join(POSTS_PATH, str(n))
  return asciidoc_meta(url_path)


# Regexps for parsing asciidoc meta information
META_RE = re.compile(r'^:(.+?): (.+)$')
AUTHOR_RE = re.compile(r'^([^\s].+?) <([^\s]+?)>$')
REV_RE = re.compile(r'^(?:(.+?),)? *(.+?): *(.+?)$')

def asciidoc_html(url_path):
  '''Generate html from asciidoc file at url_path/index'''
  @source(url_path)
  def asciidoc_html_impl(src):
    buf = StringIO()
    asciidoc.execute(
        StringIO(src),
        buf,
        **asciidoc_kwargs(attrs={'flog_url_path': url_path})) #, inpath=fpath))
    html = buf.getvalue()
    buf.close()
    out = html
    if type(html) is str:
      out = unicode(html, 'utf-8')
    return Markup(out)
  return asciidoc_html_impl()

def asciidoc_meta(url_path):
  '''Parse meta information from asciidoc file at url_path/index'''
  @source(url_path)
  def asciidoc_meta_impl(src):
    title = None
    meta = {}
    authors = []
    revs = []
    lines = list(islice(enumerate(StringIO(src)), 0, 20))
    for idx, line in lines:
      line = unicode(line[:-1], 'utf-8')
      stripped = line.rstrip()
      meta_match = META_RE.match(stripped)
      author_match = AUTHOR_RE.match(stripped)
      rev_match = REV_RE.match(stripped)
      if line.strip() != '' and title is None:
        if lines[idx + 1][1][:-1] == '=' * len(line):
          title = line
          meta['title'] = title
        else: # No title
          title = True
      elif line.strip() == '' and title != None:
        break
      elif meta_match:
        name = meta_match.group(1).lower()
        value = meta_match.group(2)
        meta[name] = value
      elif author_match:
        author = author_match.group(1)
        email = author_match.group(2)
        url = None
        authors.append({'name':author, 'email':email, 'url':url})
      elif rev_match:
        rev = rev_match.group(1)
        date = rev_match.group(2)
        remark = rev_match.group(3)
        revs.append({'rev':rev, 'date':date, 'remark':remark})
      else:
        continue
    meta['authors'] = authors
    meta['revisions'] = revs
    return meta
  return asciidoc_meta_impl()

@source(join(POSTS_PATH, 'latest'), index=None)
def latest_post_n(src):
  return int(src)

def post_metas(count):
  metas = (
      (n, post_meta(n))
      for n in range(latest_post_n(), 0, -1)
      )
  return islice(metas, 0, count)

def parse_posts(count):
  def get_data(n):
    content, meta = parse_post(n)
    return n, content, meta
  posts = (get_data(n) for n in range(latest_post_n(), 0, -1))
  return islice(posts, 0, count)

def generate_feed():
  '''Generate an atom feed from latests posts'''
  feed = AtomFeed('Recent posts',
      feed_url=FEED_URL,
      url=ROOT_URL,
      subtitle='...')
  for n, meta in post_metas(FEED_SIZE):
    post_url = ROOT_URL + '/' + POSTS_PATH + '/' + str(n) + '/'
    post_id = TAG_URI.format(n=n) if TAG_URI else post_url
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




# AsciiDocAPI
import asciidoc
def asciidoc_kwargs(**args):
  '''Return dict of default asciidoc.execute() keyword args'''
  def latest_post_titles():
    return app.jinja_env.get_or_select_template('latest_post_titles.html')\
        .render(dict(posts=post_metas(FEED_SIZE), config=app.config))
  kwargs = dict(
      conf_files=[ASCIIDOC_CONF],
      backend='html5',
      attrs={
        'flog_latest_post_titles': latest_post_titles(),
        'filter-modules': 'asciicode',
        'pygments': 'pygments'
        }
      )
  for k, v in app.config.items():
    kwargs['attrs']['flog_' + k] = v
  if ASCIIDOC_USER_CONF and ASCIIDOC_USER_CONF.strip():
    conf_path = join(FLOG_DIR, ASCIIDOC_USER_CONF)
    kwargs['conf_files'].append(conf_path)
  for k, v in args.items():
    if k in kwargs and type(kwargs[k]) is list:
      kwargs[k].extend(v)
    elif k in kwargs and type(kwargs[k]) is dict:
      kwargs[k].update(v)
    else:
      kwargs[k] = v
  return kwargs

# FIX
def asciicode_asciidoc(project):
  def execute(infile, outfile, **kwargs):
    if 'attrs' not in kwargs:
      kwargs['attrs'] = {}
    if 'conf_files' not in kwargs:
      kwargs['conf_files'] = []
    kwargs['attrs'].update({
      'pygments': 'pygments',
      'filter-modules': 'asciicode'
      })
    asciidoc.execute(infile, outfile, **kwargs)
  return execute


# Routes
@app.route('/')
@mimetype('text/html')
def root():
  '''Site index'''
  @source('')
  def root_impl(src):
    content, meta = parse_page('')
    return render_template('index.html',
        posts=post_metas(FEED_SIZE),
        content=content,
        meta=meta)
  return root_impl()

@app.route(join('/', POSTS_PATH, '<int:n>'))
def post_redirect(n):
  return redirect(url_for('post', n=n))

@app.route(join('/', POSTS_PATH, '<int:n>') + '/')
@mimetype('text/html')
def post(n):
  '''Blog post'''
  url_path = join(POSTS_PATH, str(n))
  @source(url_path)
  def post_impl(src):
    content, meta = parse_page(url_path)
    prev_meta = None
    next_meta = None
    if n > 1:
      prev_meta = post_meta(n - 1)
    if n < latest_post_n():
      next_meta = post_meta(n + 1)
    return render_template('post.html',
        n=n,
        meta=meta,
        prev_meta=prev_meta,
        next_meta=next_meta,
        content=content)
  return post_impl()

@app.route(join('/', POSTS_PATH) + '/')
@mimetype('text/html')
def posts_index():
  '''Blog post index'''
  @cache()
  def posts_index_impl():
    prev_meta = latest_post_n() - FEED_SIZE
    if prev_meta <= 0:
      prev_meta = None
    return render_template('posts_index.html',
        posts=parse_posts(FEED_SIZE),
        prev_meta=prev_meta)
  return posts_index_impl()

@app.route('/' + PROJECTS_ROOT)
def asciicode_root():
  return redirect(url_for('asciicode_docs', path = '/'))

# FIX
@app.route(normpath(join('/' + PROJECTS_ROOT, '<path:path>')))
def asciicode_docs(path):
  name_matches = [x for x in PROJECTS if path.startswith(x)]
  if not name_matches:
    return abort(404)
  name = max(name_matches, key=len)
  name_slash = name + '/'
  proj = PROJECTS[name]
  if path == name:
    return redirect(url_for('asciicode_docs', path=path + '/'))
  elif path.startswith(name_slash):
    url_path = path[len(name_slash):]
    return asciicode_or_redirect(url_path, project=proj)
  else:
    return abort(404)

@app.route('/favicon.ico')
@app.route('/favicon.ico/')
@mimetype('image/x-icon')
def favicon():
  return abort(404)

@app.route(join('/', POSTS_PATH, 'feed') + '/')
@mimetype('application/atom+xml')
def posts_feed():
  '''Blog posts atom feed'''
  @cache()
  def posts_feed_impl():
    return generate_feed()
  return posts_feed_impl()

@app.route('/<path:path>')
def catchall(path):
  if path.endswith('/'):
    return page(path)
  return redirect(url_for('catchall', path=path + '/'))


@app.context_processor
def inject_template_vars():
  '''Make these vars available to all templates'''
  return dict(len=len)
