(function(){
  var main = document.getElementById('main');
  var index = document.getElementById('index');
  var q = document.getElementById('q');
  var sortSel = document.getElementById('sort');
  var count = document.getElementById('count');
  var none = document.getElementById('none');
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var all = Array.prototype.slice.call(document.querySelectorAll('details.cond'));
  var pinned = all.filter(function(c){ return c.classList.contains('pinned'); });
  var cards = all.filter(function(c){ return !c.classList.contains('pinned'); });
  var original = cards.slice();

  // Category order for "Sort by category" comes from the build (categories order)
  var CATS = [];
  try{ CATS = JSON.parse(main.getAttribute('data-cats') || '[]'); }catch(err){}

  function catOf(c){ return c.getAttribute('data-cat') || ''; }
  function nameOf(c){ return c.getAttribute('data-short') || c.querySelector('.cn').textContent.trim(); }
  function colourOf(c){
    var m = (c.getAttribute('style') || '').match(/--c:\s*([^;]+)/);
    return m ? m[1].trim() : '';
  }

  // Jump chips: built once, re-ordered whenever the sort changes
  var chipFor = {};
  all.forEach(function(c){
    var a = document.createElement('a');
    a.href = '#' + c.id;
    a.className = 'chip';
    if(colourOf(c)){ a.setAttribute('style', '--c:' + colourOf(c)); }
    a.innerHTML = '<i></i>';
    a.appendChild(document.createTextNode(nameOf(c)));
    a.addEventListener('click', function(e){
      e.preventDefault();
      c.hidden = false;
      c.open = true;
      c.scrollIntoView({behavior: reduce ? 'auto' : 'smooth', block:'start'});
      try{ history.replaceState(null,'','#'+c.id); }catch(err){}
    });
    chipFor[c.id] = a;
  });

  function sorted(mode){
    var list = original.slice();
    if(mode === 'az'){
      list.sort(function(a,b){ return nameOf(a).localeCompare(nameOf(b)); });
    } else if(mode === 'cat'){
      list.sort(function(a,b){
        var ia = CATS.indexOf(catOf(a)), ib = CATS.indexOf(catOf(b));
        if(ia < 0) ia = 999; if(ib < 0) ib = 999;
        return (ia - ib) || (original.indexOf(a) - original.indexOf(b));
      });
    }
    return list;
  }

  function render(mode){
    Array.prototype.slice.call(document.querySelectorAll('.grp')).forEach(function(g){ g.remove(); });
    pinned.forEach(function(c){ index.appendChild(chipFor[c.id]); });
    var last = null;
    sorted(mode).forEach(function(c){
      if(mode === 'cat' && catOf(c) !== last){
        last = catOf(c);
        var h = document.createElement('h2');
        h.className = 'grp';
        if(colourOf(c)){ h.setAttribute('style', '--c:' + colourOf(c)); }
        h.innerHTML = '<i></i><span></span><small></small>';
        h.querySelector('span').textContent = last;
        main.insertBefore(h, none);
      }
      main.insertBefore(c, none);
      index.appendChild(chipFor[c.id]);
    });
    update();
  }

  function updateGroups(){
    Array.prototype.slice.call(document.querySelectorAll('.grp')).forEach(function(h){
      var n = 0, el = h.nextElementSibling;
      while(el && !el.classList.contains('grp') && el.id !== 'none'){
        if(el.tagName === 'DETAILS' && !el.hidden){ n++; }
        el = el.nextElementSibling;
      }
      h.hidden = (n === 0);
      h.querySelector('small').textContent = n + (n === 1 ? ' factfile' : ' factfiles');
    });
  }

  function update(){
    var term = q.value.trim().toLowerCase();
    var shown = 0;
    cards.forEach(function(c){
      var hay = (c.textContent + ' ' + (c.getAttribute('data-k') || '')).toLowerCase();
      var match = !term || hay.indexOf(term) !== -1;
      c.hidden = !match;
      chipFor[c.id].hidden = !match;
      if(match){ shown++; if(term.length >= 3){ c.open = true; } }
    });
    // Read-first cards are hidden while searching
    pinned.forEach(function(c){ c.hidden = !!term; chipFor[c.id].hidden = !!term; });
    none.style.display = (term && shown === 0) ? 'block' : 'none';
    count.textContent = term ? (shown + ' of ' + cards.length + ' factfiles match') : '';
    updateGroups();
  }

  q.addEventListener('input', update);

  sortSel.addEventListener('change', function(){
    render(sortSel.value);
    try{ localStorage.setItem('factfile-sort', sortSel.value); }catch(err){}
  });

  document.getElementById('openAll').addEventListener('click', function(){
    all.forEach(function(c){ if(!c.hidden) c.open = true; });
  });
  document.getElementById('closeAll').addEventListener('click', function(){
    all.forEach(function(c){ c.open = false; });
  });

  // Restore the last sort choice (falls back to list order if storage is unavailable)
  var saved = 'orig';
  try{ saved = localStorage.getItem('factfile-sort') || 'orig'; }catch(err){}
  if(['orig','cat','az'].indexOf(saved) === -1){ saved = 'orig'; }
  sortSel.value = saved;
  render(saved);

  if(location.hash){
    var t = document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if(t && t.tagName === 'DETAILS'){
      t.open = true;
      setTimeout(function(){ t.scrollIntoView({block:'start'}); }, 50);
    }
  }

  window.addEventListener('beforeprint', function(){ all.forEach(function(c){ c.open = true; }); });
})();
