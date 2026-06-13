import { useState, useEffect, useCallback } from 'react';
import { fetchConversations, createConversation, deleteConversation, renameConversation } from '../api';

const MODELS = [
  { value: 'claude', label: 'Claude (Anthropic)' },
  { value: 'openai', label: 'GPT-4o (OpenAI)' },
  { value: 'gemini', label: 'Gemini (Google)' },
  { value: 'mistral', label: 'Mistral' },
  { value: 'groq', label: 'Groq' },
];

export default function Sidebar({ activeConv, onSelectConv, model, onModelChange, user, onLogout, refreshKey, theme, toggleTheme }) {
  const [conversations, setConversations] = useState([]);
  const [renaming, setRenaming] = useState(null);
  const [renameTitle, setRenameTitle] = useState('');

  const loadConversations = useCallback(async () => {
    try {
      const convs = await fetchConversations();
      setConversations(convs.sort((a, b) => b.updated_at?.localeCompare(a.updated_at) || 0));
    } catch {
      // silent
    }
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations, refreshKey]);

  async function handleNew() {
    try {
      const conv = await createConversation();
      await loadConversations();
      onSelectConv(conv.id);
    } catch {
      // silent
    }
  }

  async function handleDelete(e, id) {
    e.stopPropagation();
    try {
      await deleteConversation(id);
      if (activeConv === id) onSelectConv(null);
      await loadConversations();
    } catch {
      // silent
    }
  }

  function handleRenameStart(e, conv) {
    e.stopPropagation();
    setRenaming(conv.id);
    setRenameTitle(conv.title || '');
  }

  async function handleRenameSubmit(e) {
    e.preventDefault();
    if (!renaming || !renameTitle.trim()) return;
    try {
      await renameConversation(renaming, renameTitle.trim());
      await loadConversations();
    } catch {
      // silent
    }
    setRenaming(null);
  }

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>Chats</h2>
      </div>

      <button className="sidebar-new-btn" onClick={handleNew}>
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="8" y1="2" x2="8" y2="14" />
          <line x1="2" y1="8" x2="14" y2="8" />
        </svg>
        New conversation
      </button>

      <div className="conversation-list">
        {conversations.map((conv) => (
          <div
            key={conv.id}
            className={`conv-item ${activeConv === conv.id ? 'active' : ''}`}
            onClick={() => onSelectConv(conv.id)}
          >
            <span className="conv-item-title">{conv.title || 'New conversation'}</span>
            <div className="conv-item-actions">
              <button title="Rename" onClick={(e) => handleRenameStart(e, conv)}>✎</button>
              <button title="Delete" onClick={(e) => handleDelete(e, conv.id)}>×</button>
            </div>
          </div>
        ))}
      </div>

      <div className="sidebar-model-select">
        <label htmlFor="model-select">Model</label>
        <select
          id="model-select"
          value={model}
          onChange={(e) => onModelChange(e.target.value)}
        >
          {MODELS.map((m) => (
            <option key={m.value} value={m.value}>{m.label}</option>
          ))}
        </select>
      </div>

      <div className="sidebar-footer">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
            <span className="user-info">{user?.displayName || user?.email || 'User'}</span>
            <button
              className="theme-toggle-btn"
              onClick={toggleTheme}
              title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {theme === 'dark' ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="5" fill="currentColor" />
                  <line x1="12" y1="1" x2="12" y2="3" />
                  <line x1="12" y1="21" x2="12" y2="23" />
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                  <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                  <line x1="1" y1="12" x2="3" y2="12" />
                  <line x1="21" y1="12" x2="23" y2="12" />
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                  <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                </svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" fill="currentColor" />
                </svg>
              )}
            </button>
          </div>
          <button className="logout-btn" onClick={onLogout} style={{ alignSelf: 'flex-start', padding: 0 }}>Log out</button>
        </div>
      </div>

      {renaming && (
        <div className="rename-overlay" onClick={() => setRenaming(null)}>
          <form className="rename-dialog" onClick={(e) => e.stopPropagation()} onSubmit={handleRenameSubmit}>
            <h3>Rename conversation</h3>
            <input
              className="text-input"
              value={renameTitle}
              onChange={(e) => setRenameTitle(e.target.value)}
              autoFocus
            />
            <div className="rename-dialog-actions">
              <button type="button" className="btn-secondary" onClick={() => setRenaming(null)} style={{ padding: '8px 16px' }}>
                Cancel
              </button>
              <button type="submit" className="btn-primary" style={{ padding: '8px 16px' }}>
                Save
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
