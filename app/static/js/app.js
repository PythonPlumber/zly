/* Zly — global client JS (HTMX CSRF, toasts, clipboard, mobile nav, modal focus trap) */
(function () {
    'use strict';

    // ── CSRF ──
    document.body.addEventListener('htmx:configRequest', function (e) {
        var m = document.cookie.match(/(?:^|;\s*)zly_csrf_token=([^;]*)/);
        if (m) e.detail.headers['X-CSRF-Token'] = decodeURIComponent(m[1]);
    });

    // ── Toast helpers ──
    function showToast(msg, kind) {
        var toast = document.getElementById('zly-toast');
        if (!toast) return;
        var el = document.createElement('div');
        var bg = kind === 'error' ? 'rgba(239,68,68,0.92)' : 'rgba(34,197,94,0.92)';
        var fg = kind === 'error' ? '#f4f0ea' : '#050a07';
        el.style.cssText = 'background:' + bg + ';color:' + fg + ';padding:0.75rem 1.25rem;font-family:Space Grotesk,sans-serif;font-size:0.8rem;font-weight:600;letter-spacing:0.05em;border:1px solid rgba(255,255,255,0.08);animation:slideIn 0.3s ease;max-width:28rem;word-break:break-word;';
        el.textContent = msg;
        toast.appendChild(el);
        setTimeout(function () {
            el.style.opacity = '0';
            el.style.transition = 'opacity 0.3s';
            setTimeout(function () { el.remove(); }, 300);
        }, kind === 'error' ? 5000 : 3000);
    }

    document.body.addEventListener('htmx:responseError', function (e) {
        var msg = 'Request failed';
        try {
            var data = JSON.parse(e.detail.xhr.responseText);
            msg = typeof data.detail === 'string' ? data.detail : (data.detail && data.detail[0] && data.detail[0].msg) || msg;
        } catch (_) {}
        showToast('ERROR: ' + msg, 'error');
    });

    document.body.addEventListener('htmx:afterSwap', function (e) {
        var target = e.detail.target;
        if (!target) return;
        var successEl = target.querySelector ? target.querySelector('[data-toast-success]') : null;
        if (successEl) showToast(successEl.getAttribute('data-toast-success'), 'success');
        // Also check if swapped content itself has the attribute
        if (target.getAttribute && target.getAttribute('data-toast-success')) {
            showToast(target.getAttribute('data-toast-success'), 'success');
        }
    });

    // Success toast via header (for API JSON responses that swap)
    document.body.addEventListener('htmx:afterRequest', function (e) {
        if (e.detail.successful && e.detail.xhr) {
            var toastMsg = e.detail.xhr.getResponseHeader('X-Toast-Success');
            if (toastMsg) showToast(decodeURIComponent(toastMsg), 'success');
        }
    });

    // ── Clipboard ──
    window.copyToClipboard = function (text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(function () {
                showToast('COPIED TO CLIPBOARD', 'success');
            }).catch(function () { fallbackCopy(text); });
        } else {
            fallbackCopy(text);
        }
    };
    function fallbackCopy(text) {
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); showToast('COPIED TO CLIPBOARD', 'success'); } catch (_) { showToast('Copy failed', 'error'); }
        ta.remove();
    }

    // ── Mobile nav ──
    window.toggleMobileNav = function () {
        var sidebar = document.querySelector('.sidebar');
        var overlay = document.getElementById('mobile-overlay');
        if (!sidebar) return;
        var isOpen = sidebar.classList.toggle('open');
        if (overlay) overlay.classList.toggle('open', isOpen);
        document.body.style.overflow = isOpen ? 'hidden' : '';
    };
    // Close on overlay click or link click (mobile)
    document.addEventListener('click', function (e) {
        if (e.target.id === 'mobile-overlay') window.toggleMobileNav();
        if (e.target.closest && e.target.closest('.sidebar-link') && window.innerWidth <= 1024) {
            var sb = document.querySelector('.sidebar');
            if (sb && sb.classList.contains('open')) window.toggleMobileNav();
        }
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            var sb = document.querySelector('.sidebar');
            if (sb && sb.classList.contains('open')) window.toggleMobileNav();
            // Also close modals on Escape
            var modal = document.querySelector('.zly-modal-overlay');
            if (modal) modal.remove();
        }
    });

    // ── Modal focus trap (basic) ──
    document.body.addEventListener('htmx:afterSwap', function (e) {
        var modal = e.detail.target && e.detail.target.querySelector
            ? e.detail.target.querySelector('.zly-modal')
            : null;
        if (!modal && e.detail.target && e.detail.target.classList && e.detail.target.classList.contains('zly-modal')) {
            modal = e.detail.target;
        }
        if (modal) {
            var focusable = modal.querySelector('input, button, select, textarea, a[href]');
            if (focusable) setTimeout(function () { focusable.focus(); }, 50);
        }
    });

    // ── Tab helper (for pages that still use JS tabs) ──
    window.switchTab = function (name) {
        document.querySelectorAll('.tab-panel').forEach(function (p) { p.classList.remove('active-panel'); });
        document.querySelectorAll('.tab-btn').forEach(function (b) { b.classList.remove('active-tab'); });
        var panel = document.getElementById('panel-' + name) || document.getElementById('tab-' + name);
        var btn = document.getElementById('btn-' + name) || document.querySelector('[data-tab="' + name + '"]');
        if (panel) panel.classList.add('active-panel');
        if (btn) btn.classList.add('active-tab');
    };
    window.switchEmailTab = function (name) { window.switchTab(name); };

    // ── Expose ──
    window.zlyToast = showToast;
})();
