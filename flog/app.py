'''.
Flog class
==========
Jeremy Hughes <jed@jedatwork.com>
2012-08-28: Initial documentation.

This file defines an extension of +flask.Flask+ with AsciiDoc, post, and page
related methods. It forms the core of Flog’s functionality.
.'''
import asciidoc
import flask
import itertools
import os
import re
import flog.core
from StringIO import StringIO
from flog.mime import mimetype

'''.
.+name:Flog[]+
+flog.app.Flog+ inherits +flask.Flask+ without overriding any of its methods. It
provides extra methods without resorting to unsafe monkey patching and gives
those methods access to instance variables in a cleaner way than as arguments to
standalone functions.
.'''
class Flog(flask.Flask):
  '''.
  .+name:Flog.\_\_init__[] (self, *args, **kwargs) => None+
  For future compatibility the init method simply forwards its arguments to
  `flask.Flask.__init__`.
  .'''
  def __init__(self, *args, **kwargs):
    '''
    Takes the same arguments as flask.Flask.__init__.
    '''
    flask.Flask.__init__(self, *args, **kwargs)

    '''.
    The instance’s +config+ is replaced by one from +flog.config+, which uses
    it as its default parameter.
    .'''
    c = flog.config.Config(self.config)
    self.config = c

    '''.
    Some frequently used configuration constants are made members of this class
    for ease of use. They are:

    .+name:Flog.SOURCE_URL[SOURCE_URL] string+
    The prefix at which raw posts and pages are found.
    .'''
    self.SOURCE_URL = self.config.SOURCE_URL

    '''.
    .+name:Flog.ROOT_URL[ROOT_URL] string+
    The prefix from which transformed posts and pages are served. At this stage
    it must be a HTTP URL with no path. E.g. \http://example.com.
    .'''
    self.ROOT_URL = self.config.ROOT_URL

    '''.
    .+name:Flog.POSTS_PATH[POSTS_PATH] string+
    The path under +SOURCE_URL+ at which raw posts are found. It also designates
    the path under +ROOT_URL+ at which transformed posts are found. The
    corresponding pages path does not exist but can be thought of as being the
    empty string.
    .'''
    self.POSTS_PATH = self.config.POSTS_PATH

    '''.
    .+name:Flog.INDEX_NAME[INDEX_NAME] string+
    A directory’s index file. Defaults to +index+.
    .'''
    self.INDEX_NAME = self.config.INDEX_NAME

    '''.
    Both +static_folder+ and +template_folder+ members are set using the
    +THEME_PATH+ configuration constant.
    .'''
    self.static_folder = os.path.join(c.THEME_PATH, 'static')
    self.template_folder = c.THEME_PATH

    '''.
    Initialization fails if the following configuration constants are not set or
    do not exist on the file system.
    .'''
    if not c.ROOT_URL:
      raise Exception('ROOT_URL not set')
    if not c.SOURCE_URL:
      raise Exception('SOURCE_URL not set')
    if not os.path.isfile(c.FLOG_CONF):
      raise Exception('FLOG_CONF not found: ' + c.FLOG_CONF)
    if not os.path.isdir(c.THEME_PATH):
      raise Exception('Theme not found: ' + c.THEME_PATH)


  '''.
  Decorators
  ----------

  Because Flog is designed to pull content from an external URL almost every
  route requires caching of the external URL response data and the result of any
  transforms applied to that data before including it in a response to a client.
  Three decorator methods simplify that task. They all wrap the functionality of
  the object stored at +self.config.SOURCE+, which is an instance of
  +flog.source.Source+. For more detail than is given below, see the
  link:source.py[+flog.source+ module].

  .+name:Flog.source_index[] (self, url, index=None) => decorator+
  The first decorator method takes a URL string and an optional index string,
  which if present is joined to the end of the URL. The URL is dereferenced, and
  the response is cached and passed to the decorated function as its first
  argument. The return value of the decorated function is also cached. Further
  calls of the function result in the cached value being returned.
  .'''
  def source_index(self, url, index=None):
    '''
    A decorator method. Dereference url or url/index and pass response body to
    decorated function as its first argument. Cache response body and function
    return value.
    '''
    if index is None:
      index = self.config.INDEX_NAME
    return self.config.SOURCE.source(os.path.join(url, index))

  '''.
  .+name:Flog.source[] (self, url) => decorator+
  The second decorator method takes only a URL string and otherwise operates
  identically to the first.
  .'''
  def source(self, url):
    '''
    A decorator method. Dereference url and pass response body to decorated
    function as its first argument. Cache response body and function return
    value.
    '''
    return self.config.SOURCE.source(url)

  '''.
  Both +source*+ methods wrap the decorated function such that the wrapper takes
  one argument less than the decorated function definition does. For example:

  [source,py]
  ------------------------------------------------------------------------------
  @app.source('http://example.com/data')
  def transform(data):
    return funky_transformation(data)

  out = transform()
  ------------------------------------------------------------------------------

  .+name:Flog.cache[] (self) => decorator+
  The last decorator method caches the return value of the decorated function.
  .'''
  def cache(self):
    '''
    A decorator method. Cache decorated function return value.
    '''
    return self.config.SOURCE.cache()


  '''.
  AsciiDoc
  --------
  :AsciiDoc: http://methods.co.nz/asciidoc/[AsciiDoc]
  :AsciiDoc-jedahu: https://github.com/jedahu/asciidoc/

  Flog’s default (currently only) content transformation is of text to HTML by
  way of a {AsciiDoc-jedahu}[variant] of {AsciiDoc}, which presents a single
  function API. It takes an in file, an out file, and a number of keyword
  arguments.

  .+name:Flog.asciidoc_kwargs[] (self, **args) => kwarg-map+
  +asciidoc_kwargs+ creates a map of default keyword args for the AsciiDoc
  function and merges it with the contents of the +args+ map, which are given
  priority. Two kinds of keyword args are treated specially: lists and dicts;
  they are merged with their default counterparts rather than replacing them.
  .'''
  def asciidoc_kwargs(self, **args):
    '''
    Return dict of keyword args for asciidoc.execute(), updating the dict with
    any passed in args.
    '''
    c = self.config
    '''.
    Included in the default map is a HTML list of latest post titles which is
    stored under the +flog_latest_post_titles+ in a map under the +attrs+ key.
    It can be accessed inside AsciiDoc conf files using that name.
    .'''
    def latest_post_titles():
      return self.jinja_env.get_or_select_template('latest_post_titles.html')\
          .render(dict(posts=post_metas(c.FEED_SIZE), config=c))
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

  '''.
  Given a path, there is a method to fetch and transform its URL response body
  to HTML, and a method to fetch and parse its response body for meta data. Both
  use the <<Flog.source_index>> decorator to cache the URL response body and
  their own return value. In both cases the URL is created by joining the
  +<<Flog.SOURCE_URL>>+ constant to the +url_path+ argument.

  .+name:Flog.asciidoc_html[] (self, url_path) => flask.Markup+
  The HTML transform method returns unicode text wrapped in a +flask.Markup+
  object for easy insertion into Jinja templates.
  .'''
  def asciidoc_html(self, url_path):
    '''Generate html from asciidoc file at url_path/index'''
    @self.source_index(os.path.join(self.config.SOURCE_URL, url_path))
    def asciidoc_html_impl(src):
      buf = StringIO()
      asciidoc.execute(
          StringIO(src),
          buf,
          **self.asciidoc_kwargs(attrs={'flog_url_path': url_path})) #, inpath=fpath))
      html = buf.getvalue()
      buf.close()
      out = html
      if type(html) is str:
        out = unicode(html, 'utf-8')
      return flask.Markup(out)
    return asciidoc_html_impl()

  '''.
  The meta-data parsing method requires a few regular expressions.
  .'''
  META_RE = re.compile(r'^:(.+?): (.+)$')
  AUTHOR_RE = re.compile(r'^([^\s].+?) <([^\s]+?)>$')
  REV_RE = re.compile(r'^(?:(.+?),)? *(.+?): *(.+?)$')

  '''.
  .+name:Flog.asciidoc_meta[] (self, url_path) => dict+
  The meta-data parsing method returns a dict with the following keys:

  +title+::
    The document title.
  +authors+::
    A list of authors, each a map containing +name+, +email+, and +url+ keys.
    Any of which may be blank or absent.
  +revisions+::
    A list of revisions, each a map containing +rev+, +date+, and +remark+ keys.
    Any of which may be blank or absent.

  The dict will contain additional keys if the document header contains any
  attribute entries.
  .'''
  def asciidoc_meta(self, url_path):
    '''
    Parse meta information from asciidoc file at url_path/index.
    '''
    @self.source_index(os.path.join(self.config.SOURCE_URL, url_path))
    def asciidoc_meta_impl(src):
      title = None
      meta = {}
      authors = []
      revs = []
      f = StringIO(src)
      for line in f:
        line = unicode(line[:-1], 'utf-8')
        stripped = line.rstrip()
        meta_match = META_RE.match(stripped)
        author_match = AUTHOR_RE.match(stripped)
        rev_match = REV_RE.match(stripped)
        if line.strip() != '' and title is None:
          pos = f.tell()
          next_line = f.readline()
          f.seek(pos)
          if next_line[:-1] == '=' * len(line):
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


  '''.
  Pages and posts
  ---------------

  Flog recognizes two kinds of document: page and post. Pages are identified by
  path, posts by number. Both use AsciiDoc for transformation to HTML and Jinja
  templates for rendering.

  .+name:Flog.page[] (self, url_path) => HTML-string+
  The +page+ method parses the AsciiDoc document at
  +SOURCE_URL/url_path/INDEX_NAME+ and renders the +page.html+ template using
  the +meta+ and +content+ returned from the parsing.
  .'''
  def page(self, url_path):
    '''
    Render HTML page from url_path.
    '''
    @self.source_index(os.path.join(self.SOURCE_URL, url_path))
    @mimetype('text/html')
    def page_impl(src):
      content, meta = self.parse_page(url_path)
      return flask.render_template('page.html', meta=meta, content=content)
    return page_impl()

  '''.
  .+name:Flog.post[] (self, url_path) => HTML-string+
  The +post+ method parses the AsciiDoc document at
  +SOURCE_URL/POSTS_PATH/n/INDEX_NAME+ and renders the +post.html+ template
  using the +meta+ and +content+ returned from the parsing, as well as the post
  number (+n+) and the from previous (+prev_meta+) and next (+next_meta+) posts
  if they exist.
  .'''
  def post(self, n):
    '''
    Render HTML page from post number.
    '''
    c = self.config
    url_path = os.path.join(self.POSTS_PATH, str(n))
    @self.source_index(app, os.path.join(self.SOURCE_URL, url_path))
    @mimetype('text/html')
    def post_impl(src):
      content, meta = self.parse_page(url_path)
      prev_meta = None
      next_meta = None
      if n > 1:
        prev_meta = self.post_meta(n - 1)
      if n < self.latest_post_n():
        next_meta = self.post_meta(n + 1)
      return render_template('post.html',
          n=n,
          meta=meta,
          prev_meta=prev_meta,
          next_meta=next_meta,
          content=content)
    return post_impl()

  '''.
  === Parsing

  +parse_page+ and +parse_post+ return the transformed content and metadata from
  a path or post number and +post_meta+ returns a post’s metadata only.

  .+name:Flog.parse_page[] (self, url_path) => (HTML-string, metadata-dict)+
  .'''
  def parse_page(self, url_path):
    '''
    Return HTML content and meta information of the document at url_path.
    '''
    content = self.asciidoc_html(url_path)
    meta = self.asciidoc_meta(url_path)
    return content, meta

  '''.
  .+name:Flog.parse_post[] (self, n) => (HTML-string, metadata-dict)+
  .'''
  def parse_post(self, n):
    '''
    Return HTML content and meta information of post n.
    '''
    url_path = os.path.join(self.config.POSTS_PATH, str(n))
    return self.parse_page(url_path)

  '''.
  .+name:Flog.post_meta[] (self, n) => metadata-dict+
  .'''
  def post_meta(self, n):
    '''
    Return meta information of post n.
    '''
    url_path = os.path.join(self.config.POSTS_PATH, str(n))
    return self.asciidoc_meta(url_path)

  '''.
  +post_metas+ and +parse_posts+ return an iterable of the last +count+ posts’
  metadata or content and metadata.

  .+name:Flog.post_metas[] (self, count) => iterable of metadata-dicts+
  .'''
  def post_metas(self, count):
    metas = (
        (n, self.post_meta(n))
        for n in range(self.latest_post_n(), 0, -1)
        )
    return itertools.islice(metas, 0, count)

  '''.
  .+name:Flog.parse_posts[] (self, count) => iterable of post data+
  .'''
  def parse_posts(self, count):
    def get_data(n):
      content, meta = self.parse_post(n)
      return n, content, meta
    posts = (get_data(n) for n in range(self.latest_post_n(), 0, -1))
    return itertools.islice(posts, 0, count)

  '''.
  === Latest post

  Because posts are not fetched from a local file-system, the latest post cannot
  be determined by a directory listing. The trade-off is store the index of the
  latest post in a file named +latest+ in the posts directory of the content
  repository. When the file is fetched through the +latest_post_n+ method, the
  index number is cached.

  .+name:Flog.latest_post_n[] (self) => integer+
  .'''
  def latest_post_n(self):
    '''
    Fetch and cache the index of the latest post.
    '''
    c = self.config
    @self.source(os.path.join(c.SOURCE_URL, c.POSTS_PATH, 'latest'))
    def latest_post_n_impl(src):
      return int(src)
    return latest_post_n_impl()

# vim: set bomb:
