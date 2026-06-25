DOMESTIC_STOCK_POOL = [
    {"code": "005930", "name": "삼성전자",       "yf_code": "005930.KS"},
    {"code": "000660", "name": "SK하이닉스",      "yf_code": "000660.KS"},
    {"code": "373220", "name": "LG에너지솔루션",  "yf_code": "373220.KS"},
    {"code": "207940", "name": "삼성바이오로직스", "yf_code": "207940.KS"},
    {"code": "005380", "name": "현대차",          "yf_code": "005380.KS"},
    {"code": "035420", "name": "NAVER",           "yf_code": "035420.KS"},
    {"code": "035720", "name": "카카오",           "yf_code": "035720.KS"},
    {"code": "000270", "name": "기아",            "yf_code": "000270.KS"},
    {"code": "005490", "name": "POSCO홀딩스",     "yf_code": "005490.KS"},
    {"code": "068270", "name": "셀트리온",         "yf_code": "068270.KS"},
    {"code": "006400", "name": "삼성SDI",         "yf_code": "006400.KS"},
    {"code": "105560", "name": "KB금융",          "yf_code": "105560.KS"},
    {"code": "055550", "name": "신한지주",         "yf_code": "055550.KS"},
    {"code": "086790", "name": "하나금융지주",     "yf_code": "086790.KS"},
    {"code": "051910", "name": "LG화학",          "yf_code": "051910.KS"},
    {"code": "066570", "name": "LG전자",          "yf_code": "066570.KS"},
    {"code": "096770", "name": "SK이노베이션",     "yf_code": "096770.KS"},
    {"code": "034730", "name": "SK",              "yf_code": "034730.KS"},
    {"code": "015760", "name": "한국전력",         "yf_code": "015760.KS"},
    {"code": "003550", "name": "LG",              "yf_code": "003550.KS"},
]

US_STOCK_POOL = [
    {"code": "AAPL", "name": "Apple"},
    {"code": "MSFT", "name": "Microsoft"},
    {"code": "GOOGL", "name": "Alphabet"},
    {"code": "AMZN", "name": "Amazon"},
    {"code": "META", "name": "Meta"},
    {"code": "NVDA", "name": "NVIDIA"},
    {"code": "TSLA", "name": "Tesla"},
    {"code": "JPM", "name": "JPMorgan"},
    {"code": "JNJ", "name": "Johnson & Johnson"},
    {"code": "V", "name": "Visa"},
    {"code": "MA", "name": "Mastercard"},
    {"code": "UNH", "name": "UnitedHealth"},
    {"code": "HD", "name": "Home Depot"},
    {"code": "BAC", "name": "Bank of America"},
    {"code": "NFLX", "name": "Netflix"},
    {"code": "AMD", "name": "AMD"},
    {"code": "INTC", "name": "Intel"},
    {"code": "DIS", "name": "Disney"},
    {"code": "PYPL", "name": "PayPal"},
    {"code": "SHOP", "name": "Shopify"},
]

# 수수료
KR_BUY_FEE = 0.00015
KR_SELL_FEE = 0.0023
US_BUY_FEE = 0.0025
US_SELL_FEE = 0.0025

# ── 스캘핑 파라미터 ──
# KR: 수수료 0.245% → 순수익 목표 ~0.75%
SCALP_TAKE_PROFIT_KR = 0.010   # +1.0%
SCALP_TAKE_PROFIT_US = 0.015   # +1.5% (US 수수료 0.5%)
SCALP_STOP_LOSS      = -0.005  # -0.5% (손절:익절 = 1:2)

# ── 스윙 파라미터 ──
SWING_TAKE_PROFIT = 0.030   # +3.0%
SWING_STOP_LOSS   = -0.020  # -2.0%

# ── 변동성 분류 임계값 ──
SCALP_ATR_THRESHOLD   = 0.020  # ATR/가격 > 2% → 스캘핑
SCALP_RANGE_THRESHOLD = 0.025  # 일봉 고저폭 > 2.5% → 스캘핑

# ── 일반 파라미터 ──
DEFAULT_INITIAL_CAPITAL = 10_000_000
MAX_POSITIONS       = 8           # 스캘핑 포함 최대 보유
MAX_POSITION_RATIO  = 0.15        # 한 종목 최대 15% (더 많은 분산)
DAILY_TARGET_RATE   = 0.020       # 일일 목표 수익률 2%
SCAN_INTERVAL_MINUTES = 3         # 스캘핑용 빠른 스캔
DEFAULT_EXCHANGE_RATE = 1350

# 하위호환
STOP_LOSS_RATE   = SWING_STOP_LOSS
TAKE_PROFIT_RATE = SWING_TAKE_PROFIT
