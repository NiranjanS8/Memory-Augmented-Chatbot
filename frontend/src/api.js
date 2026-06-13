const API_BASE = 'http://localhost:8000';

function getToken() {
  return localStorage.getItem('token');
}

function setToken(token) {
  localStorage.setItem('token', token);
}

function clearToken() {
  localStorage.removeItem('token');
}

function getUser() {
  const raw = localStorage.getItem('user');
  return raw ? JSON.parse(raw) : null;
}

function setUser(user) {
  localStorage.setItem('user', JSON.stringify(user));
}

function clearUser() {
  localStorage.removeItem('user');
}

function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...options.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

export async function register(email, password, displayName) {
  const data = await request('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, display_name: displayName }),
  });
  setToken(data.access_token);
  setUser({ id: data.user_id, email: data.email, displayName: data.display_name });
  return data;
}

export async function login(email, password) {
  const data = await request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token);
  setUser({ id: data.user_id, email: data.email, displayName: data.display_name });
  return data;
}

export function logout() {
  clearToken();
  clearUser();
}

export function isAuthenticated() {
  return !!getToken();
}

export { getUser };

export async function fetchConversations() {
  return request('/api/conversations');
}

export async function createConversation() {
  return request('/api/conversations', { method: 'POST' });
}

export async function deleteConversation(id) {
  return request(`/api/conversations/${id}`, { method: 'DELETE' });
}

export async function renameConversation(id, title) {
  return request(`/api/conversations/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ title }),
  });
}

export async function fetchMessages(convId) {
  return request(`/api/conversations/${convId}/messages`);
}

export function streamChat(body, { onChunk, onDone, onMemory, onSearch, onError, onConversationId }) {
  const controller = new AbortController();

  fetch(`${API_BASE}/api/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(body),
    signal: controller.signal,
  })
    .then(async (response) => {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;

          try {
            const event = JSON.parse(raw);
            switch (event.type) {
              case 'chunk':
                onChunk?.(event.data);
                break;
              case 'done':
                onDone?.();
                break;
              case 'memory':
                if (event.conversation_id) onConversationId?.(event.conversation_id);
                onMemory?.(event.data);
                break;
              case 'search':
                onSearch?.(event.data);
                break;
              case 'error':
                onError?.(event.data);
                break;
            }
          } catch {
            // skip malformed lines
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') onError?.(err.message);
    });

  return controller;
}

export async function fetchMemories() {
  return request('/api/memory');
}

export async function clearMemories() {
  return request('/api/memory', { method: 'DELETE' });
}

export async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  const response = await fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    headers: authHeaders(),
    body: formData,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || 'Upload failed');
  }
  return response.json();
}

export async function transcribeAudio(audioBlob) {
  const formData = new FormData();
  formData.append('file', audioBlob, 'recording.webm');
  const response = await fetch(`${API_BASE}/api/voice/transcribe`, {
    method: 'POST',
    headers: authHeaders(),
    body: formData,
  });
  if (!response.ok) throw new Error('Transcription failed');
  return response.json();
}

export async function speakText(text, voice = 'aria') {
  const response = await fetch(`${API_BASE}/api/voice/speak`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify({ text, voice }),
  });
  if (!response.ok) throw new Error('Speech synthesis failed');
  return response.blob();
}
