import { useState, useEffect } from 'react';
import { flushSync } from 'react-dom';
import { isAuthenticated } from './api';
import LandingPage from './components/LandingPage';
import AuthPage from './components/AuthPage';
import ChatLayout from './components/ChatLayout';

export default function App() {
  const [authed, setAuthed] = useState(isAuthenticated());
  const [showAuth, setShowAuth] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light');

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark-theme');
    } else {
      document.documentElement.classList.remove('dark-theme');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = (e) => {
    if (!document.startViewTransition) {
      setTheme((t) => (t === 'light' ? 'dark' : 'light'));
      return;
    }

    if (e && e.clientX !== undefined && e.clientY !== undefined) {
      document.documentElement.style.setProperty('--clip-x', `${e.clientX}px`);
      document.documentElement.style.setProperty('--clip-y', `${e.clientY}px`);
    } else {
      document.documentElement.style.setProperty('--clip-x', '50%');
      document.documentElement.style.setProperty('--clip-y', '50%');
    }

    document.startViewTransition(() => {
      flushSync(() => {
        setTheme((t) => (t === 'light' ? 'dark' : 'light'));
      });
    });
  };

  if (authed) {
    return (
      <ChatLayout
        theme={theme}
        toggleTheme={toggleTheme}
        onLogout={() => { setAuthed(false); setShowAuth(false); }}
      />
    );
  }

  if (showAuth) {
    return (
      <AuthPage
        theme={theme}
        toggleTheme={toggleTheme}
        onAuth={() => setAuthed(true)}
        onBack={() => setShowAuth(false)}
      />
    );
  }

  return (
    <LandingPage
      theme={theme}
      toggleTheme={toggleTheme}
      onGetStarted={() => setShowAuth(true)}
    />
  );
}
