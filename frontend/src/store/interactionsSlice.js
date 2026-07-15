import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000/api';

// Async thunk: fetches all interactions from the backend
export const fetchInteractions = createAsyncThunk(
  'interactions/fetchAll',
  async () => {
    const response = await axios.get(`${API_BASE}/interactions`);
    return response.data;
  }
);

// Async thunk: creates a new interaction (structured form submit)
export const createInteraction = createAsyncThunk(
  'interactions/create',
  async (interactionData) => {
    const response = await axios.post(`${API_BASE}/interactions`, interactionData);
    return response.data;
  }
);

// Async thunk: sends the full conversation history to the LangGraph agent
export const sendChatMessage = createAsyncThunk(
  'interactions/sendChat',
  async (conversationHistory) => {
    const response = await axios.post(`${API_BASE}/chat`, {
      messages: conversationHistory,
    });
    return response.data;
  }
);

const interactionsSlice = createSlice({
  name: 'interactions',
  initialState: {
    items: [],
    status: 'idle', // idle | loading | succeeded | failed
    error: null,
    chatMessages: [], // { role: 'user' | 'assistant', content: string }
  },
  reducers: {
    addChatMessage: (state, action) => {
      state.chatMessages.push(action.payload);
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchInteractions.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.items = action.payload;
      })
      .addCase(fetchInteractions.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
      })
      .addCase(createInteraction.fulfilled, (state, action) => {
        state.items.unshift(action.payload);
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.chatMessages.push({ role: 'assistant', content: action.payload.reply });
      });
  },
});

export const { addChatMessage } = interactionsSlice.actions;
export default interactionsSlice.reducer;