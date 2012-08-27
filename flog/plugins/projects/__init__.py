import asciicode
import asciidoc
import flask
import flog.route_helpers as helper
import mimetypes
import os
import urlparse
from StringIO import StringIO
from flog.mime import mimetype

TEXT_MIMES = set([
  'application/javascript'
  ])

def asciicode_or_redirect(app, commit, url_path, project=None, name=None):
  full_url = os.path.join(project['source'].format(commit=commit), url_path)
  index = None
  if url_path == '' or url_path.endswith('/'):
    index = project['index']
    full_url = os.path.join(full_url, index)

  @mimetype('text/html')
  @helper.source(app, full_url)
  def asciicode_impl(src):
    paths = []
    try:
      paths = manifest_list(app, project, name, commit)
    except Exception, e:
      print 'projects plugin: no manifest list found:', e
    asciidoc_fn = asciicode_asciidoc(app)
    log = []
    args = dict(inpath=full_url, log_names=['name', 'section'], log=log)
    html = asciicode.process_string(asciidoc_fn, StringIO(src), asciidoc_args=args).getvalue()
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
        prefix=os.path.join('/', project['root'], name),
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
      or not os.path.splitext(url_path)[1]
      or mime in TEXT_MIMES
      or mime in project['text_mimes']):
    return asciicode_impl()
  return flask.redirect(full_url)

def asciicode_asciidoc(app):
  c = app.config
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

def asciicode_docs(app, plug_conf, name, commit, path):
  root = plug_conf['root']
  projects = plug_conf['projects']
  if name not in projects:
    return abort(404)
  proj = projects[name]
  return asciicode_or_redirect(app, commit, path, project=proj, name=name)

def asciicode_docs_index(app, plug_conf, name, commit):
  projects = plug_conf['projects']
  if name not in projects:
    return abort(404)
  proj = projects[name]
  return asciicode_or_redirect(app, commit, '', project=proj, name=name)

def asciicode_docs_prefix(app, plug_conf, name):
  projects = plug_conf['projects']
  if name not in projects:
    return abort(404)
  proj = projects[name]
  return flask.redirect(flask.url_for('asciicode_docs_index', name=name, commit=proj['commit']))

def manifest_list(app, project, name, commit):
  manifest = project['manifest']
  manifest_url = os.path.join(project['source'].format(commit=commit), project['manifest'])
  @helper.source(app, manifest_url)
  def manifest_list_impl(src):
    return src.splitlines()
  return manifest_list_impl()

def init_for_flog(app, plug_conf):
  projects = plug_conf['projects']
  for name, val in projects.items():
    if type(val) in (str, unicode):
      projects[name] = val = dict(source=val)
    val['index'] = val.get('index', 'README')
    val['manifest'] = val.get('manifest', 'doc_manifest')
    val['commit'] = val.get('commit', 'master')
    val['root'] = plug_conf['root']
    val['text_mimes'] = set(plug_conf.get('text_mimes', []))
  app.add_url_rule(
      os.path.join('/' + plug_conf['root'], '<string:name>/'),
      'asciicode_docs_prefix',
      lambda name: asciicode_docs_prefix(app, plug_conf, name))
  app.add_url_rule(
      os.path.join('/' + plug_conf['root'], '<string:name>', '<string:commit>/'),
      'asciicode_docs_index',
      lambda name, commit: asciicode_docs_index(app, plug_conf, name, commit))
  app.add_url_rule(
      os.path.join('/' + plug_conf['root'], '<string:name>', '<string:commit>', '<path:path>'),
      'asciicode_docs',
      lambda name, commit, path: asciicode_docs(app, plug_conf, name, commit, path))
