import { createSlice } from '@reduxjs/toolkit';

interface SignalsState {
  activeSignals: any[];
  signalHistory: any[];
  isLoading: boolean;
  error: string | null;
}

const initialState: SignalsState = {
  activeSignals: [],
  signalHistory: [],
  isLoading: false,
  error: null,
};

const signalsSlice = createSlice({
  name: 'signals',
  initialState,
  reducers: {},
});

export default signalsSlice.reducer;