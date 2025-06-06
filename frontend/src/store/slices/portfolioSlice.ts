import { createSlice } from '@reduxjs/toolkit';

interface PortfolioState {
  positions: any[];
  transactions: any[];
  performance: any;
  isLoading: boolean;
  error: string | null;
}

const initialState: PortfolioState = {
  positions: [],
  transactions: [],
  performance: null,
  isLoading: false,
  error: null,
};

const portfolioSlice = createSlice({
  name: 'portfolio',
  initialState,
  reducers: {},
});

export default portfolioSlice.reducer;