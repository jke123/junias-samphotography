/**
 * Gallery — Lightbox style téléphone natif
 * Swipe avec momentum · Pinch zoom · Double-tap zoom · Clavier
 */
const Gallery = (() => {

  let current  = 0;
  let isOpen   = false;

  // ── Éléments DOM ──
  const lb       = document.getElementById('lb');
  const viewport = document.getElementById('lbViewport');
  const track    = document.getElementById('lbTrack');
  const counter  = document.getElementById('lbCounter');
  const dlBtn    = document.getElementById('lbDl');
  const thumbs   = document.getElementById('lbThumbs');
  const info     = document.getElementById('lbInfo');
  const btnPrev  = document.getElementById('lbPrev');
  const btnNext  = document.getElementById('lbNext');

  if (!lb) return {};   // Sécurité si la page n'a pas de lightbox

  // ── État tactile ──
  const touch = {
    active: false, pinching: false,
    startX: 0, startY: 0,
    curX: 0, lastX: 0, lastT: 0,
    velocity: 0,
    initDist: 0, baseScale: 1,
  };

  // ── État zoom ──
  const zoom = { scale: 1, lastTap: 0 };

  // ────────────────────────────────────────────
  //  API publique
  // ────────────────────────────────────────────

  function open(index) {
    if (!PHOTOS.length) return;
    current = clamp(index, 0, PHOTOS.length - 1);
    isOpen  = true;
    lb.classList.add('open');
    document.body.style.overflow = 'hidden';
    buildThumbs();
    buildSlides();
    updateUI();
  }

  function close() {
    isOpen = false;
    lb.classList.remove('open');
    document.body.style.overflow = '';
    resetZoom(false);
  }

  function navigate(dir) {
    if (PHOTOS.length <= 1) return;
    const next = clamp(current + dir, 0, PHOTOS.length - 1);
    if (next === current) {
      // Début / fin : rebond visuel
      bounceBack();
      return;
    }
    animateSlide(dir, () => {
      current = next;
      buildSlides();
      updateUI();
      resetZoom(false);
    });
  }

  // ────────────────────────────────────────────
  //  Construction des slides (fenêtre de 3)
  // ────────────────────────────────────────────

  function buildSlides() {
    track.innerHTML = '';
    track.style.transition = 'none';
    track.style.transform  = 'translateX(-100%)';

    const n   = PHOTOS.length;
    const ids = n === 1
      ? [0]
      : [(current - 1 + n) % n, current, (current + 1) % n];

    ids.forEach((pi, pos) => {
      const slide = makeSlide(PHOTOS[pi]);
      slide.style.left = `${(pos - (n === 1 ? 0 : 1)) * 100}%`;
      track.appendChild(slide);
    });

    // Forcer le reflow avant de réactiver les transitions
    void track.offsetHeight;
  }

  function makeSlide(photo) {
    const div = document.createElement('div');
    div.className = 'lb-slide';

    const loader = document.createElement('div');
    loader.className = 'lb-loader';
    loader.innerHTML = '<div class="lb-spinner"></div>';

    const img = document.createElement('img');
    img.className  = 'lb-slide-img';
    img.alt        = photo.title || '';
    img.draggable  = false;
    img.onload     = () => { loader.remove(); img.style.opacity = '1'; };
    img.onerror    = () => loader.remove();
    img.style.opacity = '0';
    img.src        = photo.src;

    div.appendChild(loader);
    div.appendChild(img);
    return div;
  }

  // ────────────────────────────────────────────
  //  Animations
  // ────────────────────────────────────────────

  function animateSlide(dir, onDone) {
    track.style.transition = 'transform 0.32s cubic-bezier(0.25,0.46,0.45,0.94)';
    track.style.transform  = `translateX(${dir > 0 ? '-200%' : '0%'})`;
    track.addEventListener('transitionend', onDone, { once: true });
  }

  function bounceBack() {
    const dir   = current === 0 ? 1 : -1;
    const over  = dir > 0 ? '-110%' : '-90%';
    track.style.transition = 'transform 0.15s ease-out';
    track.style.transform  = `translateX(${over})`;
    setTimeout(() => {
      track.style.transition = 'transform 0.2s ease-in-out';
      track.style.transform  = 'translateX(-100%)';
    }, 150);
  }

  // ────────────────────────────────────────────
  //  UI
  // ────────────────────────────────────────────

  function updateUI() {
    counter.textContent = `${current + 1} / ${PHOTOS.length}`;
    dlBtn.href          = PHOTOS[current].src;

    const p = PHOTOS[current];
    info.style.display  = (p.title || p.desc) ? 'block' : 'none';
    info.innerHTML      = p.title
      ? `<p class="lb-info-title">${p.title}</p>${p.desc ? `<p class="lb-info-desc">${p.desc}</p>` : ''}`
      : '';

    btnPrev.style.display = PHOTOS.length > 1 ? 'flex' : 'none';
    btnNext.style.display = PHOTOS.length > 1 ? 'flex' : 'none';

    // Active thumbnail
    document.querySelectorAll('.lb-thumb').forEach((t, i) => {
      t.classList.toggle('active', i === current);
    });
    const act = document.querySelector('.lb-thumb.active');
    if (act) act.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
  }

  function buildThumbs() {
    thumbs.innerHTML = '';
    PHOTOS.forEach((p, i) => {
      const div = document.createElement('div');
      div.className = 'lb-thumb';
      div.onclick   = () => jumpTo(i);
      const img     = document.createElement('img');
      img.src       = p.src;
      img.loading   = 'lazy';
      img.alt       = p.title || '';
      div.appendChild(img);
      thumbs.appendChild(div);
    });
  }

  function jumpTo(index) {
    if (index === current) return;
    current = clamp(index, 0, PHOTOS.length - 1);
    buildSlides();
    updateUI();
    resetZoom(false);
  }

  // ────────────────────────────────────────────
  //  Zoom
  // ────────────────────────────────────────────

  function getCurrentImg() {
    const slides = track.querySelectorAll('.lb-slide');
    const mid    = PHOTOS.length === 1 ? 0 : 1;
    return slides[mid]?.querySelector('img') || null;
  }

  function applyZoom(scale, animate) {
    zoom.scale   = clamp(scale, 1, 4);
    const img    = getCurrentImg();
    if (!img) return;
    img.style.transition = animate ? 'transform 0.3s ease' : 'none';
    img.style.transform  = zoom.scale === 1 ? 'scale(1)' : `scale(${zoom.scale})`;
  }

  function resetZoom(animate) {
    zoom.scale = 1;
    const img  = getCurrentImg();
    if (!img) return;
    img.style.transition = animate ? 'transform 0.3s ease' : 'none';
    img.style.transform  = 'scale(1)';
  }

  function onDoubleTap(t) {
    if (zoom.scale > 1) {
      resetZoom(true);
    } else {
      applyZoom(2.5, true);
    }
  }

  // ────────────────────────────────────────────
  //  Événements tactiles
  // ────────────────────────────────────────────

  function getPinchDist(e) {
    return Math.hypot(
      e.touches[1].clientX - e.touches[0].clientX,
      e.touches[1].clientY - e.touches[0].clientY
    );
  }

  viewport.addEventListener('touchstart', (e) => {
    if (e.touches.length === 2) {
      touch.pinching  = true;
      touch.active    = false;
      touch.initDist  = getPinchDist(e);
      touch.baseScale = zoom.scale;
      return;
    }
    // Double-tap
    const now = Date.now();
    if (now - zoom.lastTap < 280 && e.touches.length === 1) {
      e.preventDefault();
      onDoubleTap(e.touches[0]);
      zoom.lastTap = 0;
      return;
    }
    zoom.lastTap = now;

    if (zoom.scale > 1.05) return; // En mode zoom → pas de swipe

    touch.active  = true;
    touch.startX  = e.touches[0].clientX;
    touch.startY  = e.touches[0].clientY;
    touch.curX    = touch.startX;
    touch.lastX   = touch.startX;
    touch.lastT   = now;
    touch.velocity = 0;
    track.style.transition = 'none';
  }, { passive: false });

  viewport.addEventListener('touchmove', (e) => {
    if (touch.pinching && e.touches.length === 2) {
      e.preventDefault();
      const dist     = getPinchDist(e);
      const newScale = touch.baseScale * (dist / touch.initDist);
      applyZoom(newScale, false);
      return;
    }
    if (!touch.active) return;

    const dx = e.touches[0].clientX - touch.startX;
    const dy = e.touches[0].clientY - touch.startY;

    // Si scroll vertical dominant → on laisse défiler
    if (!touch._dirLocked) {
      if (Math.abs(dy) > Math.abs(dx) + 8) {
        touch.active = false;
        track.style.transition = 'transform 0.32s cubic-bezier(0.25,0.46,0.45,0.94)';
        track.style.transform  = 'translateX(-100%)';
        return;
      }
      touch._dirLocked = true;
    }

    e.preventDefault();

    // Vélocité
    const now = Date.now();
    const dt  = now - touch.lastT;
    if (dt > 0) touch.velocity = (e.touches[0].clientX - touch.lastX) / dt;
    touch.lastX = e.touches[0].clientX;
    touch.lastT = now;
    touch.curX  = e.touches[0].clientX;

    const vw  = viewport.offsetWidth;
    let pct   = -100 + (dx / vw * 100);

    // Résistance aux bords
    const atStart = current === 0 && dx > 0;
    const atEnd   = current === PHOTOS.length - 1 && dx < 0;
    if (PHOTOS.length === 1 || atStart || atEnd) {
      pct = -100 + (dx / vw * 100) * 0.2;
    }

    track.style.transform = `translateX(${pct}%)`;
  }, { passive: false });

  viewport.addEventListener('touchend', (e) => {
    touch._dirLocked = false;

    if (touch.pinching) {
      touch.pinching = false;
      if (zoom.scale < 1) resetZoom(true);
      return;
    }
    if (!touch.active) return;
    touch.active = false;

    const dx    = touch.curX - touch.startX;
    const vw    = viewport.offsetWidth;
    const DIST  = vw * 0.22;
    const SPEED = 0.4;

    const goNext = dx < -DIST || touch.velocity < -SPEED;
    const goPrev = dx > DIST  || touch.velocity > SPEED;

    track.style.transition = 'transform 0.32s cubic-bezier(0.25,0.46,0.45,0.94)';

    if (goNext && current < PHOTOS.length - 1) {
      animateSlide(1, () => { current++; buildSlides(); updateUI(); resetZoom(false); });
    } else if (goPrev && current > 0) {
      animateSlide(-1, () => { current--; buildSlides(); updateUI(); resetZoom(false); });
    } else {
      track.style.transform = 'translateX(-100%)';
    }
  }, { passive: true });

  // ────────────────────────────────────────────
  //  Glisser souris (desktop)
  // ────────────────────────────────────────────
  let md = false, mdX = 0, mdCur = 0;

  viewport.addEventListener('mousedown', (e) => {
    if (zoom.scale > 1) return;
    md = true; mdX = e.clientX; mdCur = e.clientX;
    track.style.transition = 'none';
  });
  document.addEventListener('mousemove', (e) => {
    if (!md) return;
    mdCur = e.clientX;
    const dx  = mdCur - mdX;
    const vw  = viewport.offsetWidth;
    let pct   = -100 + (dx / vw * 100);
    const atStart = current === 0 && dx > 0;
    const atEnd   = current === PHOTOS.length - 1 && dx < 0;
    if (atStart || atEnd) pct = -100 + (dx / vw * 100) * 0.15;
    track.style.transform = `translateX(${pct}%)`;
  });
  document.addEventListener('mouseup', () => {
    if (!md) return;
    md = false;
    const dx   = mdCur - mdX;
    const DIST = viewport.offsetWidth * 0.2;
    track.style.transition = 'transform 0.32s cubic-bezier(0.25,0.46,0.45,0.94)';
    if (dx < -DIST && current < PHOTOS.length - 1) {
      animateSlide(1, () => { current++; buildSlides(); updateUI(); resetZoom(false); });
    } else if (dx > DIST && current > 0) {
      animateSlide(-1, () => { current--; buildSlides(); updateUI(); resetZoom(false); });
    } else {
      track.style.transform = 'translateX(-100%)';
    }
  });

  // ────────────────────────────────────────────
  //  Clavier · Boutons · Clôture
  // ────────────────────────────────────────────

  document.getElementById('lbClose').onclick = close;
  btnPrev.onclick = () => navigate(-1);
  btnNext.onclick = () => navigate(1);

  document.addEventListener('keydown', (e) => {
    if (!isOpen) return;
    if (e.key === 'ArrowRight') navigate(1);
    if (e.key === 'ArrowLeft')  navigate(-1);
    if (e.key === 'Escape')     close();
  });

  lb.addEventListener('click', (e) => {
    if (e.target === lb || e.target.id === 'lbViewport') close();
  });

  // ────────────────────────────────────────────
  //  Utils
  // ────────────────────────────────────────────

  function clamp(v, min, max) { return Math.min(Math.max(v, min), max); }

  return { open, close, navigate };

})();
