# ── 기본 자금 ─────────────────────────────────────────────────
DEFAULT_INITIAL_CAPITAL = 10_000_000   # 1000만원
DEFAULT_EXCHANGE_RATE   = 1350         # 원/달러

# ── 수수료 ────────────────────────────────────────────────────
KR_FEE_RATE  = 0.00015   # 국내 0.015%
US_FEE_RATE  = 0.0001    # 미국 0.01%

# ── 스윙 전략 파라미터 ────────────────────────────────────────
SWING_TAKE_PROFIT = 0.03    # +3%
SWING_STOP_LOSS   = -0.02   # -2%

# ── 스캘핑 전략 파라미터 ──────────────────────────────────────
SCALP_TAKE_PROFIT_KR = 0.010   # KR +1.0%
SCALP_TAKE_PROFIT_US = 0.015   # US +1.5%
SCALP_STOP_LOSS      = -0.005  # -0.5%

# ── 포지션 관리 ───────────────────────────────────────────────
MAX_POSITIONS     = 8      # 최대 동시 보유 종목
MAX_POSITION_RATIO = 0.15  # 종목당 최대 비중 15%
DAILY_TARGET_RATE  = 0.02  # 일일 목표 수익률 2%

# ── 자동매매 스케줄 ───────────────────────────────────────────
SCAN_INTERVAL_MINUTES = 3  # 3분마다 스캔

# ── 종목 풀 (기본 fallback) ───────────────────────────────────
DOMESTIC_STOCK_POOL = [
    {"code": "005930.KS", "name": "삼성전자",  "market": "KR"},
    {"code": "000660.KS", "name": "SK하이닉스", "market": "KR"},
    {"code": "035420.KS", "name": "NAVER",      "market": "KR"},
    {"code": "035720.KS", "name": "카카오",     "market": "KR"},
    {"code": "051910.KS", "name": "LG화학",     "market": "KR"},
    {"code": "006400.KS", "name": "삼성SDI",    "market": "KR"},
    {"code": "207940.KS", "name": "삼성바이오로직스", "market": "KR"},
    {"code": "068270.KS", "name": "셀트리온",   "market": "KR"},
    {"code": "005380.KS", "name": "현대차",     "market": "KR"},
    {"code": "000270.KS", "name": "기아",       "market": "KR"},
    {"code": "105560.KS", "name": "KB금융",     "market": "KR"},
    {"code": "055550.KS", "name": "신한지주",   "market": "KR"},
    {"code": "032830.KS", "name": "삼성생명",   "market": "KR"},
    {"code": "096770.KS", "name": "SK이노베이션", "market": "KR"},
    {"code": "034730.KS", "name": "SK",         "market": "KR"},
    {"code": "017670.KS", "name": "SK텔레콤",  "market": "KR"},
    {"code": "030200.KS", "name": "KT",         "market": "KR"},
    {"code": "003550.KS", "name": "LG",         "market": "KR"},
    {"code": "009540.KS", "name": "HD한국조선해양", "market": "KR"},
    {"code": "012330.KS", "name": "현대모비스", "market": "KR"},
]

US_STOCK_POOL = [
    {"code": "AAPL",  "name": "Apple",      "market": "US"},
    {"code": "MSFT",  "name": "Microsoft",  "market": "US"},
    {"code": "NVDA",  "name": "NVIDIA",     "market": "US"},
    {"code": "AMZN",  "name": "Amazon",     "market": "US"},
    {"code": "GOOGL", "name": "Alphabet",   "market": "US"},
    {"code": "META",  "name": "Meta",       "market": "US"},
    {"code": "TSLA",  "name": "Tesla",      "market": "US"},
    {"code": "BRK-B", "name": "Berkshire",  "market": "US"},
    {"code": "JPM",   "name": "JPMorgan",   "market": "US"},
    {"code": "V",     "name": "Visa",       "market": "US"},
    {"code": "JNJ",   "name": "J&J",        "market": "US"},
    {"code": "WMT",   "name": "Walmart",    "market": "US"},
    {"code": "XOM",   "name": "ExxonMobil", "market": "US"},
    {"code": "UNH",   "name": "UnitedHealth","market": "US"},
    {"code": "MA",    "name": "Mastercard", "market": "US"},
    {"code": "PG",    "name": "P&G",        "market": "US"},
    {"code": "HD",    "name": "Home Depot", "market": "US"},
    {"code": "CVX",   "name": "Chevron",    "market": "US"},
    {"code": "LLY",   "name": "Eli Lilly",  "market": "US"},
    {"code": "AVGO",  "name": "Broadcom",   "market": "US"},
]
