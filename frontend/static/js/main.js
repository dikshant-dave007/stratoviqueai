/* ── Sidebar toggle ─────────────────────────────────────────────── */
const sidebar  = document.getElementById('sidebar');
const sbToggle = document.getElementById('sbToggle');

if (sbToggle && sidebar) {
  sbToggle.addEventListener('click', function () {
    sidebar.classList.toggle('collapsed');
  });
}

/* ── Load session history into sidebar ──────────────────────────── */
async function loadSidebarHistory() {
  const container = document.getElementById('sbHistory');
  const emptyEl   = document.getElementById('sbEmpty');
  if (!container) return;

  try {
    const res  = await fetch('/api/sessions');
    const data = await res.json();

    if (!data || data.length === 0) {
      if (emptyEl) emptyEl.style.display = 'block';
      return;
    }

    if (emptyEl) emptyEl.style.display = 'none';

    // Get current session from URL if on a result/history page
    const currentPath = window.location.pathname;
    const currentId   = currentPath.includes('/history/')
      ? currentPath.split('/history/')[1]
      : null;

    data.forEach(function (session) {
      const item = document.createElement('a');
      item.href  = '/history/' + session.session_id;
      item.className = 'sb-item' + (session.session_id === currentId ? ' active' : '');

      item.innerHTML = `
        <span class="sb-item-name">${escHtml(session.company_name)}</span>
        <span class="sb-item-meta">${escHtml(session.goals)} · ${escHtml(session.created_at)}</span>
      `;

      container.appendChild(item);
    });

  } catch (e) {
    // Silently ignore — sidebar history is non-critical
  }
}

function escHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

/* ── Result page sidebar active link ────────────────────────────── */
function initResultNav() {
  const links = document.querySelectorAll('.rsp-link');
  if (!links.length) return;

  const observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        links.forEach(l => l.classList.remove('active'));
        const id = '#' + entry.target.id;
        const active = document.querySelector('.rsp-link[href="' + id + '"]');
        if (active) active.classList.add('active');
      }
    });
  }, { threshold: 0.2 });

  document.querySelectorAll('#full-report, #agent-outputs').forEach(function (el) {
    observer.observe(el);
  });
}

/* ── Auto-open first accordion on result page ───────────────────── */
function initAccordions() {
  const first = document.querySelector('.aa-item');
  if (first) first.open = true;
}

/* ── Run on load ────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
  loadSidebarHistory();
  initResultNav();
  initAccordions();
});
