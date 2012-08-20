import flask

def mimetype(mime):
  def decorate(fn):
    def wrapper(*args, **kwargs):
      ret = fn(*args, **kwargs)
      response = ret
      if not isinstance(ret, flask.Response):
        response = flask.make_response(ret)
      response.mimetype = mime
      return response
    return wrapper
  return decorate
