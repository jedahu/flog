var Flog = new function Flog() {
  this.Notifier = function(elem) {
    this.elem = elem;
  };

  this.Notifier.prototype.error = function(content) {
    var note = this.elem;
    note.className = '';
    note.classList.add('active');
    note.classList.add('error');
    note.innerHTML = content;
    setTimeout(function() { note.classList.remove('active'); }, 3000);
  };
}();
