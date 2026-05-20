CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE,
    title TEXT,
    source TEXT,
    content TEXT,
    published_at TEXT,
    collected_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS digests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    summary TEXT,
    raw_data TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    digest_date TEXT NOT NULL,
    keyword TEXT,
    actor TEXT,
    viewpoint TEXT,
    instruments TEXT,
    direction TEXT,
    forecast_cycle TEXT,
    logic TEXT,
    related_articles TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS limitup_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    stock_code TEXT NOT NULL,
    stock_name TEXT NOT NULL,
    consecutive_days INTEGER DEFAULT 1,
    start_price REAL,
    current_price REAL,
    gain_since_start REAL,
    themes TEXT,
    first_limit_time TEXT,
    market_cap REAL,
    sealed_amount REAL,
    turnover_rate REAL,
    is_new_high INTEGER DEFAULT 0,
    UNIQUE(date, stock_code)
);

CREATE TABLE IF NOT EXISTS theme_heat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    theme TEXT NOT NULL,
    limitup_count INTEGER DEFAULT 0,
    leading_stock TEXT,
    avg_consecutive REAL DEFAULT 1.0,
    total_market_cap REAL,
    UNIQUE(date, theme)
);

CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url);
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_collected ON articles(collected_at);
CREATE INDEX IF NOT EXISTS idx_digests_date ON digests(date);
CREATE INDEX IF NOT EXISTS idx_limitup_date ON limitup_records(date);
CREATE INDEX IF NOT EXISTS idx_theme_heat_date ON theme_heat(date);
