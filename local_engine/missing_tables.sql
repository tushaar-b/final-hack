-- =============================================================================
-- MISSING CORE SCHEMA TABLES (forecasts, outcomes, models, users)
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.forecasts (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    forecast_date DATE NOT NULL,        
    closing_price NUMERIC(12,4) NOT NULL,
    p10_day1 NUMERIC(8,5), p50_day1 NUMERIC(8,5), p90_day1 NUMERIC(8,5),
    p10_day2 NUMERIC(8,5), p50_day2 NUMERIC(8,5), p90_day2 NUMERIC(8,5),
    p10_day3 NUMERIC(8,5), p50_day3 NUMERIC(8,5), p90_day3 NUMERIC(8,5),
    p10_day4 NUMERIC(8,5), p50_day4 NUMERIC(8,5), p90_day4 NUMERIC(8,5),
    p10_day5 NUMERIC(8,5), p50_day5 NUMERIC(8,5), p90_day5 NUMERIC(8,5),
    conviction_score NUMERIC(4,1),
    signal_stance TEXT NOT NULL DEFAULT 'HOLD',  
    stop_loss NUMERIC(12,4), target_price NUMERIC(12,4),
    position_pct NUMERIC(5,2),
    model_version TEXT,                  
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, forecast_date)
);

CREATE TABLE IF NOT EXISTS public.signal_outcomes (
    forecast_id BIGINT REFERENCES public.forecasts(id),
    outcome_date DATE,
    actual_close NUMERIC(12,4),
    realized_return NUMERIC(8,5),
    direction_correct BOOLEAN,
    outcome_type TEXT,    
    PRIMARY KEY (forecast_id)
);

CREATE TABLE IF NOT EXISTS public.model_registry (
    id BIGSERIAL PRIMARY KEY,
    version_tag TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL DEFAULT 'challenger',  
    trained_at TIMESTAMPTZ DEFAULT NOW(),
    backtest_accuracy NUMERIC(5,4),
    backtest_sharpe NUMERIC(6,3),
    backtest_metrics_json JSONB,
    approved_by TEXT,
    approved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'subscriber',  
    telegram_chat_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.watchlist (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, symbol)
);

CREATE TABLE IF NOT EXISTS public.portfolio_log (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    entry_price NUMERIC(12,4), exit_price NUMERIC(12,4),
    entry_date DATE, exit_date DATE,
    quantity INT, notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_forecasts_date ON public.forecasts(forecast_date DESC);

ALTER TABLE public.forecasts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portfolio_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_registry ENABLE ROW LEVEL SECURITY;

CREATE POLICY "public read forecasts" ON public.forecasts FOR SELECT USING (true);
CREATE POLICY "service writes forecasts" ON public.forecasts FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "own watchlist" ON public.watchlist FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "own portfolio" ON public.portfolio_log FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "own profile read" ON public.user_profiles FOR SELECT USING (auth.uid() = id);

-- Force PostgREST to reload its schema cache
NOTIFY pgrst, 'reload schema';
