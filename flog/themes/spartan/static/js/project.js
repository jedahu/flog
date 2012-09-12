addEventListener('DOMContentLoaded', function() {
  var $ = Dumpling,
      note = new Flog.Notifier(document.getElementById('flog-note'));

  function currentPath() {
    var prefix = $.getMeta('prefix'),
        commit = $.getMeta('commit');
    return location.pathname.substr(prefix.length + commit.length + 2);
  }

  // Path truncation
  function truncatePaths() {
    var items = document.querySelectorAll('#flog-manifest .path'),
        paths = document.querySelectorAll('#flog-manifest .path a');
    function truncate(elem) {
      var tpath = elem.getAttribute('data-trunc-path');
      if (tpath) {
        elem.innerText = tpath;
      }
      else {
        JTruncate.truncate(elem, {center: true, width: elem.clientWidth - 72});
        elem.setAttribute('data-trunc-path', elem.innerText);
      }
    }
    $.forEach(paths, function(p) {
      p.setAttribute('data-path', p.innerText);
      truncate(p);
    });
    function enterCallback() {
      var p = this.querySelector('a'),
          path = null;
      if (p) {
        path = p.getAttribute('data-path');
        if (path != p.innerText) {
          p.innerText = path;
          this.classList.add('full');
        }
      }
    }
    function leaveCallback() {
      var p = this.querySelector('a');
      if (p) {
        this.classList.remove('full');
        truncate(p);
      }
    }
    $.forEach(items, function(it) {
      it.addEventListener('mouseover', enterCallback, false);
      it.addEventListener('mouseout', leaveCallback, false);
    });
  };

  truncatePaths();

  // Github commit form
  !function() {
    var github_user = $.getMeta('github_user')
        github_repo = $.getMeta('github_repo'),
        form = document.getElementById('flog-commit'),
        options = form.getElementsByTagName('ul')[0],
        input = form.getElementsByTagName('input')[0],
        current = input.value,
        button = form.getElementsByTagName('button')[0],
        request_url = 'https://api.github.com/repos/' +
            github_user + '/' + github_repo + '/git/refs',
        refs = [],
        xhr = null;
    if (github_user && github_repo && input) {
      xhr = new XMLHttpRequest();
      xhr.onreadystatechange = function() {
        var data = null;
        if (this.readyState == 4) {
          if (this.status >= 200 && this.status < 300) {
            data = JSON.parse(this.responseText);
            data.forEach(function(r) {
              var ref = r.ref,
                  type = r.object.type === 'tag' ? 'tag' : 'branch',
                  name = ref.split('/').slice(-1)[0],
                  display = type === 'tag' ? 'tag:' + name : name,
                  option = document.createElement('li');
              refs.push(name);
              option.setAttribute('data-value', name);
              option.innerText = display;
              options.appendChild(option);
            });
          }
        }
      };
      xhr.open('GET', request_url);
      xhr.send();
      form.style.display = '';
      form.addEventListener('submit', function() {
        var commit = input.value,
            prefix = $.getMeta('prefix'),
            commit_url = 'https://api.github.com/repos/' +
                github_user + '/' + github_repo + '/commits/' + commit;
        xhr.onreadystatechange = function() {
          if (this.readyState == 4) {
            if (this.status >= 200 && this.status < 300) {
              window.location = prefix + '/' + commit + '/' + currentPath();
            }
            else {
              note.error('Ref not found: ' + commit + '.');
            }
          }
        };
        xhr.open('GET', commit_url);
        xhr.send();
      }, false);
      input.addEventListener('keypress', function(evt) {
        evt.stopPropagation();
      }, false);
      options.addEventListener('click', function(evt) {
        var li = evt.target;
        if (li.tagName.toLowerCase() == 'li') {
          input.value = li.getAttribute('data-value');
          form.submit();
        }
      }, false);
      function hideMenu(evt) {
        options.classList.remove('active');
      }
      button.addEventListener('click', function(evt) {
        evt.stopPropagation();
        options.classList.toggle('active');
      }, false);
      document.addEventListener('click', hideMenu, false);
    }
  }();

  // Listing collapse
  !function() {
    var lblocks = document.querySelectorAll('.listingblock .content'),
        msgdiv  = document.createElement('div');
    msgdiv.className = 'listing-collapser';

    $.forEach(lblocks, function(b) {
      b.setAttribute('data-height', getComputedStyle(b).height);
    });

    function collapse(block) {
      block.classList.add('collapsed');
    }
    function expand(block) {
      block.classList.remove('collapsed');
      block.style.height = block.getAttribute('data-height');
    }

    msgdiv.addEventListener('click', function() {
      var block = msgdiv.parentNode;
      if (block.classList.contains('collapsed')) expand(block);
      else collapse(block);
    }, false);

    function enterCallback() {
      var collapsed = this.classList.contains('collapsed'),
          mesg = collapsed ? 'click to expand' : 'click to collapse';
      this.appendChild(msgdiv);
      msgdiv.classList.add('active');
    }
    function leaveCallback() {
      msgdiv.classList.remove('active');
    }

    $.forEach(lblocks, function(b) {
      b.addEventListener('mouseover', enterCallback, false);
      b.addEventListener('mouseout', leaveCallback, false);
    });

    document.addEventListener('keypress', function(evt) {
      if (evt.which == 99) {
        if (lblocks.length > 0 && lblocks[0].classList.contains('collapsed')) {
          $.forEach(lblocks, expand);
        }
        else {
          $.forEach(lblocks, collapse);
        }
      }
    }, false);
  }();

  // In-place update with history
  !function() {
    var path_prefix = $.getMeta('prefix'),
        manifest    = document.getElementById('#flog-manifest'),
        spinner     = new Spinner({
          lines: 7,
          length: 3,
          width: 1,
          radius: 1,
          corners: 0,
          rotate: 0,
          color: '#f00',
          speed: 1,
          trail: 70,
          shadow: false,
          hwaccel: true,
          className: 'spinner',
          zIndex: 2e9,
          top: 'auto',
          left: 12
        });
    function installCallback(resp) {
      JSelect.fill(document.documentElement,
        [['meta[name="current_path"]', function(elem) {
          elem.setAttribute('content', currentPath());
          return elem;
        }],
        ['#flog-manifest .current', function(elem) {
          elem.classList.remove('current');
          return elem;
        }],
        ['#flog-manifest > ul', resp.doc.body.querySelector('#flog-manifest > ul')],
        ['#flog-manifest > ul', function(elem) {
          var nodes = elem.getElementsByTagName('li'),
              node = $.find(nodes, function(n) {
                var a = n.getElementsByTagName('a');
                return a.length == 1 && a[0].pathname == location.pathname;
              });
          if (node) node.classList.add('current');
          return elem;
        }],
        ['#flog-headings', resp.doc.body.querySelector('#flog-headings')],
        ['#flog-names', resp.doc.body.querySelector('#flog-names')],
        ['#flog-content', resp.doc.body.querySelector('#flog-content')]]);
      truncatePaths();
    }
    function uninstallCallback(resp) {
      JSelect.fill(document.documentElement,
          [['meta[name="current_path"]', null],
          ['#flog-headings', function(elem) { elem.innerHTML = ''; return elem; }],
          ['#flog-names', function(elem) { elem.innerHTML = ''; return elem; }],
          ['#flog-content', function(elem) { elem.innerHTML = ''; return elem; }]]);
    }
    function finishCallback(resp) {
      spinner.stop();
    }
    function xhrfailCallback(status) {
      note.error('XHR failed with: ' + status + '.');
      spinner.stop();
      history.back();
    }
    function handler(req) {
      var nodes = document.querySelectorAll('#flog-manifest li a'),
          node = $.find(nodes, function(n) {
            return n.pathname == req.locationMap.pathname;
          });
      if (node) spinner.spin(node.parentNode);
      return {
        id: req.locationMap.href.substr(0, req.locationMap.href.length - req.locationMap.hash.length),
        html: req.locationMap.href,
        title: null,
        install: installCallback,
        uninstall: uninstallCallback,
        finish: finishCallback,
        xhrfail: xhrfailCallback
      };
    }
    Jorus.start(handler, {
      aClass:    false,
      aTest: function(a) {
        var l = location;
        console.log(a.getAttribute('href'));
        return (a.getAttribute('href')[0] != '#'
          && a.host == l.host
          && a.protocol == l.protocol
          && (a.pathname == path_prefix
            || a.pathname.indexOf(path_prefix + '/') === 0));
      }
    });
  }();
});
