// frontend/src/components/Chat/TypingIndicator.jsx
import './TypingIndicator.css';

function TypingIndicator() {
  return (
    <div className="chat-message chat-message--assistant">
      <div className="chat-message__avatar">💊</div>
      <div className="chat-message__body typing-indicator">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  );
}

export default TypingIndicator;