const BASE_URL = '/api';

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (response.status === 204) return null;

  let data = null;
  try {
    data = await response.json();
  } catch {
    // Non-JSON response (e.g. server crash); fall through to a generic error.
  }

  if (!response.ok) {
    const error = new Error(data?.error || 'Something went wrong. Please try again.');
    error.status = response.status;
    error.fields = data?.fields || {};
    throw error;
  }

  return data;
}

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
