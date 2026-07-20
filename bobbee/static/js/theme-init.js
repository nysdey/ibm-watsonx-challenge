// Runs before any CSS paints: without this a light-mode user sees a dark flash
// on every load while the rest of the JS is still parsing.
(function(){ try { var t = localStorage.getItem('bobbee_theme');
  if (t) document.documentElement.setAttribute('data-theme', t); } catch(e){} })();
