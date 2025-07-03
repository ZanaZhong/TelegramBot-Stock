import logging
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from database import Database
from stock_data import StockDataManager
from alert_system import AlertSystem
from chart_generator import ChartGenerator
from config import TELEGRAM_TOKEN, INVESTMENT_PERSONALITIES
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io
from datetime import datetime, timedelta

# 設定日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 環境變數設定
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', TELEGRAM_TOKEN)
PORT = int(os.getenv('PORT', 8000))
WEBHOOK_URL = os.getenv('WEBHOOK_URL', None)

class StockBot:
    def __init__(self):
        self.db = Database()
        self.stock_manager = StockDataManager()
        self.chart_generator = ChartGenerator()
        self.alert_system = None
        self.application = None
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """開始命令"""
        user = update.effective_user
        
        # 新增用戶到資料庫
        self.db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        welcome_message = f"""
🎉 歡迎使用股票追蹤 Bot！

👋 你好 {user.first_name}！

📊 **主要功能：**
• 📈 即時股價查詢
• ⭐ 自選股票追蹤
• 🔔 價格警報設定
• 📊 技術分析
• 🎯 投資策略建議

💡 **快速開始：**
/help - 查看所有命令
/stock AAPL - 查詢股票
/watchlist - 管理追蹤清單
/alerts - 設定警報
/personality - 投資人格測驗

開始你的投資之旅吧！ 🚀
        """
        
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """幫助命令"""
        help_text = """
📚 **股票 Bot 使用指南**

🔍 **查詢功能：**
/stock <代碼> - 查詢股票資訊 (例: /stock AAPL)
/price <代碼> - 即時股價
/analysis <代碼> - 技術分析

📈 **圖表功能：**
/chart <代碼> - 生成股票圖表 (價格走勢 + 技術指標)
/compare <代碼1> <代碼2> ... - 多股票比較圖表 (最多5支)

⭐ **追蹤功能：**
/watchlist - 查看追蹤清單
/add <代碼> - 新增到追蹤清單
/remove <代碼> - 移除追蹤

🔔 **警報功能：**
/alerts - 查看警報設定
/alert_price <代碼> <價格> - 設定價格警報
/alert_change <代碼> <百分比> - 設定變動警報

🎯 **投資策略：**
/personality - 投資人格測驗
/strategy <代碼> - 策略建議
/portfolio - 投資組合分析

⚙️ **設定：**
/settings - 個人設定
/help - 顯示此幫助

💡 **圖表功能特色：**
• 📊 價格走勢圖：收盤價、開盤價、高低價範圍
• 📈 移動平均線：20日、50日均線
• 📊 技術指標：RSI、MACD、布林通道
• 📈 成交量分析：顏色區分漲跌
• 🔥 相關性熱力圖：多股票比較
        """
        
        await update.message.reply_text(help_text)
    
    async def stock_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """股票查詢命令"""
        if not context.args:
            await update.message.reply_text("請輸入股票代碼，例如: /stock AAPL")
            return
        
        symbol = context.args[0].upper()
        
        # 顯示載入訊息
        loading_msg = await update.message.reply_text("🔍 正在查詢股票資訊...")
        
        try:
            # 取得股票資訊
            stock_info = self.stock_manager.get_stock_info(symbol)
            current_price = self.stock_manager.get_current_price(symbol)
            
            if not stock_info or not current_price:
                await loading_msg.edit_text(f"❌ 無法取得 {symbol} 的資訊，請檢查股票代碼是否正確")
                return
            
            # 格式化訊息
            message = f"""
📊 **{stock_info['name']} ({symbol})**

💰 **即時價格:**
• 當前價格: ${current_price['price']:.2f}
• 漲跌幅: {current_price['change_percent']:+.2f}%
• 成交量: {current_price['volume']:,}

📈 **基本資訊:**
• 產業: {stock_info['sector']}
• 市值: ${stock_info['market_cap']:,.0f}
• P/E 比: {stock_info['pe_ratio']:.2f}
• 股息率: {stock_info['dividend_yield']*100:.2f}%

⏰ 更新時間: {current_price['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            # 建立按鈕
            keyboard = [
                [
                    InlineKeyboardButton("📊 技術分析", callback_data=f"analysis_{symbol}"),
                    InlineKeyboardButton("⭐ 加入追蹤", callback_data=f"add_watch_{symbol}")
                ],
                [
                    InlineKeyboardButton("🔔 設定警報", callback_data=f"alert_{symbol}"),
                    InlineKeyboardButton("📈 查看圖表", callback_data=f"chart_{symbol}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await loading_msg.edit_text(message, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error in stock command: {e}")
            await loading_msg.edit_text("❌ 查詢股票時發生錯誤")
    
    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """即時股價命令"""
        if not context.args:
            await update.message.reply_text("請輸入股票代碼，例如: /price AAPL")
            return
        
        symbol = context.args[0].upper()
        
        try:
            current_price = self.stock_manager.get_current_price(symbol)
            
            if not current_price:
                await update.message.reply_text(f"❌ 無法取得 {symbol} 的價格資訊")
                return
            
            # 決定表情符號
            if current_price['change_percent'] > 0:
                emoji = "📈"
            elif current_price['change_percent'] < 0:
                emoji = "📉"
            else:
                emoji = "➡️"
            
            message = f"""
{emoji} **{symbol} 即時價格**

