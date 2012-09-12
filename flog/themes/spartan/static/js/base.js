addEventListener('DOMContentLoaded', function() {
  var $ = Dumpling;
  $.polyfills();

  // Comment toggling
  !function() {
    function toggleComments(container, state) {
      var iframe = null,
          comments = null,
          height = null,
          fbcomments = null;
      iframe = container.querySelector('iframe');
      fbcomments = container.querySelector('.fb-comments');
      comments = container.querySelector('.fb-comments > span');
      if (iframe) {
        height = comments.style.height;
        fbcomments.style.height = '';
        if ((state && state == 'on') || container.style.display == 'none' || height == 0 || height == '0' || height == '0px') {
          container.style.display = '';
          comments.style.height = iframe.style.height;
          comments.style.width = iframe.style.width;
        }
        else {
          comments.style.height = 0;
        }
      }
    }

    $.forEach(
        document.querySelectorAll('article .comments'),
        function(c) {
          c.style.display = 'none';
        });

    document.body.addEventListener('click', function(evt) {
      var article = null,
          container = null,
          comments = null;
      if (evt.target.classList.contains('comments-toggle')) {
        article = $.getAncestorByTagName(evt.target, 'article');
        if (article) {
          container = article.querySelector('.comments');
          toggleComments(container);
        }
      }
    }, false);
  }();

  // Post pagination
  !function() {
    if (!document.querySelector('meta[name="page-id"][content="posts-index"]')) return;
    var container = document.getElementById('flog-content'),
        spinner = container.querySelector('.spinner'),
        body = document.body,
        xhr = new XMLHttpRequest(),
        nav = document.querySelector('.nextprev'),
        note = new Flog.Notifier(document.getElementById('flog-note'));
    if (nav) nav.style.display = 'none';
    function initializePost(p) {
      var comments = p.querySelector('.comments');
      if (comments) {
        comments.style.display = 'none';
      }
      twttr.widgets.load();
      FB.XFBML.parse(p);
    }
    xhr.onreadystatechange = function() {
      var html = null,
          posts = null;
      if (xhr.readyState == 4) {
        try {
          if (xhr.status >= 200 && xhr.status < 300) {
            html = document.createElement('html');
            html.innerHTML = xhr.responseText;
            posts = html.querySelectorAll('.hentry');
            nav = html.querySelector('.nextprev');
            $.forEach(posts, function(p) {
              container.appendChild(p);
              initializePost(p);
            });
          }
          else {
            note.error('Unable to load more posts.');
          }
        }
        finally {
          spinner.classList.remove('active');
        }
      }
    };
    window.addEventListener('scroll', function(evt) {
      var prev = null;
      if (body.scrollTop < body.scrollHeight - 800) return;
      if (spinner.classList.contains('active')) return;
      container.appendChild(spinner);
      spinner.classList.add('active');
      if (nav) {
        prev = nav.querySelector('.prev');
        if (prev) {
          xhr.open('GET', prev.href);
          xhr.send();
        }
      }
    }, false);
  }();


    // Twitter
  !function() {
    var twit_js = document.createElement('script');
    twit_js.id = 'twitter-wjs';
    twit_js.src = '//platform.twitter.com/widgets.js';
    document.head.appendChild(twit_js);
  }();

  // Facebook
  !function() {
    var fb_app_id = $.getMeta('fb:app_id');
    if (!fb_app_id) return;

    // Facebook
    (function(d, s, id) {
      var js, fjs = d.getElementsByTagName(s)[0];
      if (d.getElementById(id)) return;
      js = d.createElement(s); js.id = id;
      js.src = "//connect.facebook.net/en_US/all.js#xfbml=1&amp;appId=" + fb_app_id;
      fjs.parentNode.insertBefore(js, fjs);
    }(document, 'script', 'facebook-jssdk'));
  }();
}, false);
