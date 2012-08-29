jQuery.noConflict();

function meta_val(name) {
  return jQuery('meta[name="' + name + '"]').attr('content');
}

jQuery(function($) {
  var form = $('#flog-commit');
  form.css('display', '');
  form.live('submit', function() {
    var commit = $('#flog-commit .ui-combobox-input').val(),
        prefix = meta_val('prefix'),
        current_path = meta_val('current_path');
    window.location = prefix + '/' + commit + '/' + current_path;
  });
});

jQuery(function( $ ) {
  $.widget( "ui.combobox", {
    _create: function() {
      var input,
        self = this,
        select = this.element.hide(),
        selected = select.children( ":selected" ),
        value = selected.val() ? selected.text() : "",
        wrapper = this.wrapper = $( "<span>" )
          .addClass( "ui-combobox" )
          .insertAfter( select );

      input = $( "<input>" )
        .appendTo( wrapper )
        .val( value )
        .addClass( "ui-state-default ui-combobox-input" )
        .autocomplete({
          delay: 0,
          minLength: 0,
          source: function( request, response ) {
            var matcher = new RegExp( $.ui.autocomplete.escapeRegex(request.term), "i" );
            response( select.children( "option" ).map(function() {
              var text = $( this ).text();
              if ( this.value && ( !request.term || matcher.test(text) ) )
                return {
                  label: text.replace(
                    new RegExp(
                      "(?![^&;]+;)(?!<[^<>]*)(" +
                      $.ui.autocomplete.escapeRegex(request.term) +
                      ")(?![^<>]*>)(?![^&;]+;)", "gi"
                    ), "<strong>$1</strong>" ),
                  value: text,
                  option: this
                };
            }) );
          },
          select: function( event, ui ) {
            ui.item.option.selected = true;
            self._trigger( "selected", event, {
              item: ui.item.option
            });
          },
          change: function( event, ui ) {
            if ( !ui.item ) {
              var matcher = new RegExp( "^" + $.ui.autocomplete.escapeRegex( $(this).val() ) + "$", "i" ),
                valid = false;
              select.children( "option" ).each(function() {
                if ( $( this ).text().match( matcher ) ) {
                  this.selected = valid = true;
                  return false;
                }
              });
            }
          }
        })
        .addClass( "ui-widget ui-widget-content ui-corner-left" );

      input.data( "autocomplete" )._renderItem = function( ul, item ) {
        return $( "<li></li>" )
          .data( "item.autocomplete", item )
          .append( "<a>" + item.label + "</a>" )
          .appendTo( ul );
      };

      $( "<a>" )
        .attr( "tabIndex", -1 )
        .attr( "title", "Show All Items" )
        .appendTo( wrapper )
        .button({
          icons: {
            primary: "ui-icon-triangle-1-s"
          },
          text: false
        })
        .removeClass( "ui-corner-all" )
        .addClass( "ui-corner-right ui-combobox-toggle" )
        .click(function() {
          // close if already visible
          if ( input.autocomplete( "widget" ).is( ":visible" ) ) {
            input.autocomplete( "close" );
            return;
          }

          // work around a bug (likely same cause as #5265)
          $( this ).blur();

          // pass empty string as value to search for, displaying all results
          input.autocomplete( "search", "" );
          input.focus();
        });
    },

    destroy: function() {
      this.wrapper.remove();
      this.element.show();
      $.Widget.prototype.destroy.call( this );
    }
  });
});

jQuery(function($) {
  var github_user = meta_val('github_user')
      github_repo = meta_val('github_repo'),
      form = $('#flog-commit'),
      select = form.find('select'),
      current = select.find('option').val(),
      request_url = 'https://api.github.com/repos/' +
          github_user + '/' + github_repo + '/git/refs?callback=?';
  if (github_user && github_repo && select) {
    $.getJSON(request_url, function(message) {
      $.each(message.data, function(_i, r) {
        var ref = r.ref,
            type = r.object.type === 'tag' ? 'tag' : 'branch',
            name = ref.split('/').slice(-1)[0],
            display = type === 'tag' ? 'tag:' + name : name,
            option = $('<option>');
        if (name !== current) {
          option.attr('value', name);
          option.text(display);
          select.append(option);
        }
      });
    });
    select.combobox();
    form.find('.ui-combobox-input').bind('autocompleteselect', function(_evt, ui) {
      form.find('.ui-combobox-input').val(ui.item.value);
      form.trigger('submit');
    });
    form.css('display', '');
    form.bind('submit', function() {
      var commit = $('#flog-commit .ui-combobox-input').val(),
          prefix = meta_val('prefix'),
          current_path = meta_val('current_path');
      window.location = prefix + '/' + commit + '/' + current_path;
    });
    form.find('.ui-combobox-input').keypress(function(evt) {
      evt.stopPropagation();
    });
  }
});

jQuery(function($) {
  var lblocks = $('.listingblock .content');

  lblocks.each(function(_i, b) {
    $(b).attr('data-height', $(b).css('height'));
  });

  lblocks.dblclick(function() {
    var block = $(this);
    if (block.hasClass('collapsed')) {
      block.animate({height: block.attr('data-height')}, function() {
        block.css('height', '');
        block.removeClass('collapsed');
      });
    }
    else {
      block.animate({height: '1em'}, function() {
        block.css('height', '');
        block.addClass('collapsed');
      });
    }
    rangy.getSelection().removeAllRanges();
  });

  $(document).keypress(function(evt) {
    if (evt.which === 99) {
      if (lblocks.first().hasClass('collapsed')) {
        lblocks.removeClass('collapsed');
      }
      else {
        lblocks.addClass('collapsed');
      }
    }
  });
});
