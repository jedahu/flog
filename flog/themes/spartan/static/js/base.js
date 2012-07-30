jQuery.noConflict();

// Footnote reference numbering
jQuery(function($) {
  var refs = $('a.fnote-ref');
  var notes = $('.footnotes li')
  refs.each(function(idx, ref) {
    var note = document.getElementById(ref.getAttribute('href').slice(1));
    var idx = notes.index(note) + 1;
    ref.textContent = idx;
  });
});

// Footnote display
jQuery(function($) {
  var refs = $('a.fnote-ref');
  var notes = $('.footnotes li')
  refs.css('display', 'inline');
  refs.click(function() {
    var note = $(document.getElementById(this.getAttribute('href').slice(1)));
    if (note.css('display') == 'block') return false;
    notes.fadeOut();
    var entry = $('.hentry,article');
    note.css('top', $(this).offset().top);
        //css('left', entry.offset().left + entry.width() + 30);
    note.fadeIn();
    refs.css('color', 'black');
    $(this).css('color', 'red');
    return false;
  });
  $('body').click(function() {
    notes.fadeOut();
    refs.css('color', 'black');
  });
});
