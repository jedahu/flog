import flask
import os
import flog.config

app = flask.Flask(__name__)
c = flog.config.Config(app.config)
app.config = c

@app.route('/<path:path>')
def all(path):
  fpath = os.path.join(c.FLOG_DIR, c.SRC_DIR, path)
  if os.path.isfile(fpath):
    return flask.send_file(fpath, as_attachment=False)
  return flask.abort(404)
