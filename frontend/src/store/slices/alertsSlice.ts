import { createSlice } from '@reduxjs/toolkit';

interface AlertsState {
  alerts: any[];
  unreadCount: number;
  isLoading: boolean;
  error: string | null;
}

const initialState: AlertsState = {
  alerts: [],
  unreadCount: 0,
  isLoading: false,
  error: null,
};

const alertsSlice = createSlice({
  name: 'alerts',
  initialState,
  reducers: {},
});

export default alertsSlice.reducer;