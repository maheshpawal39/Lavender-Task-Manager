const configuredBase = import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, '');
const BASE_URL = configuredBase || '/api';

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
  } catch (networkError) {
    const error = new Error(
      "Can't reach the server. Make sure the Flask backend is running on port 5055.",
    );
    error.cause = networkError;
    throw error;
  }

  if (response.status === 204) return null;

  let data = null;
  try {
    data = await response.json();
  } catch {
    // Non-JSON response (e.g. server crash); fall through to a generic error.
  }

  if (!response.ok) {
    if (response.status === 401 && !path.startsWith('/auth/')) {
      window.dispatchEvent(new Event('auth:expired'));
    }

    const error = new Error(data?.error || 'Something went wrong. Please try again.');
    error.status = response.status;
    error.fields = data?.fields || {};
    throw error;
  }

  return data;
}

export const authApi = {
  me() {
    return request('/auth/me');
  },

  login({ email, password, rememberMe }) {
    return request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password, remember_me: Boolean(rememberMe) }),
    });
  },

  register({ fullName, email, password }) {
    return request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ full_name: fullName, email, password }),
    });
  },

  logout() {
    return request('/auth/logout', { method: 'POST' });
  },
};

export const taskApi = {
  list({ status = 'all', search = '' } = {}) {
    const params = new URLSearchParams({ status });
    if (search.trim()) params.set('search', search.trim());
    return request(`/tasks?${params}`);
  },

  create(payload) {
    return request('/tasks', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  update(id, payload) {
    return request(`/tasks/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  remove(id) {
    return request(`/tasks/${id}`, { method: 'DELETE' });
  },

  stats() {
    return request('/stats');
  },
};
