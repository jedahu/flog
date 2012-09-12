var Jorus = (function(d) {
  var currentResponse = {},
      currentHead     = [];

  function htmlToFragment(html) {
    var tmp      = d.createElement('html'),
        fragment = null;
    tmp.innerHTML = html;
    if (tmp.childNodes.length === 1) {
      return tmp.removeChild(tmp.firstChild);
    }
    else {
      fragment = d.createDocumentFragment();
      while (tmp.firstChild) fragment.appendChild(tmp.firstChild);
      return fragment;
    }
  }

  function getAncestorByTagName(node, tagName) {
    while(node && node.tagName) {
      if (node.tagName.toLowerCase() == tagName.toLowerCase()) {
        return node;
      }
      node = node.parentNode;
    };
    return null;
  }

  function callUninstall(resp) {
    if (typeof resp.uninstall == 'function') {
      resp.uninstall(resp);
    }
  }

  function callInstall(resp) {
    if (typeof resp.install == 'function') {
      resp.install(resp);
    }
  }

  function callFinish(resp) {
    if (typeof resp.finish == 'function') {
      resp.finish(resp);
    }
  }

  function getLocationMap() {
    var l = location;
    return {
      hash:     l.hash,
      host:     l.host,
      hostname: l.hostname,
      href:     l.href,
      origin:   l.origin,
      pathname: l.pathname,
      port:     l.port,
      protocol: l.protocol
    };
  }

  function replaceHead(newNodes) {
    var head = d.head;
    try {
      currentHead.forEach(function(node) {
        head.removeChild(node);
      });
      newNodes.forEach(function(node) {
        head.appendChild(node);
      });
    }
    finally {
      currentHead = newNodes;
    }
  }

  function replaceBody(newBody) {
    d.body = newBody;
  }

  function defaultXhr(url, callback, callfail) {
    var client = new XMLHttpRequest();
    client.onreadystatechange = function() {
      if (this.readyState === 4) {
        if (this.status >= 200 && this.status < 300) {
        callback(this.responseText);
        }
        else {
          callfail(this.status);
        }
      }
    }
    client.open('GET', url);
    client.send();
  }

  function getDocument(xhr, x, callback, callfail) {
    var match = null;
    function normalize(node) {
      var title     = node.querySelector('title'),
          titleText = title ? title.innerText : null;
      return {
        title: titleText,
        html:  node,
        head:  node.querySelector('head'),
        body:  node.querySelector('body')
      };
    }
    if (x instanceof Document) callback(normalize(x.documentElement));
    else if (x instanceof Element) callback(normalize(x));
    else if (x.constructor === String) {
      match = x.match(/\S/);
      if (match && match[0] == '<') callback(normalize(htmlToFragment(x)));
      else (xhr || defaultXhr)(x, function(txt) {
        callback(normalize(htmlToFragment(txt)));
      }, callfail);
    }
  }

  function callHandler(handler, req, opts) {
    console.log('callHandler');
    console.log('caller', arguments.callee.caller);
    var loc  = getLocationMap(),
        resp = null;
    req.locationMap = loc;
    resp = handler(req);
    if (resp.id === currentResponse.id) callFinish(resp);
    else {
      getDocument(
          opts.xhr,
          resp.html,
          function(doc) {
            try {
              resp.doc = doc;
              callUninstall(currentResponse);
              d.title = resp.title || doc.title;
              replaceHead(resp.replaceHead ? doc.head : []);
              if (resp.replaceBody) replaceBody(doc.body);
              callInstall(resp);
              callFinish(resp);
            }
            finally {
              currentResponse = resp;
            }
          },
          resp.xhrfail);
    }
  }

  function clickHandler(handler, opts, evt) {
    var a = getAncestorByTagName(evt.target, 'a'),
        url = a
          && (!opts.aClass || a.classList.contains(opts.aClass))
          && (!opts.aTest || opts.aTest(a))
          && a.href,
        state = null,
        obj   = null;
    console.log('url', url);
    if (url) {
      console.log('.....');
      evt.preventDefault();
      state = a.getAttribute(opts.aStateAttr);
      obj = state ? JSON.parse(state) : null;
      history.pushState(obj, null, url);
      callHandler(handler, {historyState: obj}, opts);
    }
  }

  function start(handler, opts) {
    if (!opts.aStateAttr) opts.aStateAttr = 'data-jorus-state';
    if (opts.immediateDispatch) {
      callHandler(handler, {historyState: history.state}, opts);
    }
    function popstateListener(evt) {
      console.log('popped');
      callHandler(handler, {historyState: evt.state}, opts);
    }
    function clickListener(evt) {
      clickHandler(handler, opts, evt);
    }
    addEventListener('popstate', popstateListener);
    d.documentElement.addEventListener('click', clickListener);
    return function() {
      removeEventListener('popstate', popstateListener);
      d.documentElement.removeEventListener('click', clickListener);
    };
  }

  return {
    start: start
  };

})(document);
