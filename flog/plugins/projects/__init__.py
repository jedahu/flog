import asciicode
import asciidoc
import flask
import flog.route_helpers as helper
import mimetypes
import os
from StringIO import StringIO
from flog.mime import mimetype

def asciicode_or_redirect(app, url_path, project=None, name=None):
  full_url = os.path.join(project['source'], url_path)
  index = None
  if url_path == '' or url_path.endswith('/'):
    index = project['index']
    full_url = os.path.join(full_url, index)

  @mimetype('text/html')
  @helper.source(app, full_url)
  def asciicode_impl(src):
    paths = []
    try:
      paths = manifest_list(app, project, name)
    except Exception, e:
      print e
    asciidoc_fn = asciicode_asciidoc(app)
    args = dict(inpath=full_url)
    html = asciicode.process_string(asciidoc_fn, StringIO(src), asciidoc_args=args).getvalue()
    if type(html) is not unicode:
      html = unicode(html, 'utf-8')
    current_path = url_path
    if url_path == '' or url_path.endswith('/'):
      current_path = os.path.join(url_path, index)
    return flask.render_template('project.html',
        source=project['source'],
        title=project.get('title', name),
        current_path=current_path,
        content=flask.Markup(html),
        paths=paths)

  mime, _ = mimetypes.guess_type(url_path, strict=False)
  if (mime and mime.startswith('text')) or not os.path.splitext(url_path)[1]:
    return asciicode_impl()
  return redirect(full_url)

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

def asciicode_docs(app, plug_conf, path):
  root = plug_conf['root']
  projects = plug_conf['projects']
  if not path:
    return helper.page(app, root + '/')
  name_matches = [x for x in projects if path.startswith(x)]
  if not name_matches:
    return flask.abort(404)
  name = max(name_matches, key=len)
  name_slash = name + '/'
  proj = projects[name]
  if path == name:
    return flask.redirect(flask.url_for('asciicode_docs', path=path + '/'), code=301)
  elif path.startswith(name_slash):
    url_path = path[len(name_slash):]
    return asciicode_or_redirect(app, url_path, project=proj, name=name)
  else:
    return flask.abort(404)

def manifest_list(app, project, name):
  manifest = project.get('manifest') or 'doc_manifest'
  manifest_url = os.path.join(project['source'], name, project['manifest'])
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
    val['manifest'] = val.get('manifest', 'DOC_MANIFEST')
  app.add_url_rule(
      os.path.join('/' + plug_conf['root'], '<path:path>'),
      'asciicode_docs',
      lambda path: asciicode_docs(app, plug_conf, path))

