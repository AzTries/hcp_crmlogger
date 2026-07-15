import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchInteractions } from './store/interactionsSlice';
import InteractionForm from './components/InteractionForm';
import ChatAssistant from './components/ChatAssistant';
import './App.css';

function App() {
  const dispatch = useDispatch();
  const { items, status } = useSelector((state) => state.interactions);

  useEffect(() => {
    dispatch(fetchInteractions());
  }, [dispatch]);

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>CRM Logger — HCP Interaction Module</h1>
      </header>

      <div className="main-layout">
        <InteractionForm />
        <ChatAssistant />
      </div>

      <section className="interactions-list">
        <h2>Logged Interactions</h2>
        {status === 'loading' && <p>Loading...</p>}
        {status === 'succeeded' && items.length === 0 && <p>No interactions logged yet.</p>}
        <div className="interactions-grid">
          {items.map((i) => (
            <div key={i.id} className="interaction-card">
              <div className="interaction-card-header">
                <span className={`sentiment-badge ${i.sentiment?.toLowerCase()}`}>
                  {i.sentiment || 'N/A'}
                </span>
                {i.ae_flagged && <span className="ae-badge">⚠️ AE Flagged</span>}
              </div>
              <p>{i.topics_discussed}</p>
              <small>{new Date(i.created_at).toLocaleString()}</small>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default App;