💰 **${current_price['price']:.2f}**
{current_price['change_percent']:+.2f}% ({current_price['change']:+.2f})

📊 **今日交易:**
• 開盤: ${current_price['open']:.2f}
• 最高: ${current_price['high']:.2f}
• 最低: ${current_price['low']:.2f}
• 成交量: {current_price['volume']:,}
            """
            
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Error in price command: {e}")
            await update.message.reply_text("❌ 查詢價格時發生錯誤")
    
    async def watchlist_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """追蹤清單命令"""
        user_id = update.effective_user.id
        watchlist = self.db.get_user_watchlist(user_id)
        
        if not watchlist:
            await update.message.reply_text("您目前沒有追蹤任何股票。\n使用 /add <代碼> 來新增股票到追蹤清單")
            return
        
        message = "⭐ **您的追蹤清單:**\n\n"
        
        for symbol, company_name, added_at in watchlist:
            # 取得即時價格
            current_price = self.stock_manager.get_current_price(symbol)
            if current_price:
                change_emoji = "📈" if current_price['change_percent'] > 0 else "📉" if current_price['change_percent'] < 0 else "➡️"
                message += f"{change_emoji} **{symbol}** - ${current_price['price']:.2f} ({current_price['change_percent']:+.2f}%)\n"
            else:
                message += f"❓ **{symbol}** - 無法取得價格\n"
        
        # 建立按鈕
        keyboard = [
            [InlineKeyboardButton("🔄 重新整理", callback_data="refresh_watchlist")],
            [InlineKeyboardButton("➕ 新增股票", callback_data="add_stock")],
            [InlineKeyboardButton("🗑️ 管理清單", callback_data="manage_watchlist")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def add_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """新增追蹤命令"""
        if not context.args:
            await update.message.reply_text("請輸入股票代碼，例如: /add AAPL")
            return
        
        user_id = update.effective_user.id
        symbol = context.args[0].upper()
        
        try:
            # 驗證股票代碼
            stock_info = self.stock_manager.get_stock_info(symbol)
            if not stock_info:
                await update.message.reply_text(f"❌ 無效的股票代碼: {symbol}")
                return
            
            # 新增到追蹤清單
            success = self.db.add_stock_to_watchlist(user_id, symbol, stock_info['name'])
            
            if success:
                await update.message.reply_text(f"✅ 已將 {symbol} ({stock_info['name']}) 新增到追蹤清單")
            else:
                await update.message.reply_text(f"ℹ️ {symbol} 已在追蹤清單中")
                
        except Exception as e:
            logger.error(f"Error in add command: {e}")
            await update.message.reply_text("❌ 新增追蹤時發生錯誤")
    
    async def remove_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """移除追蹤命令"""
        if not context.args:
            await update.message.reply_text("請輸入股票代碼，例如: /remove AAPL")
            return
        
        user_id = update.effective_user.id
        symbol = context.args[0].upper()
        
        try:
            self.db.remove_stock_from_watchlist(user_id, symbol)
            await update.message.reply_text(f"✅ 已從追蹤清單移除 {symbol}")
            
        except Exception as e:
            logger.error(f"Error in remove command: {e}")
            await update.message.reply_text("❌ 移除追蹤時發生錯誤")
    
    async def alerts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """警報命令"""
        user_id = update.effective_user.id
        alert_summary = self.alert_system.get_user_alert_summary(user_id)
        
        # 建立按鈕
        keyboard = [
            [InlineKeyboardButton("➕ 新增警報", callback_data="add_alert")],
            [InlineKeyboardButton("🗑️ 管理警報", callback_data="manage_alerts")],
            [InlineKeyboardButton("📊 警報統計", callback_data="alert_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(alert_summary, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def personality_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """投資人格測驗命令"""
        message = """
