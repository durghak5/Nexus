// frontend/src/services/agentApi.js
const BASE_URL = 'http://localhost:8000/api/v1/agent';

export async function getQuickPrompts() {
  const res = await fetch(`${BASE_URL}/quick-prompts`);
  if (!res.ok) throw new Error('Failed to load prompts');
  return res.json();
}

/**
 * Stream chat responses via SSE.
 * onEvent callback receives each parsed event.
 * Returns the session_id.
 */
export async function streamChat(message, sessionId, onEvent, signal) {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
    signal,
  });

  if (!res.ok) throw new Error(`Server error: ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let newSessionId = sessionId;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop(); // Keep incomplete

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      try {
        const event = JSON.parse(line.slice(6));
        if (event.type === 'session') newSessionId = event.session_id;
        onEvent(event);
      } catch (e) {
        console.warn('Bad SSE line:', line, e);
      }
    }
  }

  return newSessionId;
}

export async function clearSession(sessionId) {
  await fetch(`${BASE_URL}/clear/${sessionId}`, { method: 'POST' });
}