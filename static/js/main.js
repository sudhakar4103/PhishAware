/*
 * PhishAware Platform JavaScript
 * Version: 1.0.0
 * Date: February 12, 2026
 */

// Utility Functions

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show m-3`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container-fluid') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

/**
 * Format time duration in seconds to MM:SS format
 */
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Parse query parameters from URL
 */
function getQueryParams() {
    const params = {};
    const queryString = window.location.search.substring(1);
    const regex = /([^=&]+)=([^&]*)/g;
    let m;
    
    while ((m = regex.exec(queryString)) !== null) {
        params[decodeURIComponent(m[1])] = decodeURIComponent(m[2]);
    }
    
    return params;
}

/**
 * Export table to CSV
 */
function exportTableToCSV(tableId, filename) {
    const csv = [];
    const table = document.getElementById(tableId);
    
    // Get headers
    const headers = table.querySelectorAll('th');
    const headerRow = Array.from(headers).map(h => {
        const text = h.textContent.trim();
        return `"${text.replace(/"/g, '""')}"`;
    }).join(',');
    csv.push(headerRow);
    
    // Get rows
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        const rowData = Array.from(cells).map(cell => {
            const text = cell.textContent.trim();
            return `"${text.replace(/"/g, '""')}"`;
        }).join(',');
        csv.push(rowData);
    });
    
    // Create and download file
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename || 'export.csv');
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * Confirm action before proceeding
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

/**
 * API call wrapper with error handling
 */
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showToast(`Error: ${error.message}`, 'danger');
        return null;
    }
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString('en-US', options);
}

/**
 * Initialize datatable if available
 */
function initializeDataTables() {
    if (typeof $ !== 'undefined' && $.fn.dataTable) {
        $('table').DataTable({
            responsive: true,
            pageLength: 10,
            dom: 'Bfrtip',
            buttons: ['csv', 'excel', 'print']
        });
    }
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Parse email list from textarea
 */
function parseEmailList(textContent) {
    return textContent
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0 && isValidEmail(line));
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});