🎯 **投資人格測驗**

選擇最符合你的投資風格：

1️⃣ **打工型交易者** - 短線操作，關注技術面
2️⃣ **上班族型交易者** - 平衡投資，技術面+基本面  
3️⃣ **老闆型交易者** - 長線投資，重視基本面
4️⃣ **成長型投資者** - 高風險高報酬，關注成長股
5️⃣ **被動型投資者** - 指數投資，定期定額

請選擇你的投資人格：
        """
        
        keyboard = [
            [InlineKeyboardButton("1️⃣ 打工型交易者", callback_data="personality_打工型交易者")],
            [InlineKeyboardButton("2️⃣ 上班族型交易者", callback_data="personality_上班族型交易者")],
            [InlineKeyboardButton("3️⃣ 老闆型交易者", callback_data="personality_老闆型交易者")],
            [InlineKeyboardButton("4️⃣ 成長型投資者", callback_data="personality_成長型投資者")],
            [InlineKeyboardButton("5️⃣ 被動型投資者", callback_data="personality_被動型投資者")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup)
    
    async def strategy_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """策略建議命令"""
        if not context.args:
            await update.message.reply_text("請輸入股票代碼，例如: /strategy AAPL")
            return
        
        symbol = context.args[0].upper()
        user_id = update.effective_user.id
        
        # 取得用戶投資人格
        user = self.db.get_user(user_id)
        personality = user[4] if user else '上班族型交易者'
        
        loading_msg = await update.message.reply_text("🎯 正在分析投資策略...")
        
        try:
            analysis = self.stock_manager.get_stock_analysis(symbol, personality)
            
            if not analysis:
                await loading_msg.edit_text(f"❌ 無法分析 {symbol} 的策略")
                return
            
            # 修正 f-string 條件語法
            rsi_str = f"{analysis['technical_indicators']['rsi']:.1f}" if analysis['technical_indicators']['rsi'] is not None else 'N/A'
            macd_str = f"{analysis['technical_indicators']['macd']:.3f}" if analysis['technical_indicators']['macd'] is not None else 'N/A'
            vol_str = f"{analysis['technical_indicators']['volatility']*100:.1f}%" if analysis['technical_indicators']['volatility'] is not None else 'N/A'
            
            message = f"""
🎯 **{symbol} 投資策略分析**

👤 **投資人格:** {personality}
💰 **當前價格:** ${analysis['current_price']:.2f} ({analysis['change_percent']:+.2f}%)
⚠️ **風險等級:** {analysis['risk_level']}

📊 **技術指標:**
• RSI: {rsi_str}
• MACD: {macd_str}
• 波動率: {vol_str}

