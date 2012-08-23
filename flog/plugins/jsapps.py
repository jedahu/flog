import flask
import flog.route_helpers as helper
import os
import urllib2

def js_apps(app, plug_conf, path):
  root = plug_conf['root']
  apps = plug_conf['apps']
  if not path:
    return helper.page(root + '/')
  name_matches = [x for x in apps if path.startswith(x)]
  if not name_matches:
    return abort(404)
  name = max(name_matches, key=len)
  name_slash = name + '/'
  url = apps[name]

  @helper.source(app, url)
  def js_apps_impl(src):
    return src
  if path == name:
    return flask.redirect(flask.url_for('js_apps', path=path + '/'), code=301)
  if path not in (name, name_slash):
    src_url = os.path.join(os.path.split(url)[0], path[len(name_slash):])
    try:
      urllib2.urlopen(src_url)
      return flask.redirect(src_url)
    except urllib2.URLError:
      return js_apps_impl()
  return js_apps_impl()

def init_for_flog(app, plug_conf):
  app.add_url_rule(
      os.path.join('/', plug_conf['root'], '<path:path>'),
      'js_apps',
      lambda path: js_apps(app, plug_conf, path))
