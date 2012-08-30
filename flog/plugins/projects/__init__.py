import asciicode
import asciidoc
import flask
import mimetypes
import os
import urlparse
from StringIO import StringIO
from flog.mime import mimetype

TEXT_MIMES = set([
  'application/javascript'
  ])

class Plugin:
  def __init__(self, app, conf):
    self.app = app
    self.root = conf['root']
    self.text_mimes = set(conf.get('text_mimes', []))
    self.text_mimes.update(TEXT_MIMES)
    self.projects = conf['projects']
    for name, val in self.projects.items():
      if type(val) in (str, unicode):
        projects[name] = val = dict(source=val)
      val['index'] = val.get('index', 'README')
      val['manifest'] = val.get('manifest', 'doc_manifest')
      val['commit'] = val.get('commit', 'master')
      val['text_mimes'] = val.get('text_mimes', [])

  def asciicode_or_redirect(self, commit, url_path, project=None, name=None):
    index = None
    if url_path == '' or url_path.endswith('/'):
      index = project['index']
      url_path = os.path.join(url_path, index)
    full_url = os.path.join(project['source'].format(commit=commit), url_path)

    base_url = '/' + os.path.join(self.root, name, commit)

    paths = []
    try:
      paths = self.manifest_list(project, name, commit)
    except Exception, e:
      print 'projects plugin: no manifest list found:', e

    @mimetype('text/html')
    @self.app.source(full_url)
    def asciicode_impl(src):
      asciidoc_fn = self.asciicode_asciidoc()
      log = []
      args = dict(
          inpath=full_url,
          attrs=dict(flog_source_url_path=os.path.split(
            os.path.join(base_url, url_path))[0].encode('utf-8')),
          log_names=['name', 'section'],
          log=log)
      f = StringIO(src)
      pos = f.tell()
      first = unicode(f.read(3), 'utf-8')
      if u'\ufeff' != first:
        f.seek(pos)
      html = asciicode.process_string(asciidoc_fn, f, asciidoc_args=args).getvalue()
      if type(html) is not unicode:
        html = unicode(html, 'utf-8')
      current_path = url_path
      if url_path == '' or url_path.endswith('/'):
        current_path = os.path.join(url_path, index)
      names = [x[1]['target'] for x in log if x[0] == 'name']
      headings = [x[1] for x in log if x[0] == 'section' and x[1]['level'] > 0]
      github_info = {}
      url_bits = urlparse.urlparse(full_url)
      if url_bits.hostname == 'raw.github.com':
        user, repo = url_bits.path[1:].split('/')[:2]
        github_info = dict(user=user, repo=repo)
      return flask.render_template('project.html',
          prefix=os.path.join('/', self.root, name),
          title=project.get('title', name),
          current_path=current_path,
          content=flask.Markup(html),
          paths=paths,
          headings=headings,
          names=names,
          commit=commit,
          github_info=github_info)

    mime, _ = mimetypes.guess_type(url_path, strict=False)
    if ((mime and mime.startswith('text'))
        or mime in self.text_mimes
        or mime in project['text_mimes']
        or url_path in paths):
      return asciicode_impl()
    return flask.redirect(full_url)

  def asciicode_asciidoc(self):
    c = self.app.config
    def execute(infile, outfile, attrs={}, conf_files=[], **kwargs):
      attrs.update({
        'pygments': 'pygments',
        'filter-modules': 'asciicode'
        })
      kwargs['attrs'] = attrs
      default_conf_files = [c.ASCIIDOC_FLOG_CONF]
      if c.ASCIIDOC_CONF:
        default_conf_files.append(c.ASCIIDOC_CONF)
      default_conf_files.append(os.path.join(os.path.dirname(__file__), 'asciidoc-html5.conf'))
      kwargs['conf_files'] = default_conf_files + conf_files
      asciidoc.execute(infile, outfile, **kwargs)
    return execute

  def asciicode_docs(self, name, commit, path):
    if name not in self.projects:
      return abort(404)
    proj = self.projects[name]
    return self.asciicode_or_redirect(commit, path, project=proj, name=name)

  def asciicode_docs_index(self, name, commit):
    if name not in self.projects:
      return abort(404)
    proj = self.projects[name]
    return self.asciicode_or_redirect(commit, '', project=proj, name=name)

  def asciicode_docs_prefix(self, name):
    if name not in self.projects:
      return abort(404)
    proj = self.projects[name]
    return flask.redirect(flask.url_for('asciicode_docs_index', name=name, commit=proj['commit']))

  def manifest_list(self, project, name, commit):
    manifest = project['manifest']
    manifest_url = os.path.join(project['source'].format(commit=commit), project['manifest'])
    @self.app.source(manifest_url)
    def manifest_list_impl(src):
      return src.splitlines()
    return manifest_list_impl()

def init_for_flog(app, plug_conf):
  plug = Plugin(app, plug_conf)
  app.add_url_rule(
      os.path.join('/' + plug.root, '<string:name>/'),
      'asciicode_docs_prefix',
      lambda name: plug.asciicode_docs_prefix(name))
  app.add_url_rule(
      os.path.join('/' + plug.root, '<string:name>', '<string:commit>/'),
      'asciicode_docs_index',
      lambda name, commit: plug.asciicode_docs_index(name, commit))
  app.add_url_rule(
      os.path.join('/' + plug.root, '<string:name>', '<string:commit>', '<path:path>'),
      'asciicode_docs',
      lambda name, commit, path: plug.asciicode_docs(name, commit, path))
