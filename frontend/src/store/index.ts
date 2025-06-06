import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import authSlice from './slices/authSlice';
import userSlice from './slices/userSlice';
import marketSlice from './slices/marketSlice';
import signalsSlice from './slices/signalsSlice';
import portfolioSlice from './slices/portfolioSlice';
import alertsSlice from './slices/alertsSlice';

export const store = configureStore({
  reducer: {
    auth: authSlice,
    user: userSlice,
    market: marketSlice,
    signals: signalsSlice,
    portfolio: portfolioSlice,
    alerts: alertsSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
});

setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;