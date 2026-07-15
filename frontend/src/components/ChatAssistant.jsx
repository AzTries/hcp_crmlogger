import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { sendChatMessage, addChatMessage, fetchInteractions } from '../store/interactionsSlice';

export default function ChatAssistant() {
  const dispatch = useDispatch();
  const chatMessages = useSelector((state) => state.interactions.chatMessages);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    dispatch(addChatMessage(userMessage));
    setInput('');
    setIsLoading(true);

    // Send the full history (including the message we just added) to the backend
    const fullHistory = [...chatMessages, userMessage];
    await dispatch(sendChatMessage(fullHistory));
    dispatch(fetchInteractions());

    setIsLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-assistant">
      <h2>🩺 AI Assistant</h2>
      <p className="chat-subtitle">Log interaction via chat</p>

      <div className="chat-messages">
        {chatMessages.length === 0 && (
          <p className="chat-placeholder">
            Log interaction details here (e.g., "Met Dr. Smith, discussed Product X efficacy,
            positive sentiment, shared brochure") or ask for help.
          </p>
        )}
        {chatMessages.map((msg, idx) => (
          <div key={idx} className={`chat-bubble ${msg.role}`}>
            {msg.content}
          </div>
        ))}
        {isLoading && <div className="chat-bubble assistant">Thinking...</div>}
      </div>

      <div className="chat-input-row">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe interaction..."
          disabled={isLoading}
        />
        <button onClick={handleSend} disabled={isLoading}>
          Send
        </button>
      </div>
    </div>
  );
}