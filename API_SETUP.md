# API 設定說明

這個股票機器人支援多個免費 API 來源，按優先順序使用：

## 主要來源（免費）
- **Yahoo Finance**: 主要資料來源，無需 API key

## 免費備用來源
- **Free Stock API**: 免費備用，無需 API key
- **World Trading Data**: 免費版，使用 demo token

## 環境變數設定

在 `.env` 文件中添加：

```env
# 主要設定
TELEGRAM_TOKEN=your_telegram_token

# 可選的免費 API key（用於備用資料來源）
WORLDTRADINGDATA_API_KEY=demo
```

## API 使用限制

- **Yahoo Finance**: 無限制，但可能有速率限制
- **Free Stock API**: 免費版有請求限制
- **World Trading Data**: 免費版每月 1000 次請求

## 故障排除

如果所有 API 都失敗，機器人會返回 `None` 而不是模擬資料，確保資料的準確性。

系統會自動：
1. 實施速率限制避免超過 API 限制
2. 快取資料減少 API 請求
3. 重試機制處理暫時性錯誤
4. 按優先順序嘗試不同 API 來源

## 免費 API 優勢

✅ **完全免費** - 無需註冊或付費
✅ **無 API key 要求** - 除了 World Trading Data 的 demo token
✅ **穩定可靠** - 多個備用來源確保服務可用性
✅ **即時資料** - 提供最新的股票價格資訊 