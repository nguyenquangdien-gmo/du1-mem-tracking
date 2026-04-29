const API_BASE_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && (window.location.port !== '8000' && window.location.port !== '')
    ? 'http://localhost:8000/api/v1' 
    : (window.location.origin + '/api/v1');

const auth = {
    async login(formData) {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            if (result.success) {
                localStorage.setItem('token', result.data.access_token);
                localStorage.setItem('user', JSON.stringify(result.data.user));
                return { success: true };
            }
            return { success: false, error: result.error };
        } catch (err) {
            console.error('Login error:', err);
            return { success: false, error: { message: 'Lỗi kết nối server' } };
        }
    },

    logout() {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = 'login.html';
    },

    isAuthenticated() {
        return !!localStorage.getItem('token');
    },

    getUser() {
        const user = localStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    }
};

const api = {
    async request(endpoint, method = 'GET', data = null) {
        const token = localStorage.getItem('token');
        const headers = {
            'Authorization': `Bearer ${token}`
        };

        if (data && !(data instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
            data = JSON.stringify(data);
        }

        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method,
                headers,
                body: data
            });

            if (response.status === 401) {
                auth.logout();
                return;
            }

            return await response.json();
        } catch (err) {
            console.error(`API Error (${endpoint}):`, err);
            throw err;
        }
    },

    get(endpoint) { return this.request(endpoint, 'GET'); },
    post(endpoint, data) { return this.request(endpoint, 'POST', data); },
    put(endpoint, data) { return this.request(endpoint, 'PUT', data); },
    patch(endpoint, data) { return this.request(endpoint, 'PATCH', data); },
    delete(endpoint) { return this.request(endpoint, 'DELETE'); }
};
