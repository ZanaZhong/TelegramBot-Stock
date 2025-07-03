# Railway 部署指南

## 步驟 1: 註冊 Railway 帳號
1. 前往 https://railway.app/
2. 使用 GitHub 帳號登入

## 步驟 2: 連接 GitHub 倉庫
1. 點擊 "New Project"
2. 選擇 "Deploy from GitHub repo"
3. 選擇你的倉庫：`ZanaZhong/TelegramBot-Stock`

## 步驟 3: 設定環境變數
在 Railway 專案設定中，添加以下環境變數：

### 必要變數
- `TELEGRAM_TOKEN`: 你的 Telegram Bot Token
- `PORT`: 設定為 `8000`

### 可選變數
- `LOG_LEVEL`: 設定為 `INFO`
- `DATABASE_URL`: 如果使用外部資料庫（可選）

## 步驟 4: 部署設定
1. Railway 會自動檢測到 `Procfile`
2. 確保 Python 版本設定正確（runtime.txt）
3. 點擊 "Deploy" 開始部署

## 步驟 5: 取得 Webhook URL
部署完成後：
1. 在 Railway 專案頁面找到你的應用 URL
2. 格式類似：`https://your-app-name.railway.app`
3. 這個 URL 將用作 Telegram Webhook

## 步驟 6: 設定 Webhook
在部署完成後，需要設定 Telegram Webhook：

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-app-name.railway.app/webhook"}'
```

## 注意事項
- Railway 免費版每月有使用限制
- 確保 `.env` 檔案不要提交到 Git（已在 .gitignore 中）
- 所有敏感資訊都應該設定為環境變數
- 部署後記得測試 Bot 功能

## 故障排除
1. 如果部署失敗，檢查 requirements.txt 格式
2. 確保所有依賴都正確列出
3. 檢查環境變數是否正確設定
4. 查看 Railway 的部署日誌 