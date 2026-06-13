import { useState, useCallback } from 'react';
import Sidebar from './Sidebar';
import ChatPanel from './ChatPanel';
import { getUser, logout } from '../api';

export default function ChatLayout({ onLogout, theme, toggleTheme }) {
  const [activeConv, setActiveConv] = useState(null);
  const [model, setModel] = useState('openai');
  const [refreshKey, setRefreshKey] = useState(0);
  const user = getUser();

  function handleLogout() {
    logout();
    onLogout();
  }

  const handleConversationCreated = useCallback((id) => {
    setActiveConv(id);
    setRefreshKey((k) => k + 1);
  }, []);

  return (
    <div className="chat-layout">
      <Sidebar
        activeConv={activeConv}
        onSelectConv={setActiveConv}
        model={model}
        onModelChange={setModel}
        user={user}
        onLogout={handleLogout}
        refreshKey={refreshKey}
        theme={theme}
        toggleTheme={toggleTheme}
      />
      <ChatPanel
        conversationId={activeConv}
        model={model}
        onConversationCreated={handleConversationCreated}
      />
    </div>
  );
}
