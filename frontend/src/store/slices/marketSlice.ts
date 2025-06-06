import { createSlice } from '@reduxjs/toolkit';

interface MarketState {
  etfs: any[];
  currentETF: any;
  marketData: any[];
  isLoading: boolean;
  error: string | null;
}

const initialState: MarketState = {
  etfs: [],
  currentETF: null,
  marketData: [],
  isLoading: false,
  error: null,
};

const marketSlice = createSlice({
  name: 'market',
  initialState,
  reducers: {},
});

export default marketSlice.reducer;