import asyncio
import logging
from datetime import datetime, timedelta
from database import Database
from stock_data import StockDataManager
from config import *

class AlertSystem:
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.stock_manager = StockDataManager()
        self.logger = logging.getLogger(__name__)
        self.is_running = False
    
    def start_monitoring(self):
        """開始監控警報"""
        self.is_running = True
        self.logger.info("Alert system started")
        
        while self.is_running:
            try:
                self.check_alerts()
                import time
                time.sleep(ALERT_CHECK_INTERVAL)
            except Exception as e:
                self.logger.error(f"Error in alert monitoring: {e}")
                import time
                time.sleep(ALERT_CHECK_INTERVAL)
    
    async def stop_monitoring(self):
        """停止監控"""
        self.is_running = False
        self.logger.info("Alert system stopped")
    
    def check_alerts(self):
        """檢查所有警報"""
        try:
            # 取得所有活躍警報
            conn = self.db.db_path
            import sqlite3
            conn = sqlite3.connect(conn)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT DISTINCT user_id, symbol 
                FROM alerts 
                WHERE is_active = 1
            ''')
            
            active_alerts = cursor.fetchall()
            conn.close()
            
            for user_id, symbol in active_alerts:
                self.check_user_alerts(user_id, symbol)
                
        except Exception as e:
            self.logger.error(f"Error checking alerts: {e}")
    
    def check_user_alerts(self, user_id, symbol):
        """檢查特定用戶的股票警報"""
        try:
            # 取得當前價格
            current_data = self.stock_manager.get_current_price(symbol)
            if not current_data:
                return
            
            # 取得歷史價格
            history = self.db.get_price_history(symbol, limit=2)
            if len(history) < 2:
                return
            
            current_price = current_data['price']
            previous_price = history[1][0]  # 前一個價格
            
            # 取得用戶的警報設定
            alerts = self.db.get_user_alerts(user_id)
            symbol_alerts = [alert for alert in alerts if alert[0] == symbol]
            
            for alert in symbol_alerts:
                symbol, alert_type, threshold, is_active = alert
                
                if not is_active:
                    continue
                
                triggered = False
                message = ""
                
                if alert_type == 'price_high':
                    if current_price >= threshold:
                        triggered = True
                        message = f"🚀 {symbol} 價格突破 {threshold:.2f}！\n當前價格: ${current_price:.2f}"
                
                elif alert_type == 'price_low':
                    if current_price <= threshold:
                        triggered = True
                        message = f"📉 {symbol} 價格跌破 {threshold:.2f}！\n當前價格: ${current_price:.2f}"
                
                elif alert_type == 'price_change':
                    change_percent = abs((current_price - previous_price) / previous_price * 100)
                    if change_percent >= threshold:
                        triggered = True
                        direction = "上漲" if current_price > previous_price else "下跌"
                        message = f"⚡ {symbol} {direction} {change_percent:.1f}%！\n當前價格: ${current_price:.2f}"
                
                elif alert_type == 'volume_spike':
                    volume_ratio = current_data['volume'] / history[1][1] if history[1][1] > 0 else 0
                    if volume_ratio >= threshold:
                        triggered = True
                        message = f"📊 {symbol} 成交量放大 {volume_ratio:.1f} 倍！\n當前成交量: {current_data['volume']:,}"
                
                elif alert_type == 'volatility':
                    # 計算波動率
                    prices = [h[0] for h in history[-20:]]  # 最近20個價格
                    if len(prices) >= 2:
                        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
                        volatility = (sum(r**2 for r in returns) / len(returns))**0.5 * 100
                        
                        if volatility >= threshold:
                            triggered = True
                            message = f"🌊 {symbol} 波動率達到 {volatility:.1f}%！\n當前價格: ${current_price:.2f}"
                
                if triggered:
                    self.send_alert(user_id, message, symbol)
                    # 暫時停用警報避免重複發送
                    self.disable_alert_temporarily(user_id, symbol, alert_type)
        
        except Exception as e:
            self.logger.error(f"Error checking alerts for {user_id} {symbol}: {e}")
    
    def send_alert(self, user_id, message, symbol):
        """發送警報訊息"""
        try:
            # 取得股票資訊
            stock_info = self.stock_manager.get_stock_info(symbol)
            if stock_info:
                company_name = stock_info['name']
                message = f"🔔 **{company_name} ({symbol})**\n\n{message}"
            
            # 添加技術分析
            analysis = self.stock_manager.get_stock_analysis(symbol)
            if analysis and analysis['signals']:
                message += "\n\n📈 **技術分析信號:**\n"
                for signal in analysis['signals'][:3]:  # 只顯示前3個信號
                    message += f"• {signal}\n"
            
            # 發送訊息
            self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
            
            self.logger.info(f"Alert sent to user {user_id} for {symbol}")
            
        except Exception as e:
            self.logger.error(f"Error sending alert to {user_id}: {e}")
    
    def disable_alert_temporarily(self, user_id, symbol, alert_type):
        """暫時停用警報避免重複發送"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE alerts 
                SET is_active = 0 
                WHERE user_id = ? AND symbol = ? AND alert_type = ?
            ''', (user_id, symbol, alert_type))
            
            conn.commit()
            conn.close()
            
            # 30分鐘後重新啟用
            import threading
            import time
            def re_enable():
                time.sleep(1800)
                self.re_enable_alert(user_id, symbol, alert_type, delay=1800)
            threading.Thread(target=re_enable, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Error disabling alert: {e}")
    
    def re_enable_alert(self, user_id, symbol, alert_type, delay=1800):
        """重新啟用警報"""
        import time
        time.sleep(delay)
        
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE alerts 
                SET is_active = 1 
                WHERE user_id = ? AND symbol = ? AND alert_type = ?
            ''', (user_id, symbol, alert_type))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error re-enabling alert: {e}")
    
    def create_price_alert(self, user_id, symbol, alert_type, threshold):
        """建立價格警報"""
        try:
            # 驗證股票代碼
            stock_info = self.stock_manager.get_stock_info(symbol)
            if not stock_info:
                return False, "無效的股票代碼"
            
            # 新增警報
            self.db.add_alert(user_id, symbol, alert_type, threshold)
            
            return True, f"已設定 {symbol} 的 {alert_type} 警報"
            
        except Exception as e:
            self.logger.error(f"Error creating alert: {e}")
            return False, "設定警報時發生錯誤"
    
    def get_user_alert_summary(self, user_id):
        """取得用戶警報摘要"""
        try:
            alerts = self.db.get_user_alerts(user_id)
            
            if not alerts:
                return "您目前沒有設定任何警報"
            
            summary = "🔔 **您的警報設定:**\n\n"
            
            for symbol, alert_type, threshold, is_active in alerts:
                status = "✅ 啟用" if is_active else "⏸️ 暫停"
                
                alert_type_text = {
                    'price_high': '價格突破',
                    'price_low': '價格跌破', 
                    'price_change': '價格變動',
                    'volume_spike': '成交量放大',
                    'volatility': '波動率'
                }.get(alert_type, alert_type)
                
                summary += f"**{symbol}** - {alert_type_text} {threshold}\n{status}\n\n"
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting alert summary: {e}")
            return "取得警報摘要時發生錯誤"
    
    def delete_alert(self, user_id, symbol, alert_type):
        """刪除警報"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM alerts 
                WHERE user_id = ? AND symbol = ? AND alert_type = ?
            ''', (user_id, symbol, alert_type))
            
            conn.commit()
            conn.close()
            
            return True, f"已刪除 {symbol} 的 {alert_type} 警報"
            
        except Exception as e:
            self.logger.error(f"Error deleting alert: {e}")
            return False, "刪除警報時發生錯誤" 