📈 **投資信號:**
"""
            
            for signal in analysis['signals']:
                message += f"• {signal}\n"
            
            message += f"\n💡 **建議:** {analysis['recommendation']}"
            
            await loading_msg.edit_text(message)
            
        except Exception as e:
            logger.error(f"Error in strategy command: {e}")
            await loading_msg.edit_text("❌ 分析策略時發生錯誤")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """按鈕回調處理"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith("analysis_"):
            symbol = data.split("_")[1]
            await self.handle_analysis_callback(query, symbol)
        
        elif data.startswith("add_watch_"):
            symbol = data.split("_")[2]
            await self.handle_add_watch_callback(query, symbol)
        
        elif data.startswith("alert_"):
            symbol = data.split("_")[1]
            await self.handle_alert_callback(query, symbol)
        
        elif data.startswith("chart_"):
            symbol = data.split("_")[1]
            await self.handle_chart_callback(query, symbol)
        
        elif data.startswith("personality_"):
            personality = data.split("_", 1)[1]
            await self.handle_personality_callback(query, personality)
        
        elif data == "refresh_watchlist":
            await self.handle_refresh_watchlist_callback(query)
        
        elif data == "add_stock":
            await self.handle_add_stock_callback(query)
    
    async def handle_analysis_callback(self, query, symbol):
        """處理技術分析回調"""
        user_id = query.from_user.id
        user = self.db.get_user(user_id)
        personality = user[4] if user else '上班族型交易者'
        
        await query.edit_message_text("📊 正在進行技術分析...")
        
        try:
            analysis = self.stock_manager.get_stock_analysis(symbol, personality)
            
            if not analysis:
                await query.edit_message_text(f"❌ 無法分析 {symbol}")
                return
            
            # 修正 f-string 條件語法
            rsi_str = f"{analysis['technical_indicators']['rsi']:.1f}" if analysis['technical_indicators']['rsi'] is not None else 'N/A'
            macd_str = f"{analysis['technical_indicators']['macd']:.3f}" if analysis['technical_indicators']['macd'] is not None else 'N/A'
            bb_str = f"{analysis['technical_indicators']['bb_position']:.2f}" if analysis['technical_indicators']['bb_position'] is not None else 'N/A'
            vol_str = f"{analysis['technical_indicators']['volume_ratio']:.1f}" if analysis['technical_indicators']['volume_ratio'] is not None else 'N/A'
            vola_str = f"{analysis['technical_indicators']['volatility']*100:.1f}%" if analysis['technical_indicators']['volatility'] is not None else 'N/A'
            
            message = f"""
📊 **{symbol} 技術分析**

💰 **價格:** ${analysis['current_price']:.2f} ({analysis['change_percent']:+.2f}%)

📈 **技術指標:**
• RSI: {rsi_str}
• MACD: {macd_str}
• 布林位置: {bb_str}
• 均線趨勢: {analysis['technical_indicators']['ma_trend']}
• 成交量比: {vol_str}
• 波動率: {vola_str}

🎯 **投資信號:**
"""
            
            for signal in analysis['signals']:
                message += f"• {signal}\n"
            
            keyboard = [
                [InlineKeyboardButton("🔔 設定警報", callback_data=f"alert_{symbol}")],
                [InlineKeyboardButton("📈 查看圖表", callback_data=f"chart_{symbol}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error in analysis callback: {e}")
            await query.edit_message_text("❌ 技術分析時發生錯誤")
    
    async def handle_add_watch_callback(self, query, symbol):
        """處理新增追蹤回調"""
        user_id = query.from_user.id
        
        try:
            stock_info = self.stock_manager.get_stock_info(symbol)
            if not stock_info:
                await query.edit_message_text(f"❌ 無效的股票代碼: {symbol}")
                return
            
            success = self.db.add_stock_to_watchlist(user_id, symbol, stock_info['name'])
            
            if success:
                await query.edit_message_text(f"✅ 已將 {symbol} 新增到追蹤清單")
            else:
                await query.edit_message_text(f"ℹ️ {symbol} 已在追蹤清單中")
                
        except Exception as e:
            logger.error(f"Error in add watch callback: {e}")
            await query.edit_message_text("❌ 新增追蹤時發生錯誤")
    
    async def handle_alert_callback(self, query, symbol):
        """處理警報回調"""
        message = f"""
🔔 **設定 {symbol} 警報**

選擇警報類型：

💰 **價格警報**
• 價格突破上限
• 價格跌破下限

⚡ **變動警報**
• 價格變動百分比
• 成交量放大

🌊 **波動警報**
• 波動率異常
        """
        
        keyboard = [
            [InlineKeyboardButton("💰 價格突破", callback_data=f"alert_price_high_{symbol}")],
            [InlineKeyboardButton("💰 價格跌破", callback_data=f"alert_price_low_{symbol}")],
            [InlineKeyboardButton("⚡ 價格變動", callback_data=f"alert_change_{symbol}")],
            [InlineKeyboardButton("📊 成交量", callback_data=f"alert_volume_{symbol}")],
            [InlineKeyboardButton("🌊 波動率", callback_data=f"alert_volatility_{symbol}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    async def handle_personality_callback(self, query, personality):
        """處理投資人格回調"""
        user_id = query.from_user.id
        
        try:
            self.db.update_investment_personality(user_id, personality)
            
            personality_info = INVESTMENT_PERSONALITIES.get(personality, {})
            description = personality_info.get('description', '')
            risk_level = personality_info.get('risk_level', '')
            
            message = f"""
✅ **投資人格設定完成！**

👤 **您的投資人格:** {personality}
📝 **描述:** {description}
⚠️ **風險等級:** {risk_level}

現在您可以：
• 使用 /strategy <代碼> 獲得個人化建議
• 查看符合您風格的技術分析
• 獲得量身定制的投資信號

開始您的投資之旅吧！ 🚀
            """
            
            await query.edit_message_text(message)
            
        except Exception as e:
            logger.error(f"Error in personality callback: {e}")
            await query.edit_message_text("❌ 設定投資人格時發生錯誤")
    
    async def handle_refresh_watchlist_callback(self, query):
        """處理重新整理追蹤清單回調"""
        user_id = query.from_user.id
        watchlist = self.db.get_user_watchlist(user_id)
        
        if not watchlist:
            await query.edit_message_text("您目前沒有追蹤任何股票。\n使用 /add <代碼> 來新增股票到追蹤清單")
            return
        
        message = "⭐ **您的追蹤清單:**\n\n"
        
        for symbol, company_name, added_at in watchlist:
            current_price = self.stock_manager.get_current_price(symbol)
            if current_price:
                change_emoji = "📈" if current_price['change_percent'] > 0 else "📉" if current_price['change_percent'] < 0 else "➡️"
                message += f"{change_emoji} **{symbol}** - ${current_price['price']:.2f} ({current_price['change_percent']:+.2f}%)\n"
            else:
                message += f"❓ **{symbol}** - 無法取得價格\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 重新整理", callback_data="refresh_watchlist")],
            [InlineKeyboardButton("➕ 新增股票", callback_data="add_stock")],
            [InlineKeyboardButton("🗑️ 管理清單", callback_data="manage_watchlist")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_add_stock_callback(self, query):
        """處理新增股票回調"""
        await query.edit_message_text("請使用 /add <股票代碼> 來新增股票到追蹤清單\n\n例如: /add AAPL")
    
    async def handle_chart_callback(self, query, symbol):
        """處理圖表回調"""
        await query.edit_message_text("📈 正在生成圖表...")
        
        try:
            # 生成價格走勢圖
            price_chart = self.chart_generator.generate_price_chart(symbol, period='1mo')
            
            if price_chart:
                # 發送圖片
                await query.message.reply_photo(
                    photo=price_chart,
                    caption=f"📊 {symbol} 價格走勢圖 (1個月)\n\n包含：價格走勢、移動平均線、成交量"
                )
                
                # 生成技術指標圖
                technical_chart = self.chart_generator.generate_technical_chart(symbol, period='1mo')
                
                if technical_chart:
                    await query.message.reply_photo(
                        photo=technical_chart,
                        caption=f"📈 {symbol} 技術分析圖\n\n包含：RSI、MACD、布林通道、成交量分析"
                    )
                
                # 更新原始訊息
                keyboard = [
                    [
                        InlineKeyboardButton("📊 技術分析", callback_data=f"analysis_{symbol}"),
                        InlineKeyboardButton("⭐ 加入追蹤", callback_data=f"add_watch_{symbol}")
                    ],
                    [
                        InlineKeyboardButton("🔔 設定警報", callback_data=f"alert_{symbol}"),
                        InlineKeyboardButton("📈 查看圖表", callback_data=f"chart_{symbol}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"✅ {symbol} 圖表已生成完成！\n\n上方是價格走勢圖，下方是技術分析圖。",
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(f"❌ 無法生成 {symbol} 的圖表，請稍後再試")
                
        except Exception as e:
            logger.error(f"Error in chart callback: {e}")
            await query.edit_message_text("❌ 生成圖表時發生錯誤")
    
    async def chart_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """圖表命令"""
        if not context.args:
            await update.message.reply_text("請輸入股票代碼，例如: /chart AAPL")
            return
        
        symbol = context.args[0].upper()
        
        # 顯示載入訊息
        loading_msg = await update.message.reply_text("📈 正在生成圖表...")
        
        try:
            # 生成價格走勢圖
            price_chart = self.chart_generator.generate_price_chart(symbol, period='1mo')
            
            if price_chart:
                await loading_msg.delete()
                
                # 發送圖片
                await update.message.reply_photo(
                    photo=price_chart,
                    caption=f"📊 {symbol} 價格走勢圖 (1個月)\n\n包含：價格走勢、移動平均線、成交量"
                )
                
                # 生成技術指標圖
                technical_chart = self.chart_generator.generate_technical_chart(symbol, period='1mo')
                
                if technical_chart:
                    await update.message.reply_photo(
                        photo=technical_chart,
                        caption=f"📈 {symbol} 技術分析圖\n\n包含：RSI、MACD、布林通道、成交量分析"
                    )
            else:
                await loading_msg.edit_text(f"❌ 無法生成 {symbol} 的圖表，請檢查股票代碼是否正確")
                
        except Exception as e:
            logger.error(f"Error in chart command: {e}")
            await loading_msg.edit_text("❌ 生成圖表時發生錯誤")
    
    async def compare_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """股票比較命令"""
        if len(context.args) < 2:
            await update.message.reply_text("請輸入至少兩個股票代碼，例如: /compare AAPL MSFT GOOGL")
            return
        
        symbols = [arg.upper() for arg in context.args[:5]]  # 最多比較5支股票
        
        loading_msg = await update.message.reply_text("📊 正在生成比較圖表...")
        
        try:
            # 生成比較圖
            comparison_chart = self.chart_generator.generate_comparison_chart(symbols, period='1mo')
            
            if comparison_chart:
                await loading_msg.delete()
                
                await update.message.reply_photo(
                    photo=comparison_chart,
                    caption=f"📊 股票表現比較圖\n\n比較股票: {', '.join(symbols)}\n\n標準化價格以第一天為基準 (100%)"
                )
                
                # 生成相關性熱力圖
                heatmap_chart = self.chart_generator.generate_heatmap_chart(symbols, period='1mo')
                
                if heatmap_chart:
                    await update.message.reply_photo(
                        photo=heatmap_chart,
                        caption=f"🔥 股票相關性熱力圖\n\n數值範圍：-1 (完全負相關) 到 +1 (完全正相關)"
                    )
            else:
                await loading_msg.edit_text("❌ 無法生成比較圖表，請檢查股票代碼是否正確")
                
        except Exception as e:
            logger.error(f"Error in compare command: {e}")
            await loading_msg.edit_text("❌ 生成比較圖表時發生錯誤")
    
    def run(self):
        """運行 Bot"""
        # 建立應用程式
        self.application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # 初始化警報系統
        self.alert_system = AlertSystem(self.application.bot)
        
        # 註冊命令處理器
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stock", self.stock_command))
        self.application.add_handler(CommandHandler("price", self.price_command))
        self.application.add_handler(CommandHandler("watchlist", self.watchlist_command))
        self.application.add_handler(CommandHandler("add", self.add_command))
        self.application.add_handler(CommandHandler("remove", self.remove_command))
        self.application.add_handler(CommandHandler("alerts", self.alerts_command))
        self.application.add_handler(CommandHandler("personality", self.personality_command))
        self.application.add_handler(CommandHandler("strategy", self.strategy_command))
        self.application.add_handler(CommandHandler("chart", self.chart_command))
        self.application.add_handler(CommandHandler("compare", self.compare_command))
        
        # 註冊按鈕回調處理器
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # 啟動 Bot
        logger.info("Starting Stock Bot...")
        
        # 檢查是否使用 webhook（雲端部署）
        if WEBHOOK_URL:
            logger.info(f"Using webhook: {WEBHOOK_URL}")
            self.application.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                webhook_url=WEBHOOK_URL,
                secret_token=None
            )
        else:
            # 檢查是否在雲端環境（Render/Heroku 等）
            if os.getenv('RENDER') or os.getenv('HEROKU') or os.getenv('PORT'):
                # 在雲端環境使用 webhook，但沒有設定 WEBHOOK_URL
                logger.info("Detected cloud environment, using webhook mode")
                # 使用 polling 模式，但設定為 webhook 準備
                self.application.run_polling(allowed_updates=Update.ALL_TYPES)
            else:
                logger.info("Using polling mode")
                self.application.run_polling()

if __name__ == "__main__":
    bot = StockBot()
    bot.run() 