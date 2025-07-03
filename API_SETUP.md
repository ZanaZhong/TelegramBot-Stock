# API 設定說明

這個股票機器人支援多個 API 來源，按優先順序使用：

## 主要來源（免費）
- **Yahoo Finance**: 主要資料來源，無需 API key

## 免費備用來源
- **Free Stock API**: 免費備用，無需 API key
- **World Trading Data**: 免費版，使用 demo token

## 付費備用來源（可選）
如果你想要更穩定的資料來源，可以申請以下 API keys：

### Alpha Vantage
1. 前往 https://www.alphavantage.co/
2. 註冊免費帳號
3. 取得 API key
4. 設定環境變數：`ALPHA_VANTAGE_API_KEY=your_key_here`

### Finnhub
1. 前往 https://finnhub.io/
2. 註冊免費帳號
3. 取得 API key
4. 設定環境變數：`FINNHUB_API_KEY=your_key_here`

### Polygon
1. 前往 https://polygon.io/
2. 註冊免費帳號
3. 取得 API key
4. 設定環境變數：`POLYGON_API_KEY=your_key_here`

### World Trading Data（付費版）
1. 前往 https://www.worldtradingdata.com/
2. 註冊帳號
3. 取得 API key
4. 設定環境變數：`WORLDTRADINGDATA_API_KEY=your_key_here`

## 環境變數設定

在 `.env` 文件中添加：

```env
# 主要設定
TELEGRAM_TOKEN=your_telegram_token

# 可選的 API keys（用於備用資料來源）
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FINNHUB_API_KEY=your_finnhub_key
POLYGON_API_KEY=your_polygon_key
WORLDTRADINGDATA_API_KEY=your_worldtradingdata_key
```

## API 使用限制

- **Yahoo Finance**: 無限制，但可能有速率限制
- **Free Stock API**: 免費版有請求限制
- **World Trading Data**: 免費版每月 1000 次請求
- **Alpha Vantage**: 免費版每分鐘 5 次請求
- **Finnhub**: 免費版每分鐘 60 次請求
- **Polygon**: 免費版每月 5 次請求

## 故障排除

如果所有 API 都失敗，機器人會返回 `None` 而不是模擬資料，確保資料的準確性。

系統會自動：
1. 實施速率限制避免超過 API 限制
2. 快取資料減少 API 請求
3. 重試機制處理暫時性錯誤
4. 按優先順序嘗試不同 API 來源 