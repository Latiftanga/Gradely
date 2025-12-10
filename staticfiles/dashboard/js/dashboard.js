/**
 * Dashboard JavaScript
 * Handles theme management and sidebar collapsing functionality
 */

// Theme Management
(function() {
    'use strict';

    const checkbox = document.getElementById('theme-toggle-checkbox');
    const theme = localStorage.getItem('theme');

    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    }

    // Set initial theme
    if (theme) {
        document.documentElement.setAttribute('data-theme', theme);
        if (theme === 'dark' && checkbox) {
            checkbox.checked = true;
        }
    } else {
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (prefersDark) {
            document.documentElement.setAttribute('data-theme', 'dark');
            if (checkbox) {
                checkbox.checked = true;
            }
        }
    }

    // Add event listener for theme toggle
    if (checkbox) {
        checkbox.addEventListener('change', toggleTheme);
    }
})();

// Collapsible Sidebar
(function() {
    'use strict';

    const sidebar = document.getElementById('main-sidebar');
    const container = document.getElementById('main-container');
    const toggleButton = document.getElementById('sidebar-toggle-button');

    if (!sidebar || !container || !toggleButton) {
        return; // Exit if elements don't exist
    }

    const sidebarState = localStorage.getItem('sidebarState');

    const collapseSidebar = () => {
        sidebar.classList.add('is-collapsed');
        container.classList.add('is-collapsed');
        toggleButton.setAttribute('aria-expanded', 'false');
        toggleButton.setAttribute('aria-label', 'Expand sidebar');
        localStorage.setItem('sidebarState', 'collapsed');
    };

    const expandSidebar = () => {
        sidebar.classList.remove('is-collapsed');
        container.classList.remove('is-collapsed');
        toggleButton.setAttribute('aria-expanded', 'true');
        toggleButton.setAttribute('aria-label', 'Collapse sidebar');
        localStorage.setItem('sidebarState', 'expanded');
    };

    // Set initial state from localStorage
    if (sidebarState === 'collapsed') {
        collapseSidebar();
    }

    // Toggle on button click
    toggleButton.addEventListener('click', () => {
        if (sidebar.classList.contains('is-collapsed')) {
            expandSidebar();
        } else {
            collapseSidebar();
        }
    });
})();
