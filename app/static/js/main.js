/**
 * MaraGate System — Main JavaScript
 * Shared utilities used across all pages
 */

'use strict';

// ── Sidebar mobile toggle ─────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const sidebar  = document.getElementById('sidebar');
  const toggle   = document.getElementById('sidebarToggle');
  const overlay  = createOverlay();

  if (toggle && sidebar) {
    toggle.addEventListener('click', () => {
      if (window.innerWidth <= 768) {
        sidebar.classList.toggle('mobile-open');
        overlay.classList.toggle('d-none');
      } else {
        sidebar.classList.toggle('collapsed');
        document.getElementById('main-content')?.classList.toggle('expanded');
      }
    });

    overlay.addEventListener('click', () => {
      sidebar.classList.remove('mobile-open');
      overlay.classList.add('d-none');
    });
  }

  // Auto-dismiss alerts after 6 seconds
  document.querySelectorAll('.alert.alert-dismissible').forEach(el => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      bsAlert?.close();
    }, 6000);
  });

  // Activate all Bootstrap tooltips
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    new bootstrap.Tooltip(el);
  });

  // Activate Bootstrap popovers
  document.querySelectorAll('[data-bs-toggle="popover"]').forEach(el => {
    new bootstrap.Popover(el);
  });
});

function createOverlay() {
  let overlay = document.getElementById('sidebarOverlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'sidebarOverlay';
    overlay.style.cssText = [
      'position:fixed', 'inset:0', 'background:rgba(0,0,0,0.4)',
      'z-index:999', 'display:none'
    ].join(';');
    overlay.classList.add('d-none');
    document.body.appendChild(overlay);
  }
  return overlay;
}

// ── Confirm-action helper ─────────────────────────────────────────
window.confirmAction = function(message, formId) {
  if (confirm(message)) {
    document.getElementById(formId)?.submit();
  }
};

// ── Format currency ───────────────────────────────────────────────
window.formatKES = function(amount) {
  return 'KES ' + Number(amount).toLocaleString('en-KE', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  });
};

// ── Live gate density refresh (admin wildlife/vehicles) ───────────
window.refreshGateDensity = async function(mapInstance) {
  try {
    const res  = await fetch('/api/v1/gates/density');
    const data = await res.json();
    return data.gates;
  } catch (e) {
    console.error('Gate density fetch error:', e);
    return [];
  }
};

// ── Chart.js global defaults ──────────────────────────────────────
if (typeof Chart !== 'undefined') {
  Chart.defaults.font.family  = "'Inter', sans-serif";
  Chart.defaults.font.size    = 12;
  Chart.defaults.color        = '#6b7280';
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.legend.labels.padding = 16;

  // Register a custom plugin for empty-state labels
  Chart.register({
    id: 'emptyState',
    afterDraw(chart) {
      const datasets = chart.data.datasets;
      const isEmpty  = datasets.every(ds =>
        ds.data.every(v => v === 0 || v === null || v === undefined)
      );
      if (isEmpty) {
        const { ctx, width, height } = chart;
        ctx.save();
        ctx.textAlign    = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle    = '#9ca3af';
        ctx.font         = '14px Inter, sans-serif';
        ctx.fillText('No data available', width / 2, height / 2);
        ctx.restore();
      }
    }
  });
}

// ── Table row click to detail ─────────────────────────────────────
document.querySelectorAll('tr[data-href]').forEach(row => {
  row.style.cursor = 'pointer';
  row.addEventListener('click', () => {
    window.location.href = row.dataset.href;
  });
});

// ── Search input debounce ─────────────────────────────────────────
function debounce(fn, delay = 400) {
  let timer;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

const searchInput = document.getElementById('liveSearch');
if (searchInput) {
  searchInput.addEventListener('input', debounce(function() {
    const term  = this.value.toLowerCase();
    const rows  = document.querySelectorAll('tbody tr[data-searchable]');
    rows.forEach(row => {
      row.style.display = row.dataset.searchable.toLowerCase().includes(term)
        ? '' : 'none';
    });
  }));
}

// ── Copy-to-clipboard ─────────────────────────────────────────────
window.copyToClipboard = function(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.innerHTML;
    btn.innerHTML = '<i class="bi bi-check2"></i> Copied!';
    btn.classList.add('btn-success');
    setTimeout(() => {
      btn.innerHTML = orig;
      btn.classList.remove('btn-success');
    }, 1800);
  });
};

// ── Print helper ──────────────────────────────────────────────────
window.printSection = function(sectionId) {
  const section = document.getElementById(sectionId);
  if (!section) return;
  const win = window.open('', '_blank');
  win.document.write(`
    <html>
      <head>
        <title>Print</title>
        <link rel="stylesheet"
              href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">
        <style>body{padding:20px;}</style>
      </head>
      <body>${section.innerHTML}</body>
    </html>
  `);
  win.document.close();
  win.focus();
  win.print();
  win.close();
};

// ── File size validator ───────────────────────────────────────────
document.querySelectorAll('input[type="file"]').forEach(input => {
  input.addEventListener('change', function() {
    const maxBytes = 16 * 1024 * 1024; // 16 MB
    for (const file of this.files) {
      if (file.size > maxBytes) {
        alert(`File "${file.name}" is too large (max 16 MB).`);
        this.value = '';
        return;
      }
    }
  });
});

// ── Plate number formatter ────────────────────────────────────────
document.querySelectorAll('input[name="plate_number"]').forEach(input => {
  input.addEventListener('input', function() {
    this.value = this.value.toUpperCase();
  });
});
