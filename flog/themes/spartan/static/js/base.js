jQuery.noConflict();

// Comments toggle
jQuery(function($) {
  $(document.body).click(function(x) {
    $(x.target).parents('article').find('.comments').first().slideToggle();
  });
});

jQuery(function($) {
  var fb_app_id, twit_js;

  // Twitter
  twit_js = document.createElement('script');
  twit_js.id = 'twitter-wjs';
  twit_js.src = '//platform.twitter.com/widgets.js';
  $(document.head).append(twit_js);

  // Facebook
  fb_app_id = $('meta[property="fb:app_id"]').first().attr('content');
  (function(d, s, id) {
    var js, fjs = d.getElementsByTagName(s)[0];
    if (d.getElementById(id)) return;
    js = d.createElement(s); js.id = id;
    js.src = "//connect.facebook.net/en_US/all.js#xfbml=1&amp;appId=" + fb_app_id;
    fjs.parentNode.insertBefore(js, fjs);
  }(document, 'script', 'facebook-jssdk'));

  window.onLoadNewPosts = function(posts) {
    twttr.widgets.load();
    $.each(posts, function(idx, post) {
      FB.XFBML.parse(post);
    });
  };
});
