/**
 * Dolphin Storage Server - Admin Interface JavaScript
 * Modern vanilla JS for interactivity
 */

// ==============================================
// Toast Notifications
// ==============================================

const Toast = {
    container: null,
    
    init() {
        this.container = document.getElementById('toast-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    },
    
    show(message, type = 'success', title = null, duration = 4000) {
        if (!this.container) this.init();
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icons = {
            success: '✅',
            warning: '⚠️',
            danger: '❌',
            info: 'ℹ️'
        };
        
        const titles = {
            success: 'Successo',
            warning: 'Attenzione',
            danger: 'Errore',
            info: 'Info'
        };
        
        toast.innerHTML = `
            <span class="toast-icon">${icons[type] || icons.info}</span>
            <div class="toast-content">
                <div class="toast-title">${title || titles[type] || 'Notifica'}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="Toast.close(this.parentElement)">×</button>
        `;
        
        this.container.appendChild(toast);
        
        // Auto-remove after duration
        setTimeout(() => this.close(toast), duration);
        
        return toast;
    },
    
    close(toast) {
        if (!toast || !toast.parentElement) return;
        toast.classList.add('toast-out');
        setTimeout(() => toast.remove(), 300);
    },
    
    success(message, title = null) {
        return this.show(message, 'success', title);
    },
    
    warning(message, title = null) {
        return this.show(message, 'warning', title);
    },
    
    danger(message, title = null) {
        return this.show(message, 'danger', title);
    },
    
    info(message, title = null) {
        return this.show(message, 'info', title);
    }
};

// Initialize toast on load
document.addEventListener('DOMContentLoaded', () => Toast.init());


// ==============================================
// Loading Overlay
// ==============================================

const Loading = {
    overlay: null,
    
    show() {
        if (this.overlay) return;
        
        this.overlay = document.createElement('div');
        this.overlay.className = 'loading-overlay';
        this.overlay.innerHTML = '<div class="spinner"></div>';
        document.body.appendChild(this.overlay);
    },
    
    hide() {
        if (this.overlay) {
            this.overlay.remove();
            this.overlay = null;
        }
    }
};


// ==============================================
// Confirm Dialog
// ==============================================

function confirmAction(message, onConfirm) {
    if (confirm(message)) {
        onConfirm();
    }
}


// ==============================================
// Format Utilities
// ==============================================

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('it-IT', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function timeAgo(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    const intervals = {
        anno: 31536000,
        mese: 2592000,
        settimana: 604800,
        giorno: 86400,
        ora: 3600,
        minuto: 60
    };
    
    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
        const interval = Math.floor(seconds / secondsInUnit);
        if (interval >= 1) {
            return `${interval} ${unit}${interval > 1 ? (unit === 'mese' ? 'i' : 'i') : ''} fa`;
        }
    }
    
    return 'Adesso';
}


// ==============================================
// API Utilities
// ==============================================

async function apiRequest(url, options = {}) {
    const defaults = {
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    };
    
    const config = { ...defaults, ...options };
    
    try {
        const response = await fetch(url, config);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Errore sconosciuto');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}


// ==============================================
// Mobile Menu
// ==============================================

function initMobileMenu() {
    const toggle = document.getElementById('mobile-menu-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    
    if (!toggle || !sidebar) return;
    
    toggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        if (overlay) overlay.classList.toggle('active');
    });
    
    if (overlay) {
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        });
    }
}

document.addEventListener('DOMContentLoaded', initMobileMenu);


// ==============================================
// Form Helpers
// ==============================================

function serializeForm(form) {
    const formData = new FormData(form);
    const data = {};
    
    for (const [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    return data;
}

function disableFormSubmit(form, button, loadingText = 'Caricamento...') {
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = loadingText;
    
    return () => {
        button.disabled = false;
        button.textContent = originalText;
    };
}


// ==============================================
// Copy to Clipboard
// ==============================================

async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        Toast.success('Copiato negli appunti!');
        return true;
    } catch (error) {
        console.error('Copy failed:', error);
        Toast.danger('Impossibile copiare');
        return false;
    }
}


// ==============================================
// Keyboard Shortcuts
// ==============================================

document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K = Focus search (if exists)
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            e.preventDefault();
            searchInput.focus();
        }
    }
    
    // Escape = Close modals/sidebars
    if (e.key === 'Escape') {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        if (sidebar && sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
            if (overlay) overlay.classList.remove('active');
        }
    }
});
