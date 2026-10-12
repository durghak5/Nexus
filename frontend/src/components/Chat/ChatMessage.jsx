// frontend/src/components/Chat/ChatMessage.jsx
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './ChatMessage.css';

function ChatMessage({ role, content }) {
  const isUser = role === 'user';

  return (
    <div className={`chat-message ${isUser ? 'chat-message--user' : 'chat-message--assistant'}`}>
      <div className="chat-message__avatar">
        {isUser ? '👤' : '💊'}
      </div>
      <div className="chat-message__body">
        {isUser ? (
          <p>{content}</p>
        ) : (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {content}
          </ReactMarkdown>
        )}
      </div>
    </div>
  );
}

export default ChatMessage;