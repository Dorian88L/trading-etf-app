import { createSlice } from '@reduxjs/toolkit';

interface UserState {
  preferences: any;
  watchlist: any[];
  isLoading: boolean;
  error: string | null;
}

const initialState: UserState = {
  preferences: null,
  watchlist: [],
  isLoading: false,
  error: null,
};

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {},
});

export default userSlice.reducer;