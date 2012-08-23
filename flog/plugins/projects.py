import asciicode
import asciidoc
import flask
import flog.route_helpers as helper
import mimetypes
import os
from StringIO import StringIO
from flog.mime import mimetype

def asciicode_or_redirect(app, url_path, project=None):
  if type(project) in (str, unicode):
    project = dict(source=project)
  full_url = os.path.join(project['source'], url_path)
  index = None
  if url_path == '' or url_path.endswith('/'):
    index = project.get('index') or 'README'
    full_url = os.path.join(full_url, index)

  @mimetype('text/html')
  @helper.source(app, full_url)
  def asciicode_impl(src):
    asciidoc_fn = asciicode_asciidoc(project)
    args = dict(inpath=full_url)
    return asciicode.process_string(asciidoc_fn, StringIO(src), asciidoc_args=args).getvalue()

  mime, _ = mimetypes.guess_type(url_path, strict=False)
  if (mime and mime.startswith('text')) or not os.path.splitext(url_path)[1]:
    return asciicode_impl()
  return redirect(full_url)

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
    return asciicode_or_redirect(app, url_path, project=proj)
  else:
    return flask.abort(404)

def init_for_flog(app, plug_conf):
  app.add_url_rule(
      os.path.join('/' + plug_conf['root'], '<path:path>'),
      'asciicode_docs',
      lambda path: asciicode_docs(app, plug_conf, path))
