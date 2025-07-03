import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot 設定
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# 資料庫設定
DATABASE_PATH = 'stock_bot.db'

# 股票資料來源設定
STOCK_DATA_SOURCE = 'yfinance'  # 或 'twse' 用於台股

# 更新頻率設定 (秒)
PRICE_UPDATE_INTERVAL = 60  # 1分鐘更新一次
ALERT_CHECK_INTERVAL = 30   # 30秒檢查一次警報

# 技術指標設定
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BOLLINGER_PERIOD = 20
BOLLINGER_STD = 2

# 警報設定
PRICE_CHANGE_THRESHOLD = 0.05  # 5% 價格變動
VOLUME_SPIKE_THRESHOLD = 2.0   # 成交量放大2倍
VOLATILITY_THRESHOLD = 0.03    # 3% 波動率

# 投資策略設定
INVESTMENT_PERSONALITIES = {
    '打工型交易者': {
        'description': '適合短線操作，關注技術面',
        'indicators': ['RSI', 'MACD', 'BOLLINGER'],
        'timeframe': '1d',
        'risk_level': 'medium'
    },
    '上班族型交易者': {
        'description': '平衡型投資，技術面+基本面',
        'indicators': ['RSI', 'MA', 'VOLUME'],
        'timeframe': '1d',
        'risk_level': 'medium-low'
    },
    '老闆型交易者': {
        'description': '長線投資，重視基本面',
        'indicators': ['MA', 'VOLUME', 'TREND'],
        'timeframe': '1wk',
        'risk_level': 'low'
    },
    '成長型投資者': {
        'description': '高風險高報酬，關注成長股',
        'indicators': ['RSI', 'MACD', 'VOLUME'],
        'timeframe': '1d',
        'risk_level': 'high'
    },
    '被動型投資者': {
        'description': '指數投資，定期定額',
        'indicators': ['MA', 'TREND'],
        'timeframe': '1mo',
        'risk_level': 'very-low'
    }
} 