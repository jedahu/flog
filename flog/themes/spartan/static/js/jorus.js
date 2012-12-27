var define = typeof define === 'function' ? define : function(x) { window.JSelect = x; };

define(Object.freeze(

{ init: function(doc) {
    this.currentResponse = {};
    this.currentHead = [];
    this._doc = doc;
    return Object.freeze(this);
  }

, htmlToFragment: function(html) {
    var tmp      = this._doc.createElement('html'),
        fragment = null;
    tmp.innerHTML = html;
    if (tmp.childNodes.length === 1) {
      return tmp.removeChild(tmp.firstChild);
    }
    else {
      fragment = this._doc.createDocumentFragment();
      while (tmp.firstChild) fragment.appendChild(tmp.firstChild);
      return fragment;
    }
  }

, getAncestorByTagName: function(node, tagName) {
    while(node && node.tagName) {
      if (node.tagName.toLowerCase() == tagName.toLowerCase()) {
        return node;
      }
      node = node.parentNode;
    };
    return null;
  }

, callUninstall: function(resp) {
    if (typeof resp.uninstall == 'function') {
      resp.uninstall(resp);
    }
  }

, callInstall: function(resp) {
    if (typeof resp.install == 'function') {
      resp.install(resp);
    }
  }

, callFinish: function(resp) {
    if (typeof resp.finish == 'function') {
      resp.finish(resp);
    }
  }

, getLocationMap: function() {
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

, replaceHead: function(newNodes) {
    var head = this._doc.head;
    try {
      this.currentHead.forEach(function(node) {
        head.removeChild(node);
      });
      newNodes.forEach(function(node) {
        head.appendChild(node);
      });
    }
    finally {
      this.currentHead = newNodes;
    }
  }

, replaceBody: function(newBody) {
    this._doc.body = newBody;
  }

, defaultXhr: function(url, callback, callfail) {
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

, getDocument: function(xhr, x, callback, callfail) {
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
      if (match && match[0] == '<') callback(normalize(this.htmlToFragment(x)));
      else (xhr || defaultXhr)(x, function(txt) {
        callback(normalize(this.htmlToFragment(txt)));
      }, callfail);
    }
  }

, callHandler: function(handler, req, opts) {
    console.log('callHandler');
    console.log('caller', arguments.callee.caller);
    var self = this
      , loc  = this.getLocationMap()
      , resp = null
      ;
    req.locationMap = loc;
    resp = handler(req);
    if (resp.id === this.currentResponse.id) this.callFinish(resp);
    else {
      getDocument(
          opts.xhr,
          resp.html,
          function(doc) {
            try {
              resp.doc = doc;
              self.callUninstall(self.currentResponse);
              self._doc.title = resp.title || doc.title;
              self.replaceHead(resp.replaceHead ? doc.head : []);
              if (resp.replaceBody) self.replaceBody(doc.body);
              self.callInstall(resp);
              self.callFinish(resp);
            }
            finally {
              self.currentResponse = resp;
            }
          },
          resp.xhrfail);
    }
  }

, clickHandler: function(handler, opts, evt) {
    var a = this.getAncestorByTagName(evt.target, 'a'),
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
      this.callHandler(handler, {historyState: obj}, opts);
    }
  }

, start: function(handler, opts) {
    var self = this;
    if (!opts.aStateAttr) opts.aStateAttr = 'data-jorus-state';
    if (opts.immediateDispatch) {
      this.callHandler(handler, {historyState: history.state}, opts);
    }
    function popstateListener(evt) {
      console.log('popped');
      self.callHandler(handler, {historyState: evt.state}, opts);
    }
    function clickListener(evt) {
      self.clickHandler(handler, opts, evt);
    }
    addEventListener('popstate', popstateListener);
    this._doc.documentElement.addEventListener('click', clickListener);
    return function() {
      removeEventListener('popstate', popstateListener);
      this._doc.documentElement.removeEventListener('click', clickListener);
    };
  }

}));
