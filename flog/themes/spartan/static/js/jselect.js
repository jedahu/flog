/*.
jselect.js
==========

Selector templating via a caller-defined selector function.
.*/
var define = typeof define === 'function' ? define : function(x) { window.JSelect = x; };

define(Object.freeze(

{ init: function(doc) {
    this._doc = doc;
    return Object.freeze(this);
  }

  /*.
  Selector functions
  ------------------

  Selector functions take a root node, a query, and return a sequence of
  descendent nodes that match the query. This makes it easy to change the
  selector implementation to whatever system is desired (e.g. XPath).

  .+name:defaultCssSelector[] (rootNode, query) => Array<Node>+
  Two selector functions are provided by JSelect. The first wraps the browser’s
  implementation of `querySelectorAll`.
  .*/
, defaultCssSelector: function(rootNode, query) {
    return rootNode.querySelectorAll(query);
  }

  /*.
  .+name:sizzleSelector[] (rootNode, query) => Array<Node>+
  The second uses http://sizzlejs.com[Sizzle].
  .*/
, sizzleSelector: function(rootNode, query) {
    return Sizzle(query, rootNode);
  }

  /*.
  .+name:getSelector[] (selectorFn|null) => selector+
  If no selector function is provided to <<fill>> and `window.Sizzle` exists,
  <<sizzleSelector>> is used, otherwise <<defaultCssSelector>> is used.
  .*/
, getSelector: function(selectorFn) {
    var selector = selectorFn ||
      (typeof Sizzle !== 'undefined' && this.sizzleSelector) ||
      (this._doc.querySelectorAll && this.defaultCssSelector);
    if (selector) return selector;
    throw new Error(
        'No usable selector function found. Please supply one.');
  }



  /*.
  Replacement values
  ------------------

  Each Node matched by a selector query is either replaced or modified in-place.

  A replacement can be a function or a value (+Node+, +String+, +null+).

  +function (matchedNode) => replacementValue+::
    Will be called with a single argument: the matched Node, and must return a
    value to replace it with. If the returned value is the matched Node, no
    replacement will be made. This is for the cases where it makes more sense
    to modify the matched Node in-place. All other return values are treated as
    follows:

  +Node+::
    Used to replace the matched Node.

  +String+::
    Wrapped in a Text Node and used to replace the matched Node.'

  +null|undefined|false+::
    Results in deletion of the matched Node.
  .*/
, replace: function(rep, matchedNode) {
    var value = typeof rep === 'function' ? rep(matchedNode) : rep;
    if (value !== null && value !== undefined && value !== false) {
      this.replaceNode(matchedNode, this.wrapReplacement(value));
    }
    else {
      this.removeNode(matchedNode);
    }
  }

, wrapReplacement: function(r) {
    return r instanceof Node ? r : this._doc.createTextNode(r);
  }

, replaceNode: function(oldNode, newNode) {
    oldNode.parentNode.replaceChild(newNode, oldNode);
  }

, removeNode: function(node) {
    node.parentNode.removeChild(node);
  }



  /*.
  Entry point
  -----------

  .+name:fill[] (rootNode, queryMap, selectorFn) => undefined+
  The `fill` function takes a root Node, a map from queries to replacements,
  and an optional selector function. `fill` simply iterates through each query
  in the map and applies the replacement to each matching Node. The replacement
  can be either: a value (+Node|String+) which will simply replace the matched
  Node; +null|undefined|false+ which will remove the matched Node; or a
  function which must take the matched Node as its argument and return a single
  replacement value of +Node|String|null|undefined|false+.
  .*/
, fill: function(rootNode, queryMap, selectorFn) {
    var i,
        j,
        query,
        newNode,
        matchedNode,
        matchedNodes,
        replacement,
        select = this.getSelector(selectorFn);
    for (i in queryMap) {
      query = queryMap[i][0];
      replacement = queryMap[i][1];
      matchedNodes = select(rootNode, query);
      for (j = 0; j < matchedNodes.length; ++j) {
        matchedNode = matchedNodes[j];
        this.replace(replacement, matchedNode);
      }
    }
  }

}));
