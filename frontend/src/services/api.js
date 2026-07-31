// Change this to match the backend prefix exactly
const API_BASE = '/api/v1'; 

class CAWNCADEAPI {
  constructor() {
    // If running on HF, we use relative paths so the browser 
    // automatically prepends the Space's URL.
    this.baseUrl = API_BASE;
  }

  async analyze({ input_text, input_type = 'auto', max_sources = 10 }) {
    // This will call /api/v1/analysis/analyze
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
    // This will call /api/v1/analysis/analyze/image
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
    // REFACTOR-02 FIX: Handle HTTP errors consistently with analyze() and analyzeImage().
    // Without this check, 4xx/5xx errors would return as apparent "successes".
    const response = await fetch(`${this.baseUrl}/analysis/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ request_id, user_rating, user_comment, was_helpful }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Feedback submission failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
  }

  async healthCheck() {
    // This calls the health endpoint inside the V1 prefix
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