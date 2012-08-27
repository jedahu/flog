import flask
import os
import urllib2

class Plugin:
  def __init__(self, app, conf):
    self.app = app
    self.root = conf['root']
    self.jsapps = conf['apps']

  def js_apps(self, path):
    if not path:
      return self.app.page(self.root + '/')
    name_matches = [x for x in self.jsapps if path.startswith(x)]
    if not name_matches:
      return abort(404)
    name = max(name_matches, key=len)
    name_slash = name + '/'
    url = self.jsapps[name]

    @self.app.source(url)
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
  plug = Plugin(app, plug_conf)
  app.add_url_rule(
      os.path.join('/', plug.root, '<path:path>'),
      'js_apps',
      lambda path: plug.js_apps(path))
