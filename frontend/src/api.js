const configuredBase = import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, '');
const BASE_URL = configuredBase || '/api';

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
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

  const rawBody = await response.text();
  let data = null;
  try {
    data = rawBody ? JSON.parse(rawBody) : null;
  } catch {
    // The API should always return JSON. HTML errors usually come from the
    // Vite proxy or Flask's debug page, so expose the status instead of hiding it.
  }

  if (!response.ok) {
    let message = data?.error;
    if (!message) {
      if (response.status === 401) {
        message = 'Your session has expired. Please sign in again.';
      } else if ([502, 503, 504].includes(response.status)) {
        message = 'The task server is temporarily unavailable. Make sure the Flask backend is running, then try again.';
      } else if (response.status === 404) {
        message =
          'The API endpoint was not found. Open the app through the Vite dev server (port 5173) or Flask (port 5055), not a static file server.';
      } else if (response.status >= 500) {
        message = `The server could not complete the request (error ${response.status}). Please try again.`;
      } else {
        message = `Request failed (error ${response.status}). Please try again.`;
      }
    }

    if (response.status === 401 && !path.startsWith('/auth/')) {
      window.dispatchEvent(new Event('auth:expired'));
    }

    const error = new Error(message);
    error.status = response.status;
    error.fields = data?.fields || {};
    throw error;
  }

  if (data === null) {
    throw new Error('The server returned an unexpected response. Please try again.');
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
