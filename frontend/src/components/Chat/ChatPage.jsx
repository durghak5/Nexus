// frontend/src/components/Chat/ChatPage.jsx
import { useState, useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import TypingIndicator from './TypingIndicator';
import { streamChat, getQuickPrompts } from '../../services/agentApi';
import './ChatPage.css';

function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [quickPrompts, setQuickPrompts] = useState([]);
  const [error, setError] = useState(null);

  const messagesEndRef = useRef(null);
  const abortRef = useRef(null);
  // Buffer for the current assistant message — avoids React state batching issues
  const bufferRef = useRef('');

  useEffect(() => {
    getQuickPrompts()
      .then((data) => setQuickPrompts(data.prompts || []))
      .catch(() => setQuickPrompts([]));
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streaming]);

  const sendMessage = async (text) => {
    const userMessage = (text || input).trim();
    if (!userMessage || streaming) return;

    setInput('');
    setError(null);
    bufferRef.current = '';

    // Add user + placeholder assistant messages
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: userMessage },
      { role: 'assistant', content: '' },
    ]);
    setStreaming(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await streamChat(
        userMessage,
        sessionId,
        (event) => {
          if (event.type === 'session') {
            setSessionId(event.session_id);
          } else if (event.type === 'text') {
            // Append to buffer
            bufferRef.current += event.content;
            // Update the LAST assistant message with the accumulated text
            setMessages((prev) => {
              const copy = [...prev];
              for (let i = copy.length - 1; i >= 0; i--) {
                if (copy[i].role === 'assistant') {
                  copy[i] = { ...copy[i], content: bufferRef.current };
                  break;
                }
              }
              return copy;
            });
          } else if (event.type === 'tool_call') {
            console.log('🔧 Tool call:', event.name, event.args);
          } else if (event.type === 'tool_result') {
            console.log('✅ Tool result:', event.name, event.result);
          } else if (event.type === 'error') {
            setError(event.message);
          }
        },
        controller.signal
      );
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Failed to reach the assistant');
      }
    } finally {
      setStreaming(false);
      abortRef.current = null;
    }
  };

  const cancelStream = () => {
    abortRef.current?.abort();
    setStreaming(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const resetChat = () => {
    setMessages([]);
    setSessionId(null);
    setError(null);
    bufferRef.current = '';
  };

  return (
    <div className="chat-page">
      <div className="chat-page__header">
        <div className="chat-page__title">
          <span className="chat-page__title-icon">💊</span>
          <div>
            <h1>MediScan AI</h1>
            <p>Ask about drug interactions, alternatives, or your prescription</p>
          </div>
        </div>
        {messages.length > 0 && (
          <button className="btn-ghost" onClick={resetChat} disabled={streaming}>
            New chat
          </button>
        )}
      </div>

      <div className="chat-page__messages">
        {messages.length === 0 && (
          <div className="chat-page__empty">
            <div className="chat-page__empty-icon">💬</div>
            <h2>How can I help you today?</h2>
            <p>Ask about your prescription or check for interactions</p>
            <div className="quick-prompts">
              {quickPrompts.map((prompt, i) => (
                <button
                  key={i}
                  className="quick-prompt"
                  onClick={() => sendMessage(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => {
          const isLastAssistant =
            msg.role === 'assistant' && i === messages.length - 1;
          const isEmpty = !msg.content || msg.content.trim() === '';

          // Show typing dots only if the assistant slot is empty AND streaming
          if (isLastAssistant && isEmpty && streaming) {
            return <TypingIndicator key={i} />;
          }

          // Skip empty assistant messages (will render when content arrives)
          if (msg.role === 'assistant' && isEmpty) {
            return null;
          }

          return <ChatMessage key={i} role={msg.role} content={msg.content} />;
        })}

        {error && (
          <div className="chat-page__error">
            ⚠️ {error}
            <button
              onClick={() => {
                const lastUser = [...messages].reverse().find((m) => m.role === 'user');
                setMessages((prev) => prev.slice(0, -1)); // drop failed assistant
                if (lastUser) sendMessage(lastUser.content);
              }}
            >
              Retry
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-page__input">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your prescription..."
          rows={1}
          disabled={streaming}
        />
        {streaming ? (
          <button className="btn-cancel" onClick={cancelStream}>
            Stop
          </button>
        ) : (
          <button
            className="btn-send"
            onClick={() => sendMessage()}
            disabled={!input.trim()}
          >
            Send
          </button>
        )}
      </div>

      <p className="chat-page__disclaimer">
        ⚠️ Informational only. Always consult your doctor or pharmacist.
      </p>
    </div>
  );
}

export default ChatPage;