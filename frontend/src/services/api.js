const API_BASE = '/api/v1';

class CAWNCADEAPI {
  constructor() {
    this.baseUrl = API_BASE;
  }

  async analyze({ input_text, input_type = 'text', max_sources = 8 }) {
    const response = await fetch(`${this.baseUrl}/analysis/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input_text, input_type, max_sources }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async submitFeedback({ request_id, user_rating, user_comment, was_helpful }) {
    const response = await fetch(`${this.baseUrl}/analysis/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ request_id, user_rating, user_comment, was_helpful }),
    });
    return response.json();
  }

  async login(email, password) {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!response.ok) throw new Error('Login failed');
    return response.json();
  }

  async register(email, password, display_name) {
    const response = await fetch(`${this.baseUrl}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, display_name }),
    });
    if (!response.ok) throw new Error('Registration failed');
    return response.json();
  }

  async getAdminSources() {
    const token = localStorage.getItem('cawncade_token');
    const response = await fetch(`${this.baseUrl}/admin/sources`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return response.json();
  }

  healthCheck() {
    return fetch(`${this.baseUrl}/analysis/health`).then((r) => r.json());
  }
}

const api = new CAWNCADEAPI();
export default api;
