import { useState } from 'react';

export default function LandingPage({ onGetStarted, theme, toggleTheme }) {
  return (
    <div className="landing">
      <nav className="landing-nav">
        <div className="landing-nav-inner">
          <span className="landing-wordmark">Mnemo</span>
          <div className="landing-nav-links">
            <a href="#features">Features</a>
            <a href="#models">Models</a>
            <a href="#memory">Memory</a>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <button
              className="theme-toggle-btn"
              onClick={toggleTheme}
              title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {theme === 'dark' ? (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" fill="currentColor" />
                </svg>
              )}
            </button>
            <button className="btn-primary" onClick={onGetStarted} style={{ padding: '10px 20px', fontSize: '14px' }}>
              Get started free
            </button>
          </div>
        </div>
      </nav>

      <section className="landing-hero">
        <div className="landing-container">
          <h1 className="landing-display-lg">
            A chatbot that<br />actually remembers you
          </h1>
          <p className="landing-hero-sub">
            Mnemo is a multi-model AI assistant with persistent cross-session memory.
            It learns your preferences, recalls past decisions, and gets smarter every conversation.
          </p>
          <div className="landing-hero-actions">
            <button className="btn-primary" onClick={onGetStarted}>Get started free</button>
            <a href="#features" className="btn-secondary">See how it works</a>
          </div>
        </div>
      </section>

      <section className="landing-logo-strip">
        <div className="landing-container">
          <p className="landing-logo-label">Powered by leading AI providers</p>
          <div className="landing-logos">
            <span>OpenAI</span>
            <span>Anthropic</span>
            <span>Google</span>
            <span>Mistral</span>
            <span>Groq</span>
          </div>
        </div>
      </section>

      <section className="landing-section" id="features">
        <div className="landing-container">
          <h2 className="landing-display-md">Everything you need in one interface</h2>
          <div className="landing-feature-grid">
            <div className="landing-feature-card">
              <div className="landing-feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a8 8 0 0 1 8 8c0 3-1.5 5.5-4 7v3H8v-3c-2.5-1.5-4-4-4-7a8 8 0 0 1 8-8z" />
                  <line x1="9" y1="22" x2="15" y2="22" />
                </svg>
              </div>
              <h3>Cross-session memory</h3>
              <p>Mnemo extracts and stores facts from every conversation. Your preferences, decisions, and context persist across sessions with no repetition needed.</p>
            </div>
            <div className="landing-feature-card">
              <div className="landing-feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="3" width="20" height="14" rx="2" />
                  <line x1="8" y1="21" x2="16" y2="21" />
                  <line x1="12" y1="17" x2="12" y2="21" />
                </svg>
              </div>
              <h3>Five models, one interface</h3>
              <p>Switch between Claude, GPT-4o, Gemini, Mistral, and Groq mid-conversation. Same memory, same context, different strengths.</p>
            </div>
            <div className="landing-feature-card">
              <div className="landing-feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8" />
                  <line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
              </div>
              <h3>Real-time web search</h3>
              <p>Mnemo automatically detects when you need current information and searches the web, injecting fresh context into the response.</p>
            </div>
            <div className="landing-feature-card">
              <div className="landing-feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="9" y="1" width="6" height="12" rx="3" />
                  <path d="M5 10a7 7 0 0 0 14 0" />
                  <line x1="12" y1="17" x2="12" y2="21" />
                </svg>
              </div>
              <h3>Voice input & output</h3>
              <p>Speak to Mnemo with Whisper transcription. Have responses read back with natural ElevenLabs voices. Hands-free, full-featured.</p>
            </div>
            <div className="landing-feature-card">
              <div className="landing-feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                </svg>
              </div>
              <h3>File & image uploads</h3>
              <p>Upload PDFs, CSVs, images, and code files. Mnemo processes them and weaves the content into the conversation context.</p>
            </div>
            <div className="landing-feature-card">
              <div className="landing-feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="16 18 22 12 16 6" />
                  <polyline points="8 6 2 12 8 18" />
                </svg>
              </div>
              <h3>Sandboxed code execution</h3>
              <p>Run Python code in an isolated Docker container. Visualize data with matplotlib plots rendered inline in the chat.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-section landing-section--flush">
        <div className="landing-container">
          <div className="landing-signature-card coral">
            <div className="landing-signature-content">
              <h2>Memory that gets smarter over time</h2>
              <p>
                Mnemo doesn't just store conversations; it extracts semantic facts and episodic context,
                reconciles contradictions, and builds a persistent knowledge graph unique to you.
                Correct a fact once, and it stays corrected forever.
              </p>
              <button className="btn-primary" onClick={onGetStarted}>
                Try it yourself
              </button>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-section" id="models">
        <div className="landing-container">
          <h2 className="landing-display-md">Choose the right model for the task</h2>
          <p className="landing-section-sub">
            Every model shares the same memory layer. Switch freely without losing context.
          </p>
          <div className="landing-model-grid">
            {[
              { name: 'Claude', provider: 'Anthropic', desc: 'Nuanced reasoning and careful analysis' },
              { name: 'GPT-4o', provider: 'OpenAI', desc: 'Versatile general-purpose intelligence' },
              { name: 'Gemini', provider: 'Google', desc: 'Multimodal understanding at scale' },
              { name: 'Mistral', provider: 'Mistral AI', desc: 'Efficient European-built models' },
              { name: 'Groq', provider: 'Groq', desc: 'Ultra-fast inference for rapid iteration' },
            ].map((m) => (
              <div className="landing-model-card" key={m.name}>
                <h4>{m.name}</h4>
                <span className="landing-model-provider">{m.provider}</span>
                <p>{m.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="landing-section landing-section--flush" id="memory">
        <div className="landing-container">
          <div className="landing-signature-card dark">
            <h2>Your assistant, your memory</h2>
            <p>
              Every preference you share, every decision you make, every correction you give: Mnemo remembers.
              Across sessions, across models, across time.
            </p>
            <div className="landing-memory-pills">
              <span className="landing-pill semantic">Prefers Python</span>
              <span className="landing-pill semantic">Uses FastAPI</span>
              <span className="landing-pill episodic">Chose PostgreSQL over MySQL</span>
              <span className="landing-pill semantic">Works at Google DeepMind</span>
              <span className="landing-pill episodic">Moved from PST to EST</span>
              <span className="landing-pill semantic">Prefers concise responses</span>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-cta-band">
        <div className="landing-container">
          <div className="landing-cta-card">
            <h2 className="landing-display-md">Start your first conversation</h2>
            <p>Free to use. No credit card required.</p>
            <button className="btn-primary" onClick={onGetStarted}>Get started free</button>
          </div>
        </div>
      </section>

      <footer className="landing-footer">
        <div className="landing-container">
          <div className="landing-footer-inner">
            <span className="landing-wordmark">Mnemo</span>
            <span className="landing-footer-copy">Built with memory in mind.</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
