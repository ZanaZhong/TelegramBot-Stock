# Render 免費部署指南

## 🆓 為什麼選擇 Render？
- **完全免費**：每月 750 小時免費額度
- **簡單易用**：類似 Railway 的介面
- **自動部署**：連接 GitHub 自動部署
- **支援 Python**：原生支援 Python 應用

## 📋 部署步驟

### 步驟 1: 註冊 Render 帳號
1. 前往 https://render.com/
2. 點擊 "Get Started for Free"
3. 使用 GitHub 帳號登入

### 步驟 2: 建立新服務
1. 點擊 "New +"
2. 選擇 "Web Service"
3. 連接你的 GitHub 帳號
4. 選擇倉庫：`ZanaZhong/TelegramBot-Stock`

### 步驟 3: 設定服務
- **Name**: `telegram-stock-bot`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python bot.py`

### 步驟 4: 設定環境變數
在 "Environment Variables" 區塊添加：

**必要變數：**
- `TELEGRAM_TOKEN`: 你的 Telegram Bot Token
- `PORT`: `8000`

**可選變數：**
- `LOG_LEVEL`: `INFO`

### 步驟 5: 部署
1. 點擊 "Create Web Service"
2. 等待部署完成（約 2-5 分鐘）
3. 部署完成後會得到一個 URL，格式如：`https://telegram-stock-bot.onrender.com`

### 步驟 6: 設定 Telegram Webhook
部署完成後，設定 webhook：

**方法 1：瀏覽器訪問**
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://telegram-stock-bot.onrender.com/webhook
```

**方法 2：使用 curl**
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://telegram-stock-bot.onrender.com/webhook"}'
```

## ⚠️ 重要注意事項

### 免費版限制
- **每月 750 小時**：足夠 24/7 運行
- **15 分鐘無活動休眠**：首次請求會重新啟動（約 30 秒）
- **512MB RAM**：足夠運行 Bot
- **共享 CPU**：適合輕量級應用

### 最佳實踐
1. **設定健康檢查**：確保服務正常運行
2. **監控日誌**：定期檢查錯誤日誌
3. **備份資料**：重要資料要備份
4. **測試功能**：部署後測試所有功能

## 🔧 故障排除

### 常見問題
1. **部署失敗**：檢查 requirements.txt 格式
2. **環境變數錯誤**：確認 TELEGRAM_TOKEN 正確
3. **服務無法啟動**：檢查日誌錯誤訊息
4. **Webhook 設定失敗**：確認 URL 正確

### 查看日誌
1. 在 Render 儀表板點擊你的服務
2. 點擊 "Logs" 標籤
3. 查看實時日誌和錯誤訊息

## 🎉 完成！
部署完成後，你的 Telegram Bot 就可以在 Render 上免費運行了！

### 測試 Bot
1. 在 Telegram 中找到你的 Bot
2. 發送 `/start` 命令
3. 測試各種功能是否正常

### 監控服務
- 定期檢查 Render 儀表板
- 監控服務狀態和日誌
- 確保 Bot 正常回應 