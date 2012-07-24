import os
from os.path import abspath, dirname, join, isdir, isfile, getmtime, normpath
import sys
import re
from StringIO import StringIO
from asciidocapi import AsciiDocAPI
from werkzeug.contrib.atom import AtomFeed
import dateutil.parser
import itertools
import subprocess
from filecache import filecache
from flask import Flask, Markup, render_template, send_file, abort
from flask import redirect, url_for, make_response
app = Flask(__name__, static_url_path='/never-used')
app.config.from_envvar('FLOG_CONF')

# Config defaults
config_defaults = dict(
    SRC_DIR = '.',
    POSTS_PATH = 'posts',
    PAGES_PATH = '.',
    THEME_PATH = 'spartan',
    FEED_SIZE = 10,
    ASCIIDOC_CONF = None,
    TAG_URI = None,
    ROOT_URL = None,
    STYLUS_PATH = 'stylus')

for key in config_defaults:
  if key not in app.config:
    app.config[key] = config_defaults[key]

THIS_DIR = abspath(dirname(sys.argv[0]))
FLOG_CONF = os.environ.get('FLOG_CONF')
FLOG_DIR = dirname(FLOG_CONF)
SRC_DIR = join(FLOG_DIR, app.config['SRC_DIR'])
POSTS_PATH = app.config['POSTS']
PAGES_PATH = app.config['PAGES']
ROOT_URL = app.config['ROOT_URL']
TAG_URI = app.config['TAG_URI']
THEME_PATH = join(FLOG_DIR, app.config['THEME_PATH'])
if not isdir(THEME_PATH):
  THEME_PATH = join(THIS_DIR, 'themes', app.config['THEME_PATH'])
FEED_SIZE = app.config['FEED_SIZE']
ASCIIDOC_CONF = join(THIS_DIR, 'asciidoc-html5.conf')
ASCIIDOC_USER_CONF = app.config['ASCIIDOC_CONF']
STYLUS_PATH = app.config['STYLUS_PATH']
DEBUG = __name__ == '__main__' and 'nodebug' not in sys.argv

app.static_folder = join(THEME_PATH, 'static')
app.template_folder = THEME_PATH


# Config checks
if not ROOT_URL:
  raise Exception('ROOT_URL not set')
if not isfile(FLOG_CONF):
  raise Exception('FLOG_CONF not found: ' + FLOG_CONF)
if not isdir(THEME_PATH):
  raise Exception('Theme not found: ' + THEME_PATH)


# Cache
def identity(x):
  return x

if DEBUG:
  filecache = identity


# Routes
@app.route('/')
@filecache
def root():
  '''Site index'''
  posts = os.listdir(join(SRC_DIR, POSTS_PATH))
  posts.sort(key=int, reverse=True)
  posts = [(n, post_meta(n)) for n in posts[:FEED_SIZE]]
  content = asciidoc_html(join(SRC_DIR, PAGES_PATH, 'index'), '')
  return render_template('index.html',
      posts=posts,
      content=content)

@app.route(join('/', POSTS_PATH, '<int:n>') + '/')
@filecache
def post(n):
  '''Blog post'''
  print 'post!'
  content, meta = parse_post(n, join('/', POSTS_PATH, str(n)))
  prev_meta = None
  next_meta = None
  if post_exists(n - 1):
    prev_meta = post_meta(n - 1)
  if post_exists(n + 1):
    next_meta = post_meta(n + 1)
  return render_template('post.html',
      n=n,
      meta=meta,
      prev_meta=prev_meta,
      next_meta=next_meta,
      content=content)

@app.route(join('/', POSTS_PATH) + '/')
@filecache
def posts_index():
  '''Blog post index'''
  posts = os.listdir(join(SRC_DIR, POSTS_PATH))
  posts.sort(key=int, reverse=True)
  def get_data(n):
    n = int(n)
    content, meta = parse_post(n, join('/', POSTS_PATH, str(n)))
    return n, content, meta
  posts = [get_data(n) for n in posts[:FEED_SIZE]]
  last, _, _ = posts[-1]
  prev_meta = None
  print 'LAST', last
  if post_exists(last - 1):
    prev_meta = post_meta(last - 1)
  print 'METAAAA', prev_meta
  return render_template('posts_index.html',
      posts=posts,
      n=last,
      prev_meta=prev_meta)


@app.route(normpath(join('/', PAGES_PATH) + '/<path:path>'))
@filecache
def page_or_media(path):
  '''Asciidoc page or other (media) file'''
  fpath = join(SRC_DIR, PAGES_PATH, path)
  if path.endswith('/'):
    return page(fpath, '/' + path[:-1])
  else:
    if isfile(fpath):
      return media(fpath)
    elif isdir(fpath):
      return redirect(url_for('page_or_media', path = path + '/'))
      #return page(fpath)
    else:
      abort(404)

@app.route('/favicon.ico')
@app.route('/favicon.ico/')
def favicon():
  abort(404)

@app.route(join('/', POSTS_PATH, 'feed') + '/')
@filecache
def posts_feed():
  '''Blog posts atom feed'''
  return generate_feed()

