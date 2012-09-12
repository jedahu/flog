var JTruncate = new function JTruncate() {
  function isNumber(n) {
    return !isNaN(parseFloat(n)) && isFinite(n);
  }

  function findTruncPoint(dimension, max, text, start, end, workerEl, token, fromEnd) {
    var opt1,
        opt2,
        mid,
        dim1,
        dim2;

    function getDim() {
      return workerEl['offset' + (dimension == 'width' ? 'Width' : 'Height')];
    }

    if (fromEnd) {
      opt1 = start === 0 ? '' : text.slice(-start);
      opt2 = text.slice(-end);
    } else {
      opt1 = text.slice(0, start);
      opt2 = text.slice(0, end);
    }

    workerEl.innerHTML = token;
    if (max < getDim()) {
      return 0;
    }

    workerEl.innerHTML = opt2 + token;
    dim2 = getDim();
    workerEl.innerHTML = opt1 + token;
    dim1 = getDim();

    if (dim2 < dim1) {
      return end;
    }

    mid = parseInt((start + end) / 2, 10);
    opt1 = fromEnd ? text.slice(-mid) : text.slice(0, mid);

    workerEl.innerHTML = opt1 + token;
    if (getDim() == max) {
      return mid;
    }

    if (getDim() > max) {
      end = mid - 1;
    } else {
      start = mid + 1;
    }

    return findTruncPoint(dimension, max, text, start, end, workerEl, token, fromEnd);
  }

  this.truncate = function(elem, opts) {
    var prop = null,
        options = (function() {
          var out = opts,
              defaults = {
                width: 'auto',
                token: '…',
                center: false,
                multiline: false
              };
          for (var prop in defaults) {
            if (defaults.hasOwnProperty(prop) && !out[prop]) {
              out[prop] = defaults[prop];
            }
          }
          return out;
        })(),
        fontCSS = (function() {
          var css = {};
          [
            'font-family', 'font-size', 'font-style', 'font-weight',
            'font-variant', 'text-indent', 'text-transform',
            'letter-spacing', 'word-spacing'].forEach(function(prop) {
              css[prop] = getComputedStyle(elem)[prop];
            });
          return css;
        })(),
        elementText = elem.innerText,
        truncateWorker = (function() {
          var worker = document.createElement('span');
          for (var prop in fontCSS) {
            if (fontCSS.hasOwnProperty(prop)) {
              worker.style[prop] = fontCSS[prop];
            }
          }
          worker.innerHTML = elementText;
          document.body.appendChild(worker);
          return worker;
        })(),
        originalWidth = truncateWorker.offsetWidth,
        truncateWidth = isNumber(options.width) ? options.width : elem.clientWidth;
        dimension = 'width',
        truncatedText = null,
        originalDim = null,
        truncateDim = null;

    if(options.multiline) {
      truncateWorker.style.width('' + elem.clientWidth + 'px');
      dimension = 'height';
      originalDim = truncateWorker.offsetHeight;
      truncateDim = elem.offsetHeight + 1;
    }
    else {
      originalDim = originalWidth;
      truncateDim = truncateWidth;
    }

    if (originalDim > truncateDim) {
      truncateWorker.innerText = '';
      if (options.center) {
        truncateDim = truncateDim / 2 + 1;
        truncatedText = elementText.slice(0, findTruncPoint(dimension, truncateDim, elementText, 0, elementText.length, truncateWorker, options.token, false))
                + options.token
                + elementText.slice(-1 * findTruncPoint(dimension, truncateDim, elementText, 0, elementText.length, truncateWorker, '', true));
      } else {
        truncatedText = elementText.slice(0, findTruncPoint(dimension, truncateDim, elementText, 0, elementText.length, truncateWorker, options.token, false)) + options.token;
      }

      elem.innerText = truncatedText;
    }

    document.body.removeChild(truncateWorker);
  };
};
