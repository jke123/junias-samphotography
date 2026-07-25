/* Année footer dynamique */
const yearEl = document.getElementById('footerYear');
if (yearEl) yearEl.textContent = new Date().getFullYear();

/* Barre de progression navigation */
const navProgress = document.getElementById('navProgress');
document.querySelectorAll('a[href]').forEach(link => {
  const href = link.getAttribute('href');
  if (!href || href.startsWith('#') || href.startsWith('http') ||
      href.startsWith('mailto') || href.startsWith('tel') || href.includes('wa.me')) return;
  link.addEventListener('click', () => { if (navProgress) navProgress.classList.add('loading'); });
});
window.addEventListener('pageshow', () => {
  if (navProgress) {
    navProgress.classList.remove('loading');
    navProgress.classList.add('done');
    setTimeout(() => navProgress.classList.remove('done'), 700);
  }
});

/* Navbar scroll */
const navbar = document.getElementById('navbar');
if (navbar) {
  window.addEventListener('scroll', () => navbar.classList.toggle('scrolled', window.scrollY > 60), { passive: true });
}

/* Bouton retour en haut */
const scrollTopBtn = document.getElementById('scrollTopBtn');
if (scrollTopBtn) {
  window.addEventListener('scroll', () => scrollTopBtn.classList.toggle('visible', window.scrollY > 400), { passive: true });
}

/* Menu mobile */
const navToggle = document.getElementById('navToggle');
const navLinks  = document.getElementById('navLinks');
if (navToggle && navLinks) {
  navToggle.addEventListener('click', () => {
    const open = navLinks.classList.toggle('open');
    const spans = navToggle.querySelectorAll('span');
    spans[0].style.transform = open ? 'rotate(45deg) translate(4px,4px)' : '';
    spans[1].style.opacity   = open ? '0' : '';
    spans[2].style.transform = open ? 'rotate(-45deg) translate(4px,-4px)' : '';
  });
  document.addEventListener('click', (e) => {
    if (!navToggle.contains(e.target) && !navLinks.contains(e.target)) navLinks.classList.remove('open');
  });
}

/* Scroll reveal */
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      setTimeout(() => entry.target.classList.add('visible'), i * 60);
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });
document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

/* Auto dismiss flash */
document.querySelectorAll('.flash').forEach(f => {
  setTimeout(() => {
    f.style.transition = 'opacity 0.4s';
    f.style.opacity = '0';
    setTimeout(() => f.remove(), 400);
  }, 5000);
});
