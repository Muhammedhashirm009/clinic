// Browser automation app JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Handle login form submission
    const loginForm = document.getElementById('loginForm');
    const loginBtn = document.getElementById('loginBtn');
    const loginBtnText = document.getElementById('loginBtnText');
    const loginSpinner = document.getElementById('loginSpinner');

    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            // Show loading state
            loginBtn.disabled = true;
            loginBtnText.textContent = 'Logging in...';
            loginSpinner.classList.remove('d-none');
            
            // The form will submit naturally, this is just for UI feedback
        });
    }

    // Handle refresh button
    const refreshBtn = document.getElementById('refreshBtn');
    const refreshBtn2 = document.getElementById('refreshBtn2');
    
    function handleRefresh() {
        const originalText = this.innerHTML;
        this.innerHTML = '<i class="fas fa-sync-alt fa-spin me-2"></i>Refreshing...';
        this.disabled = true;
        
        fetch('/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Reload the page to show updated content
                window.location.reload();
            } else {
                showAlert('error', 'Refresh failed: ' + data.message);
            }
        })
        .catch(error => {
            showAlert('error', 'Network error: ' + error.message);
        })
        .finally(() => {
            this.innerHTML = originalText;
            this.disabled = false;
        });
    }

    if (refreshBtn) {
        refreshBtn.addEventListener('click', handleRefresh);
    }
    
    if (refreshBtn2) {
        refreshBtn2.addEventListener('click', handleRefresh);
    }

    // Handle status button
    const statusBtn = document.getElementById('statusBtn');
    const statusModal = new bootstrap.Modal(document.getElementById('statusModal'));
    
    if (statusBtn) {
        statusBtn.addEventListener('click', function() {
            statusModal.show();
            loadStatus();
        });
    }

    // Load system status
    function loadStatus() {
        const statusContent = document.getElementById('statusContent');
        
        fetch('/status')
        .then(response => response.json())
        .then(data => {
            const statusHtml = `
                <div class="row">
                    <div class="col-12">
                        <h6>Session Status</h6>
                        <ul class="list-unstyled">
                            <li>
                                <i class="fas fa-${data.logged_in ? 'check-circle text-success' : 'times-circle text-danger'} me-2"></i>
                                Logged In: ${data.logged_in ? 'Yes' : 'No'}
                            </li>
                            <li>
                                <i class="fas fa-${data.browser_active ? 'check-circle text-success' : 'times-circle text-danger'} me-2"></i>
                                Browser Active: ${data.browser_active ? 'Yes' : 'No'}
                            </li>
                            <li>
                                <i class="fas fa-${data.session_valid ? 'check-circle text-success' : 'times-circle text-danger'} me-2"></i>
                                Session Valid: ${data.session_valid ? 'Yes' : 'No'}
                            </li>
                        </ul>
                        ${data.website_url ? `<p><strong>Website:</strong> ${data.website_url}</p>` : ''}
                    </div>
                </div>
            `;
            statusContent.innerHTML = statusHtml;
        })
        .catch(error => {
            statusContent.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Error loading status: ${error.message}
                </div>
            `;
        });
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Helper function to show alerts
    function showAlert(type, message) {
        const alertHtml = `
            <div class="alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Insert at the top of the main container
        const container = document.querySelector('.container, .container-fluid');
        if (container) {
            container.insertAdjacentHTML('afterbegin', alertHtml);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                const newAlert = container.querySelector('.alert');
                if (newAlert) {
                    const bsAlert = new bootstrap.Alert(newAlert);
                    bsAlert.close();
                }
            }, 5000);
        }
    }

    // Handle iframe content loading
    const contentFrame = document.getElementById('contentFrame');
    if (contentFrame) {
        contentFrame.onload = function() {
            // Add some styling to make the iframe content more visible
            try {
                const iframeDoc = contentFrame.contentDocument || contentFrame.contentWindow.document;
                if (iframeDoc) {
                    const style = iframeDoc.createElement('style');
                    style.textContent = `
                        body { 
                            background-color: white !important; 
                            color: black !important; 
                        }
                    `;
                    iframeDoc.head.appendChild(style);
                }
            } catch (e) {
                // Cross-origin restrictions may prevent this
                console.log('Cannot modify iframe content due to cross-origin restrictions');
            }
        };
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+R or F5 to refresh
        if ((e.ctrlKey && e.key === 'r') || e.key === 'F5') {
            e.preventDefault();
            if (refreshBtn) {
                refreshBtn.click();
            }
        }
        
        // Ctrl+Shift+S to show status
        if (e.ctrlKey && e.shiftKey && e.key === 'S') {
            e.preventDefault();
            if (statusBtn) {
                statusBtn.click();
            }
        }
    });
});
