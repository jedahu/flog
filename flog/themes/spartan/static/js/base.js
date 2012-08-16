jQuery.noConflict();

// Comments toggle
jQuery(function($) {
  var comments = $('.comments');
  $('.comments-toggle').click(function() {
    comments.slideToggle();
  });
});

// Twitter
jQuery(function($) {
  var js = document.createElement('script');
  js.id = 'twitter-wjs';
  js.src = '//platform.twitter.com/widgets.js';
  $(document.head).append(js);
});
