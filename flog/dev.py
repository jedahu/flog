import flask
import os
import flog.config as config

app = flask.Flask('src server')
app.config.from_pyfile(config.file_path())
config.apply_defaults(app)

@app.route('/<path:path>')
def all(path):
  fpath = os.path.join(os.path.dirname(config.file_path()), app.config['SRC_DIR'], path)
  if os.path.isfile(fpath):
    return flask.send_file(fpath, as_attachment=False)
  return flask.abort(404)
