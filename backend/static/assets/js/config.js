// API base URL. Override khi deploy.
window.API_BASE = window.API_BASE || (
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && (window.location.port !== '8000' && window.location.port !== '')
    ? "http://localhost:8000/api/v1"
    : (window.location.origin + "/api/v1")
);