@app.route('/css/<path:path>.css')
@filecache
def css(path):
  '''CSS and Stylus files (which are converted to CSS)'''
  fpath = join(THEME_PATH, 'css', path)
  csspath = fpath + '.css'
  stylpath = fpath + '.styl'
  if isfile(stylpath):
    code = subprocess.call([STYLUS_PATH, '-c', stylpath])
    if code != 0:
      return abort(500)
  if isfile(csspath):
    return send_file(csspath)
  else:
    return abort(404)


@app.context_processor
def inject_template_vars():
  '''Make these vars available to all templates'''
  return dict(len=len)


# Helper functions
def media(fpath):
  '''Send file from filesystem'''
  return send_file(fpath)

def page(fpath, abs_url):
  '''Render page at fpath with a base-url of abs_url'''
  fp = join(fpath, 'index')
  if isfile(fp):
    content, meta = parse_page(fp, abs_url)
    return render_template('page.html', meta=meta, content=content)
  else:
    abort(404)

def parse_post(n, abs_url):
  '''Return html content and meta information from post n with base-url of
  abs_url'''
  path = join(SRC_DIR, POSTS_PATH, str(n), 'index')
  return parse_page(path, abs_url)

def parse_page(fpath, abs_url):
  '''Return html content and meta information from page at fpath with base-url
  of abs_url'''
  if isfile(fpath):
    content = asciidoc_html(fpath, abs_url)
    meta = asciidoc_meta(fpath, abs_url)
    return content, meta
  else:
    abort(404)

def post_exists(n):
  '''Check if post n exists in filesystem'''
  fpath = join(SRC_DIR, POSTS_PATH, str(n), 'index')
  return isfile(fpath)

@filecache
def post_meta(n):
  '''Return meta information from post n with base-url of abs_url'''
  abs_url = join('/', POSTS_PATH, str(n))
  fpath = join(SRC_DIR, POSTS_PATH, str(n), 'index')
  return asciidoc_meta(fpath, abs_url)


# Regexps for parsing asciidoc meta information
META_RE = re.compile(r'^:(.+?): (.+)$')
AUTHOR_RE = re.compile(r'^([^\s].+?) <([^\s]+?)>$')
REV_RE = re.compile(r'^(?:(.+?),)? *(.+?): *(.+?)$')

def asciidoc():
  '''Return AsciiDocAPI object configured for flog'''
  ad = AsciiDocAPI()
  ad.options('--no-header-footer')
  ad.attributes['flog-posts-path'] = POSTS_PATH
  ad.attributes['flog-pages-path'] = PAGES_PATH
  ad.attributes['pygments'] = 'pygments'
  ad.attributes['conf-files'] = ASCIIDOC_CONF
  if ASCIIDOC_USER_CONF and ASCIIDOC_USER_CONF.trim() != '':
    ad.attributes['conf-files'] += '|' + ASCIIDOC_USER_CONF.trim()
  return ad

def asciidoc_html(fpath, abs_url):
  '''Generate html from asciidoc file at fpath, with a base-url of abs_url'''
  ad = asciidoc()
  ad.attributes['base-url'] = abs_url
  with open(fpath) as f:
    buf = StringIO()
    ad.execute(f, buf, 'html5')
    html = buf.getvalue()
    buf.close()
    return Markup(unicode(html, 'utf-8'))

def asciidoc_html_from_string(s, abs_url):
  '''Generate html from asciidoc string, with a base-url of abs_url'''
  ad = asciidoc()
  ad.attributes['base-url'] = abs_url
  in_buf = StringIO(s)
  out_buf = StringIO()
  ad.execute(in_buf, out_buf, 'html5')
  html = out_buf.getvalue()
  in_buf.close()
  out_buf.close()
  return Markup(unicode(html, 'utf-8'))

@filecache
def asciidoc_meta(fpath, abs_url):
  '''Parse meta information from asciidoc file at fpath, with a base-url of
  abs_url'''
  title = None
  meta = {}
  authors = []
  revs = []
  with open(fpath) as f:
    for line in f:
      line = line.rstrip()
      meta_match = META_RE.match(line)
      author_match = AUTHOR_RE.match(line)
      rev_match = REV_RE.match(line)
      if line.strip() != '' and title == None:
        title = line
        meta['title'] = title
      elif line.strip() == '' and title != None:
        break
      elif meta_match:
        name = meta_match.group(1).lower()
        if name == 'summary':
          value = asciidoc_html_from_string(meta_match.group(2), abs_url)
        else:
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

def generate_feed():
  '''Generate an atom feed from latests posts'''
  posts = os.listdir(join(SRC_DIR, POSTS_PATH))
  posts.sort(key=int, reverse=True)
  metas = (
      (n, asciidoc_meta(join(SRC_DIR, POSTS_PATH, n, 'index'), join('/', POSTS_PATH, n)))
      for n in posts
      )
  feed = AtomFeed('Recent posts',
      feed_url=ROOT_URL + POSTS_PATH + '/feed/',
      url=ROOT_URL,
      subtitle='...')
  for n, meta in itertools.islice(metas, FEED_SIZE):
    print meta['revisions']
    post_url = ROOT_URL + POSTS_PATH + '/' + n + '/'
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


if __name__ == '__main__':
  app.run(debug=True)
