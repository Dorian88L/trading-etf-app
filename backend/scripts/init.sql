-- Create TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create additional extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create enum types
CREATE TYPE signal_type AS ENUM ('BUY', 'SELL', 'HOLD', 'WAIT');
CREATE TYPE alert_type AS ENUM ('SIGNAL', 'EVENT', 'RISK', 'NEWS');
CREATE TYPE transaction_type AS ENUM ('BUY', 'SELL');

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ETFs table
CREATE TABLE etfs (
    isin VARCHAR(12) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    currency VARCHAR(3) DEFAULT 'EUR',
    ter DECIMAL(5,4), -- Total Expense Ratio
    aum BIGINT, -- Assets Under Management
    exchange VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Market data table (time-series)
CREATE TABLE market_data (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    etf_isin VARCHAR(12) NOT NULL REFERENCES etfs(isin),
    open_price DECIMAL(10,4),
    high_price DECIMAL(10,4),
    low_price DECIMAL(10,4),
    close_price DECIMAL(10,4),
    volume BIGINT,
    nav DECIMAL(10,4), -- Net Asset Value
    PRIMARY KEY (time, etf_isin)
);

-- Convert to hypertable for TimescaleDB
SELECT create_hypertable('market_data', 'time');

-- Technical indicators table (time-series)
CREATE TABLE technical_indicators (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    etf_isin VARCHAR(12) NOT NULL REFERENCES etfs(isin),
    sma_20 DECIMAL(10,4),
    sma_50 DECIMAL(10,4),
    sma_200 DECIMAL(10,4),
    ema_20 DECIMAL(10,4),
    ema_50 DECIMAL(10,4),
    rsi DECIMAL(5,2),
    macd DECIMAL(10,6),
    macd_signal DECIMAL(10,6),
    macd_histogram DECIMAL(10,6),
    bb_upper DECIMAL(10,4),
    bb_middle DECIMAL(10,4),
    bb_lower DECIMAL(10,4),
    atr DECIMAL(10,4),
    obv BIGINT,
    vwap DECIMAL(10,4),
    PRIMARY KEY (time, etf_isin)
);

-- Convert to hypertable
SELECT create_hypertable('technical_indicators', 'time');

-- Signals table
CREATE TABLE signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    etf_isin VARCHAR(12) NOT NULL REFERENCES etfs(isin),
    signal_type signal_type NOT NULL,
    confidence DECIMAL(5,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 100),
    price_target DECIMAL(10,4),
    stop_loss DECIMAL(10,4),
    technical_score DECIMAL(5,2),
    fundamental_score DECIMAL(5,2),
    risk_score DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

-- User portfolios
CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Portfolio positions
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    etf_isin VARCHAR(12) NOT NULL REFERENCES etfs(isin),
    quantity DECIMAL(12,4) NOT NULL,
    average_price DECIMAL(10,4) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(portfolio_id, etf_isin)
);

-- Transactions table
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    etf_isin VARCHAR(12) NOT NULL REFERENCES etfs(isin),
    transaction_type transaction_type NOT NULL,
    quantity DECIMAL(12,4) NOT NULL,
    price DECIMAL(10,4) NOT NULL,
    fees DECIMAL(10,4) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User watchlists
CREATE TABLE watchlists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    etf_isin VARCHAR(12) NOT NULL REFERENCES etfs(isin),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, etf_isin)
);

-- Alerts table
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    alert_type alert_type NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    etf_isin VARCHAR(12) REFERENCES etfs(isin),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User preferences
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    risk_tolerance DECIMAL(3,2) DEFAULT 0.5 CHECK (risk_tolerance >= 0 AND risk_tolerance <= 1),
    min_signal_confidence DECIMAL(5,2) DEFAULT 60,
    notification_settings JSONB DEFAULT '{"email": true, "push": true, "sms": false}',
    trading_preferences JSONB DEFAULT '{"max_position_size": 0.1, "stop_loss_pct": 0.05}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_market_data_etf_time ON market_data(etf_isin, time DESC);
CREATE INDEX idx_technical_indicators_etf_time ON technical_indicators(etf_isin, time DESC);
CREATE INDEX idx_signals_etf_active ON signals(etf_isin, is_active, created_at DESC);
CREATE INDEX idx_signals_confidence ON signals(confidence DESC, created_at DESC);
CREATE INDEX idx_positions_portfolio ON positions(portfolio_id);
CREATE INDEX idx_transactions_portfolio_time ON transactions(portfolio_id, created_at DESC);
CREATE INDEX idx_alerts_user_unread ON alerts(user_id, is_read, created_at DESC);
CREATE INDEX idx_watchlists_user ON watchlists(user_id);

-- Insert sample ETFs
INSERT INTO etfs (isin, name, sector, ter, aum, exchange) VALUES
('FR0010296061', 'Lyxor CAC 40 UCITS ETF', 'Broad Market', 0.0025, 3500000000, 'Euronext'),
('IE00B4L5Y983', 'iShares Core MSCI World UCITS ETF', 'Global Equity', 0.0020, 45000000000, 'Euronext'),
('LU0274211217', 'Xtrackers MSCI World UCITS ETF', 'Global Equity', 0.0019, 8500000000, 'Xetra'),
('IE00B4L5YC18', 'iShares Core S&P 500 UCITS ETF', 'US Equity', 0.0007, 55000000000, 'Euronext'),
('FR0010315770', 'Lyxor MSCI Emerging Markets UCITS ETF', 'Emerging Markets', 0.0055, 2100000000, 'Euronext'),
('IE00BKM4GZ66', 'iShares Core MSCI Europe UCITS ETF', 'European Equity', 0.0012, 12000000000, 'Euronext'),
('LU0290358497', 'Xtrackers EURO STOXX 50 UCITS ETF', 'European Equity', 0.0009, 4500000000, 'Xetra'),
('IE00B52MJD48', 'iShares NASDAQ 100 UCITS ETF', 'Technology', 0.0033, 8500000000, 'Euronext'),
('LU0488316133', 'Xtrackers MSCI Japan UCITS ETF', 'Japanese Equity', 0.0020, 2800000000, 'Xetra'),
('IE00B6R52259', 'iShares MSCI ACWI UCITS ETF', 'Global Equity', 0.0020, 12000000000, 'Euronext');

-- Create data retention policies
SELECT add_retention_policy('market_data', INTERVAL '5 years');
SELECT add_retention_policy('technical_indicators', INTERVAL '3 years');