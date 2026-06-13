import { useState, useEffect, useRef, useCallback } from 'react';
import { fetchMessages, streamChat } from '../api';
import MessageInput from './MessageInput';
import MemoryDrawer from './MemoryDrawer';

function renderMarkdown(text) {
  if (!text) return '';

  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // code blocks
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    return `<pre><code class="language-${lang}">${code}</code></pre>`;
  });

  // inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

  // italic
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // headings
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // blockquote
  html = html.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');

  // unordered list items
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>');

  // ordered list items
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

  // wrap consecutive <li> in <ul>
  html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');

  // paragraphs: wrap non-tag lines
  html = html
    .split('\n\n')
    .map((block) => {
      const trimmed = block.trim();
      if (!trimmed) return '';
      if (/^<[a-z]/.test(trimmed)) return trimmed;
      return `<p>${trimmed.replace(/\n/g, '<br/>')}</p>`;
    })
    .join('\n');

  return html;
}

export default function ChatPanel({ conversationId, model, onConversationCreated }) {
  const [messages, setMessages] = useState([]);
  const [streaming, setStreaming] = useState(false);
  const [streamText, setStreamText] = useState('');
  const [searchStatus, setSearchStatus] = useState('');
  const [memories, setMemories] = useState([]);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const messagesEndRef = useRef(null);
  const controllerRef = useRef(null);

  useEffect(() => {
    if (!conversationId) {
      setMessages([]);
      return;
    }
    fetchMessages(conversationId)
      .then(setMessages)
      .catch(() => {});
  }, [conversationId]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamText, scrollToBottom]);

  function handleSend(text, attachments) {
    if (streaming) return;

    const userMsg = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setStreaming(true);
    setStreamText('');
    setSearchStatus('');
    setMemories([]);

    const body = {
      message: text,
      conversation_id: conversationId || undefined,
      model,
      attachments: attachments?.length
        ? attachments.map((a) => ({
            type: a.type,
            content: a.content,
            filename: a.filename,
            media_type: a.media_type,
          }))
        : undefined,
    };

    let accumulated = '';

    controllerRef.current = streamChat(body, {
      onChunk(chunk) {
        accumulated += chunk;
        setStreamText(accumulated);
      },
      onDone() {
        setMessages((prev) => [...prev, { role: 'assistant', content: accumulated }]);
        setStreamText('');
        setStreaming(false);
      },
      onMemory(mems) {
        setMemories(mems || []);
      },
      onSearch(status) {
        setSearchStatus(status);
      },
      onError(err) {
        setMessages((prev) => [...prev, { role: 'assistant', content: `Error: ${err}` }]);
        setStreamText('');
        setStreaming(false);
      },
      onConversationId(id) {
        if (!conversationId) onConversationCreated?.(id);
      },
    });
  }

  const hasMessages = messages.length > 0 || streaming;

  return (
    <>
      <div className="chat-panel">
        <div className="chat-header">
          <span className="chat-header-title">
            {conversationId ? 'Conversation' : 'New chat'}
          </span>
          <div className="chat-header-actions">
            <span className="model-badge">{model}</span>
            <button
              className={`memory-toggle ${drawerOpen ? 'active' : ''}`}
              onClick={() => setDrawerOpen(!drawerOpen)}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a8 8 0 0 1 8 8c0 3-1.5 5.5-4 7v3H8v-3c-2.5-1.5-4-4-4-7a8 8 0 0 1 8-8z" />
                <line x1="9" y1="22" x2="15" y2="22" />
              </svg>
              Memory
              {memories.length > 0 && ` (${memories.length})`}
            </button>
          </div>
        </div>

        {!hasMessages ? (
          <div className="empty-state">
            <h2>Start a conversation</h2>
            <p>Send a message to begin. Mnemo remembers important details across sessions.</p>
          </div>
        ) : (
          <div className="messages-container">
            <div className="messages-inner">
              {searchStatus && (
                <div className="search-indicator">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                  {searchStatus}
                </div>
              )}

              {messages.map((msg, i) => (
                <div key={i} className={`message ${msg.role}`}>
                  <div className="message-role">{msg.role}</div>
                  <div
                    className="message-content"
                    dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
                  />
                </div>
              ))}

              {streaming && streamText && (
                <div className="message assistant">
                  <div className="message-role">assistant</div>
                  <div className="message-content">
                    <span dangerouslySetInnerHTML={{ __html: renderMarkdown(streamText) }} />
                    <span className="streaming-cursor" />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>
        )}

        <MessageInput onSend={handleSend} disabled={streaming} model={model} />
      </div>

      <MemoryDrawer
        open={drawerOpen}
        memories={memories}
        onClose={() => setDrawerOpen(false)}
      />
    </>
  );
}
