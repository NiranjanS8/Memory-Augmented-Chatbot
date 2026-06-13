import { fetchMemories, clearMemories } from '../api';
import { useState, useEffect } from 'react';

export default function MemoryDrawer({ open, memories, onClose }) {
  const [allMemories, setAllMemories] = useState([]);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    if (showAll && open) {
      fetchMemories().then(setAllMemories).catch(() => {});
    }
  }, [showAll, open]);

  const displayMemories = showAll ? allMemories : memories;

  async function handleClear() {
    if (!confirm('Clear all stored memories? This cannot be undone.')) return;
    try {
      await clearMemories();
      setAllMemories([]);
    } catch {
      // silent
    }
  }

  return (
    <div className={`memory-drawer ${open ? 'open' : ''}`}>
      <div className="drawer-header">
        <h3>
          {showAll ? 'All Memories' : 'Retrieved Memories'}
        </h3>
        <div style={{ display: 'flex', gap: '4px' }}>
          <button
            className="btn-ghost"
            onClick={() => setShowAll(!showAll)}
            style={{ fontSize: '12px' }}
          >
            {showAll ? 'Show retrieved' : 'Show all'}
          </button>
          <button className="btn-ghost" onClick={onClose} title="Close">×</button>
        </div>
      </div>

      <div className="drawer-content">
        {displayMemories.length === 0 ? (
          <div className="drawer-empty">
            <p>{showAll ? 'No memories stored yet.' : 'No memories retrieved for this query.'}</p>
          </div>
        ) : (
          displayMemories.map((mem, i) => (
            <div className="memory-card" key={mem.id || i}>
              <span className={`memory-card-type ${mem.type || 'semantic'}`}>
                {mem.type || 'semantic'}
              </span>
              <p className="memory-card-text">{mem.content}</p>
            </div>
          ))
        )}
      </div>

      <div className="drawer-actions">
        <button onClick={handleClear}>Clear all memories</button>
      </div>
    </div>
  );
}
