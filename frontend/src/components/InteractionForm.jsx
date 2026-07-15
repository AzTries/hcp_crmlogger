import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import axios from 'axios';
import { createInteraction, fetchInteractions } from '../store/interactionsSlice';

const API_BASE = 'http://127.0.0.1:8000/api';

export default function InteractionForm() {
  const dispatch = useDispatch();
  const [hcps, setHcps] = useState([]);
  const [formData, setFormData] = useState({
    hcp_id: '',
    interaction_type: 'Meeting',
    attendees: '',
    topics_discussed: '',
    materials_shared: '',
    samples_distributed: '',
    sentiment: 'Neutral',
    outcomes: '',
    followup_actions: '',
  });

  // Load the HCP list once, for the dropdown
  useEffect(() => {
    axios.get(`${API_BASE}/hcps`).then((res) => setHcps(res.data));
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.hcp_id) {
      alert('Please select an HCP');
      return;
    }
    await dispatch(createInteraction({ ...formData, hcp_id: Number(formData.hcp_id) }));
    dispatch(fetchInteractions());
    // Reset form after submit
    setFormData({
      hcp_id: '',
      interaction_type: 'Meeting',
      attendees: '',
      topics_discussed: '',
      materials_shared: '',
      samples_distributed: '',
      sentiment: 'Neutral',
      outcomes: '',
      followup_actions: '',
    });
  };

  return (
    <form onSubmit={handleSubmit} className="interaction-form">
      <h2>Log HCP Interaction</h2>

      <label>HCP Name</label>
      <select name="hcp_id" value={formData.hcp_id} onChange={handleChange}>
        <option value="">Select HCP...</option>
        {hcps.map((h) => (
          <option key={h.id} value={h.id}>{h.name}</option>
        ))}
      </select>

      <label>Interaction Type</label>
      <select name="interaction_type" value={formData.interaction_type} onChange={handleChange}>
        <option>Meeting</option>
        <option>Call</option>
        <option>Email</option>
      </select>

      <label>Attendees</label>
      <input name="attendees" value={formData.attendees} onChange={handleChange} placeholder="Enter names..." />

      <label>Topics Discussed</label>
      <textarea name="topics_discussed" value={formData.topics_discussed} onChange={handleChange} placeholder="Enter key discussion points..." />

      <label>Materials Shared</label>
      <input name="materials_shared" value={formData.materials_shared} onChange={handleChange} placeholder="e.g. OncoBoost brochure" />

      <label>Samples Distributed</label>
      <input name="samples_distributed" value={formData.samples_distributed} onChange={handleChange} />

      <label>Observed/Inferred HCP Sentiment</label>
      <div className="sentiment-options">
        {['Positive', 'Neutral', 'Negative'].map((s) => (
          <label key={s}>
            <input
              type="radio"
              name="sentiment"
              value={s}
              checked={formData.sentiment === s}
              onChange={handleChange}
            />
            {s}
          </label>
        ))}
      </div>

      <label>Outcomes</label>
      <textarea name="outcomes" value={formData.outcomes} onChange={handleChange} placeholder="Key outcomes or agreements..." />

      <label>Follow-up Actions</label>
      <textarea name="followup_actions" value={formData.followup_actions} onChange={handleChange} placeholder="Enter next steps or tasks..." />

      <button type="submit">Log Interaction</button>
    </form>
  );
}