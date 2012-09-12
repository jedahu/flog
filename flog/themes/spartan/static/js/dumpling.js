/*
Dumpling
========
Jeremy Hughes <jed@jedatwork.com>
2012-09-08: Documented.
:asciicode-language: js
:asciicode-comments: '/\*', '', '\*\/'

A small Javascript library of polyfills and utilities. It tries not to
duplicate existing browser functionality.
*/
var Dumpling = new function Dumpling() {
  var self = this;

  /*
  Utilities
  ---------

  */
  self.getMeta = function(prop, propAttr) {
    var attr = propAttr || 'property',
        meta = document.querySelector('meta[' + attr + '="' + prop + '"]');
    if (meta) return meta.getAttribute('content');
    return null;
  };

  self.setMeta = function(prop, val, propAttr) {
    var attr = propAttr || 'property',
        meta = document.querySelector('meta[' + attr + '="' + prop + '"]');
    if (!meta) {
      meta = document.createElement('meta');
      meta.setAttribute(attr, prop);
      document.head.appendChild(meta);
    }
    meta.setAttribute('content', val);
  };

  self.getAncestor = function(node, test) {
    while(node) {
      if (test(node)) return node;
      node = node.parentNode;
    };
    return null;
  }

  self.getAncestorByTagName = function(node, tagName) {
    var tagName = tagName.toLowerCase();
    function tagNameTest(elem) {
      return elem.tagName.toLowerCase() == tagName;
    }
    return self.getAncestor(node, tagNameTest);
  };

  self.getAncestorByClass = function(node, className) {
    function classNameTest(elem) {
      return self.containsClass(elem, className);
    }
    return self.getAncestor(node, classNameTest);
  };

  self.forEach = function(coll, fn, scope) {
    for (var i = 0, len = coll.length; i < len; ++i) {
      fn.call(scope || coll, coll[i], i, coll);
    }
  };

  self.map = function(coll, fn, scope) {
    var out = [];
    for (var i = 0, len = this.length; i < len; ++i) {
      out[i] = fn.call(scope || coll, coll[i], i, coll);
    }
    return out;
  }

  self.forEachProp = function(obj, fn, scope) {
    for (var p in obj) {
      if (obj.hasOwnProperty(p)) {
        fn.call(scope || obj, obj[p], p, obj);
      }
    }
  };

  self.mapProps = function(obj, fn, scope) {
    var out = {};
    for (var p in obj) {
      if (obj.hasOwnProperty(p)) {
        out[p] = fn.call(scope || obj, obj[p], p, obj);
      }
    }
    return out;
  };

  self.find = function(coll, pred) {
    var item = null;
    for (var i = 0, len = coll.length; i < len; ++i) {
      item = coll[i];
      if (pred(item)) return item;
    }
    return null;
  };

  /*
  Polyfills
  ---------

  */
  self.polyfill = {};

  self.polyfills = function() {
    for (var p in self.polyfill) {
      if (self.polyfill.hasOwnProperty(p)) {
        self.polyfill[p]();
      }
    }
  };

  self.polyfill.forEach = function() {
    if (!Array.prototype.forEach) {
      Array.prototype.forEach = function(fn, scope) {
        for(var i = 0, len = this.length; i < len; ++i) {
          fn.call(scope || this, this[i], i, this);
        }
      }
    }
  };

  self.polyfill.map = function() {
    if (!Array.prototype.map) {
      Array.prototype.map = function(fn, scope) {
        var out = [];
        for (var i = 0, len = this.length; i < len; ++i) {
          out[i] = fn.call(scope || this, this[i], i, this);
        }
        return out;
      }
    }
  };

  // For IE9
  self.polyfill.classList = function() {
    if (typeof document == 'undefined'
        || 'classList' in document.createElement('a')) {
      return;
    }
    function Error(type, msg) {
      this.name = type;
      this.code = DOMException[type];
      this.message = msg;
    }
    function checkTokenAndGetIndex(classList, token) {
      if (token === '') {
        throw new Error('SYNTAX_ERR', 'An invalid or illegal string was specified');
      }
      if (/\s/.test(token)) {
        throw new Error('INVALID_CHARACTER_ERR', 'String contains and invalid character');
      }
      return Array.prototype.indexOf.call(classList, token);
    }
    function ClassList(elem) {
      var trimmedClasses = elem.className.trim(),
          classes = trimmedClasses ? trimmedClasses.split(/\s+/) : [],
          len = classes.length;
      for (var i = 0; i < len; ++i) this.push(classes[i]);
      this._updateClassName = function() {
        elem.className = this.toString();
      };
    }
    function classListGetter() {
      return new ClassList(this);
    }
    ClassList.prototype = [];
    ClassList.prototype.item = function(i) {
      return this[i] || null;
    };
    ClassList.prototype.contains = function(token) {
      token += '';
      return checkTokenAndGetIndex(this, token) !== -1;
    };
    ClassList.prototype.add = function(token) {
      token += '';
      if (checkTokenAndGetIndex(this, token) === -1) {
        this.push(token);
        this._updateClassName();
      }
    };
    ClassList.prototype.remove = function(token) {
      token += '';
      var index = checkTokenAndGetIndex(this, token);
      if (index !== -1) {
        this.splice(index, 1);
        this._updateClassName();
      }
    };
    ClassList.prototype.toggle = function(token) {
      token += '';
      if (checkTokenAndGetIndex(this, token) === -1) {
        this.add(token);
      }
      else {
        this.remove(token);
      }
    };
    ClassList.prototype.toString = function() {
      return this.join(' ');
    };

    var elemCtor = typeof HTMLElement == 'undefined' ? Element : HTMLElement,
        elemProto = elemCtor.prototype;

    if (Object.defineProperty) {
      var classListProp = {
        get: classListGetter,
        enumerable: true,
        configurable: true
      };
      Object.defineProperty(elemProto, 'classList', classListProp);
    }
    else if (Object.prototype.__defineGetter__) {
      elemProto.__defineGetter__('classList', classListGetter);
    }
  };
};
// vim: set tw=80:
