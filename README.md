# 📈 Telegram 股票追蹤機器人

一個功能完整的 Telegram 股票追蹤機器人，參考 CMoney 付費平台的投資策略概念，提供即時股價查詢、技術分析、投資策略建議和價格警報功能。

## 🚀 主要功能

### 📊 股票查詢與分析
- **即時股價查詢** - 支援美股、台股等多個市場
- **技術分析** - RSI、MACD、布林通道、移動平均線等指標
- **圖表生成** - 價格走勢圖、技術指標圖、多股票比較圖
- **投資策略建議** - 根據投資人格提供個人化建議

### ⭐ 自選股票追蹤
- **追蹤清單管理** - 新增/移除感興趣的股票
- **即時價格更新** - 自動追蹤價格變動
- **波動率分析** - 計算並監控股票波動情況

### 🔔 智能警報系統
- **價格突破警報** - 設定價格上下限
- **變動百分比警報** - 監控價格變動幅度
- **成交量異常警報** - 檢測成交量暴增
- **波動率警報** - 監控異常波動

### 🎯 投資策略系統
參考 CMoney 的五種投資人格：
1. **打工型交易者** - 短線操作，關注技術面
2. **上班族型交易者** - 平衡投資，技術面+基本面
3. **老闆型交易者** - 長線投資，重視基本面
4. **成長型投資者** - 高風險高報酬，關注成長股
5. **被動型投資者** - 指數投資，定期定額

## 📋 使用指南

### 基本命令
```
/start - 開始使用機器人
/help - 查看所有命令說明
/stock AAPL - 查詢股票資訊
/price AAPL - 即時股價
/chart AAPL - 生成股票圖表
/compare AAPL MSFT GOOGL - 多股票比較
```

### 追蹤功能
```
/watchlist - 查看追蹤清單
/add AAPL - 新增到追蹤清單
/remove AAPL - 移除追蹤
```

### 投資策略
```
/personality - 投資人格測驗
/strategy AAPL - 個人化策略建議
```

### 警報設定
```
/alerts - 查看警報設定
/alert_price AAPL 150 - 設定價格突破警報
/alert_change AAPL 5 - 設定5%變動警報
```

## 🛠️ 安裝與部署

### 本地開發

1. **克隆專案**
```bash
git clone https://github.com/your-username/telegram-stock-bot.git
cd telegram-stock-bot
```

2. **建立虛擬環境**
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows
```

3. **安裝依賴**
```bash
pip install -r requirements.txt
```

4. **設定環境變數**
```bash
# 建立 .env 檔案
echo "TELEGRAM_TOKEN=your_bot_token_here" > .env
```

5. **啟動機器人**
```bash
python3 bot.py
```

### 雲端部署

#### Railway 部署
1. Fork 此專案到你的 GitHub
2. 註冊 [Railway](https://railway.app/)
3. 連接 GitHub 倉庫
4. 設定環境變數 `TELEGRAM_TOKEN`
5. 自動部署完成

#### Render 部署
1. Fork 此專案到你的 GitHub
2. 註冊 [Render](https://render.com/)
3. 建立新的 Web Service
4. 連接 GitHub 倉庫
5. 設定環境變數和啟動命令

## 📁 專案結構

```
TelegramBot-Stock/
├── bot.py              # 主要機器人邏輯
├── config.py           # 設定檔
├── database.py         # 資料庫管理
├── stock_data.py       # 股票資料獲取與分析
├── alert_system.py     # 警報系統
├── chart_generator.py  # 圖表生成
├── requirements.txt    # Python 依賴
├── .env               # 環境變數 (不提交到 Git)
├── .gitignore         # Git 忽略檔案
└── README.md          # 專案說明
```

## 🔧 技術架構

### 核心技術
- **Python 3.8+** - 主要開發語言
- **python-telegram-bot** - Telegram Bot API
- **yfinance** - 股票資料來源
- **pandas** - 資料處理
- **matplotlib/seaborn** - 圖表生成
- **SQLite** - 本地資料庫
- **ta** - 技術指標計算

### 資料來源
- **Yahoo Finance** - 股票價格和基本資訊
- **Telegram Bot API** - 機器人平台

### 部署選項
- **本地部署** - 適合個人使用
- **Railway** - 免費雲端部署
- **Render** - 免費雲端部署
- **Heroku** - 付費雲端部署
- **VPS** - 自架伺服器

## 🎨 圖表功能

### 單股票圖表
- 價格走勢圖（收盤價、開盤價、高低價）
- 移動平均線（20日、50日）
- 成交量分析
- 技術指標圖（RSI、MACD、布林通道）

### 多股票比較
- 標準化價格比較
- 相關性熱力圖
- 表現對比分析

## 🔒 安全性

- 環境變數保護敏感資訊
- 資料庫本地儲存
- 用戶資料加密
- 錯誤處理和日誌記錄

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

### 開發流程
1. Fork 專案
2. 建立功能分支
3. 提交變更
4. 建立 Pull Request

## 📄 授權

MIT License - 詳見 [LICENSE](LICENSE) 檔案

## 🙏 致謝

- [CMoney](https://www.cmoney.tw/) - 投資策略概念參考
- [Yahoo Finance](https://finance.yahoo.com/) - 股票資料來源
- [python-telegram-bot](https://python-telegram-bot.org/) - Telegram Bot 框架

## 📞 聯絡方式

如有問題或建議，請透過以下方式聯絡：
- GitHub Issues
- Email: your-email@example.com

---

⭐ 如果這個專案對你有幫助，請給個 Star！ 