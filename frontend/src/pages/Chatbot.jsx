import { useState, useRef, useEffect } from 'react';
import './Chatbot.css';

const QUICK_PROMPTS = [
  'How does the physiological sigh relieve stress?',
  'Guide me through the 5-4-3-2-1 grounding technique',
  'What are common cognitive distortions in CBT?',
  'Explain sleep cycles and the 20-minute rule',
  'How does the gut-brain axis influence mood?',
  'What are the DBT TIPP skills for acute anxiety?',
];

function formatMessage(text) {
  if (!text) return '';

  const lines = text.split('\n');
  return lines.map((line, idx) => {
    // Check for headings
    if (line.startsWith('### ')) {
      return (
        <h4 key={idx} className="msg-heading-3">
          {renderFormattedInline(line.replace('### ', ''))}
        </h4>
      );
    }
    if (line.startsWith('## ')) {
      return (
        <h3 key={idx} className="msg-heading-2">
          {renderFormattedInline(line.replace('## ', ''))}
        </h3>
      );
    }

    // Check for bullet lists
    if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
      const cleanLine = line.trim().replace(/^[-*]\s+/, '');
      return (
        <li key={idx} className="msg-bullet-item">
          {renderFormattedInline(cleanLine)}
        </li>
      );
    }

    // Check for numbered lists (e.g. 1. , 2. )
    const numMatch = line.trim().match(/^(\d+)\.\s+(.*)/);
    if (numMatch) {
      return (
        <div key={idx} className="msg-numbered-item">
          <span className="msg-num-badge">{numMatch[1]}.</span>
          <span className="msg-num-content">{renderFormattedInline(numMatch[2])}</span>
        </div>
      );
    }

    // Empty line creates spacing
    if (!line.trim()) {
      return <div key={idx} className="msg-spacer" />;
    }

    return (
      <p key={idx} className="msg-paragraph">
        {renderFormattedInline(line)}
      </p>
    );
  });
}

function renderFormattedInline(str) {
  // Support bold **text** and inline `code`
  const parts = [];
  const regex = /(\*\*.*?\*\*|`.*?`)/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(str)) !== null) {
    if (match.index > lastIndex) {
      parts.push(str.substring(lastIndex, match.index));
    }
    const token = match[0];
    if (token.startsWith('**') && token.endsWith('**')) {
      parts.push(<strong key={match.index}>{token.slice(2, -2)}</strong>);
    } else if (token.startsWith('`') && token.endsWith('`')) {
      parts.push(<code key={match.index}>{token.slice(1, -1)}</code>);
    }
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < str.length) {
    parts.push(str.substring(lastIndex));
  }

  return parts.length > 0 ? parts : str;
}

export default function Chatbot() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        "Hello! I'm WellSync, your evidence-informed mental wellness companion powered by Groq and a comprehensive clinical wellness knowledge base. How can I support your well-being today?",
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const sendQuery = async (queryText) => {
    if (!queryText.trim() || loading) return;

    const userMessage = queryText.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const res = await fetch('/api/chatbot/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage, session_id: sessionId }),
      });
      const data = await res.json();

      if (data.session_id) setSessionId(data.session_id);
      setMessages((prev) => [...prev, { role: 'assistant', content: data.response }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I could not connect to the backend server. Please verify the Flask server is running.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendQuery(input);
  };

  return (
    <div className="chatbot-page">
      <div className="chatbot-header">
        <h1 className="page-title">Wellness Assistant</h1>
        <p className="page-subtitle">
          In-depth explanations of stress physiology, emotional regulation, CBT techniques, and sleep science. Powered by <strong>Groq LLM</strong> + <strong>Evidence-Based Knowledge Base</strong>.
        </p>
      </div>

      <div className="quick-prompts-container">
        <span className="quick-prompts-label">Explore Topics:</span>
        <div className="quick-prompts-chips">
          {QUICK_PROMPTS.map((prompt, i) => (
            <button
              key={i}
              type="button"
              className="prompt-chip"
              onClick={() => sendQuery(prompt)}
              disabled={loading}
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      <div className="chat-container card">
        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`chat-bubble ${msg.role}`}>
              <div className="bubble-header">
                {msg.role === 'assistant' ? '🌿 WellSync' : '👤 You'}
              </div>
              <div className="bubble-content">{formatMessage(msg.content)}</div>
            </div>
          ))}
          {loading && (
            <div className="chat-bubble assistant typing">
              <div className="bubble-header">🌿 WellSync</div>
              <div className="typing-indicator">
                <span>Generating explanation</span>
                <span className="dot dot-1">.</span>
                <span className="dot dot-2">.</span>
                <span className="dot dot-3">.</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form className="chat-input-form" onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question or describe how you are feeling..."
            disabled={loading}
          />
          <button type="submit" className="primary" disabled={loading || !input.trim()}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
