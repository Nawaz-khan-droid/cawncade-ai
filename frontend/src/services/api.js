const API_BASE = '/api/v1';

class CAWNCADEAPI {
  constructor() {
    this.baseUrl = API_BASE;
  }

  async analyze({ input_text, input_type = 'auto', max_sources = 10 }) {
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

  async analyzeImage({ image_base64 }) {
    const response = await fetch(`${this.baseUrl}/analysis/analyze/image`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_base64 }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Image analysis failed' }));
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

  async healthCheck() {
    const response = await fetch(`${this.baseUrl}/analysis/health`);
    return response.json();
  }

  fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result);
      reader.onerror = (error) => reject(error);
    });
  }
}

const api = new CAWNCADEAPI();
export default api;
