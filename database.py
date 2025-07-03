import sqlite3
import json
from datetime import datetime
from config import DATABASE_PATH

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """初始化資料庫表格"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 用戶表格
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                investment_personality TEXT DEFAULT '上班族型交易者',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 股票追蹤表格
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                symbol TEXT,
                company_name TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE(user_id, symbol)
            )
        ''')
        
        # 警報設定表格
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                symbol TEXT,
                alert_type TEXT,  -- price_high, price_low, volume_spike, volatility
                threshold REAL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # 股價歷史表格
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                price REAL,
                volume INTEGER,
                change_percent REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 用戶偏好設定
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY,
                update_frequency INTEGER DEFAULT 60,
                alert_enabled BOOLEAN DEFAULT 1,
                chart_style TEXT DEFAULT 'line',
                timezone TEXT DEFAULT 'Asia/Taipei',
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id, username=None, first_name=None, last_name=None):
        """新增用戶"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, datetime.now()))
        
        # 同時新增偏好設定
        cursor.execute('''
            INSERT OR IGNORE INTO user_preferences (user_id)
            VALUES (?)
        ''', (user_id,))
        
        conn.commit()
        conn.close()
    
    def get_user(self, user_id):
        """取得用戶資料"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        conn.close()
        return user
    
    def add_stock_to_watchlist(self, user_id, symbol, company_name=None):
        """新增股票到追蹤清單"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO stock_watchlist (user_id, symbol, company_name)
                VALUES (?, ?, ?)
            ''', (user_id, symbol.upper(), company_name))
            conn.commit()
            success = True
        except sqlite3.IntegrityError:
            success = False  # 已存在
        
        conn.close()
        return success
    
    def remove_stock_from_watchlist(self, user_id, symbol):
        """從追蹤清單移除股票"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM stock_watchlist 
            WHERE user_id = ? AND symbol = ?
        ''', (user_id, symbol.upper()))
        
        conn.commit()
        conn.close()
    
    def get_user_watchlist(self, user_id):
        """取得用戶的追蹤清單"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, company_name, added_at 
            FROM stock_watchlist 
            WHERE user_id = ?
            ORDER BY added_at DESC
        ''', (user_id,))
        
        watchlist = cursor.fetchall()
        conn.close()
        return watchlist
    
    def add_alert(self, user_id, symbol, alert_type, threshold):
        """新增警報設定"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (user_id, symbol, alert_type, threshold)
            VALUES (?, ?, ?, ?)
        ''', (user_id, symbol.upper(), alert_type, threshold))
        
        conn.commit()
        conn.close()
    
    def get_user_alerts(self, user_id):
        """取得用戶的警報設定"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, alert_type, threshold, is_active
            FROM alerts 
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        alerts = cursor.fetchall()
        conn.close()
        return alerts
    
    def update_investment_personality(self, user_id, personality):
        """更新投資人格設定"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET investment_personality = ?, updated_at = ?
            WHERE user_id = ?
        ''', (personality, datetime.now(), user_id))
        
        conn.commit()
        conn.close()
    
    def save_price_data(self, symbol, price, volume, change_percent):
        """儲存股價資料"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO price_history (symbol, price, volume, change_percent)
            VALUES (?, ?, ?, ?)
        ''', (symbol.upper(), price, volume, change_percent))
        
        conn.commit()
        conn.close()
    
    def get_price_history(self, symbol, limit=100):
        """取得股價歷史資料"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT price, volume, change_percent, timestamp
            FROM price_history 
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (symbol.upper(), limit))
        
        history = cursor.fetchall()
        conn.close()
        return history 