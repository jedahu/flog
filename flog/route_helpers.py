import asciidoc
import flask
import itertools
import os
import re
from StringIO import StringIO
from flog.mime import mimetype

def source_index(app, url, index=None):
  if index is None:
    index = app.config.INDEX_NAME
  return app.config.SOURCE.source(os.path.join(url, index))

def source(app, url):
  return app.config.SOURCE.source(url)

def cache(app):
  return app.config.SOURCE.cache()

def asciidoc_kwargs(app, **args):
  '''Return dict of default asciidoc.execute() keyword args'''
  c = app.config
  def latest_post_titles():
    return app.jinja_env.get_or_select_template('latest_post_titles.html')\
        .render(dict(posts=post_metas(app, c.FEED_SIZE), config=c))
  kwargs = dict(
      conf_files=[c.ASCIIDOC_FLOG_CONF],
      backend='html5',
      attrs={
        'flog_latest_post_titles': latest_post_titles(),
        'pygments': 'pygments'
        }
      )
  for k, v in c.items():
    kwargs['attrs']['flog_' + k] = v
  if c.ASCIIDOC_CONF and c.ASCIIDOC_CONF.strip():
    conf_path = os.path.join(c.FLOG_DIR, c.ASCIIDOC_CONF)
    kwargs['conf_files'].append(conf_path)
  for k, v in args.items():
    if k in kwargs and type(kwargs[k]) is list:
      kwargs[k].extend(v)
    elif k in kwargs and type(kwargs[k]) is dict:
      kwargs[k].update(v)
    else:
      kwargs[k] = v
  return kwargs

@mimetype('text/html')
def page(app, url_path):
  '''Render page from path'''
  @source_index(app, os.path.join(app.config.SOURCE_URL, url_path))
  def page_impl(src):
    content, meta = parse_page(app, url_path)
    return flask.render_template('page.html', meta=meta, content=content)
  return page_impl()

def parse_page(app, url_path):
  '''Return html content and meta information from src from url_path'''
  content = asciidoc_html(app, url_path)
  meta = asciidoc_meta(app, url_path)
  return content, meta

def latest_post_n(app):
  c = app.config
  @source(app, os.path.join(c.SOURCE_URL, c.POSTS_PATH, 'latest'))
  def latest_post_n_impl(src):
    return int(src)
  return latest_post_n_impl()

def parse_post(app, n):
  url_path = os.path.join(app.config.POSTS_PATH, str(n))
  return parse_page(app, url_path)

def post_meta(app, n):
  '''Return meta information from post n'''
  url_path = os.path.join(app.config.POSTS_PATH, str(n))
  return asciidoc_meta(app, url_path)

def post_metas(app, count):
  metas = (
      (n, post_meta(app, n))
      for n in range(latest_post_n(app), 0, -1)
      )
  return itertools.islice(metas, 0, count)

def parse_posts(app, count):
  def get_data(n):
    content, meta = parse_post(app, n)
    return n, content, meta
  posts = (get_data(n) for n in range(latest_post_n(app), 0, -1))
  return itertools.islice(posts, 0, count)


# Regexps for parsing asciidoc meta information
META_RE = re.compile(r'^:(.+?): (.+)$')
AUTHOR_RE = re.compile(r'^([^\s].+?) <([^\s]+?)>$')
REV_RE = re.compile(r'^(?:(.+?),)? *(.+?): *(.+?)$')

def asciidoc_html(app, url_path):
  '''Generate html from asciidoc file at url_path/index'''
  @source_index(app, os.path.join(app.config.SOURCE_URL, url_path))
  def asciidoc_html_impl(src):
    buf = StringIO()
    asciidoc.execute(
        StringIO(src),
        buf,
        **asciidoc_kwargs(app, attrs={'flog_url_path': url_path})) #, inpath=fpath))
    html = buf.getvalue()
    buf.close()
    out = html
    if type(html) is str:
      out = unicode(html, 'utf-8')
    return flask.Markup(out)
  return asciidoc_html_impl()

def asciidoc_meta(app, url_path):
  '''Parse meta information from asciidoc file at url_path/index'''
  @source_index(app, os.path.join(app.config.SOURCE_URL, url_path))
  def asciidoc_meta_impl(src):
    title = None
    meta = {}
    authors = []
    revs = []
    lines = list(itertools.islice(enumerate(StringIO(src)), 0, 20))
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
