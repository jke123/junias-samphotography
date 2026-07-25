const sidebar       = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebarClose  = document.getElementById('sidebarClose');
const modalOverlay  = document.getElementById('modalOverlay');

if (sidebarToggle) sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
if (sidebarClose)  sidebarClose.addEventListener('click', () => sidebar.classList.remove('open'));

function closeModal() {
  document.querySelectorAll('.modal.open').forEach(m => m.classList.remove('open'));
  if (modalOverlay) modalOverlay.classList.remove('open');
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

document.querySelectorAll('.admin-flash').forEach(f => {
  setTimeout(() => {
    f.style.transition = 'opacity 0.4s';
    f.style.opacity = '0';
    setTimeout(() => f.remove(), 400);
  }, 6000);
});
