import yfinance as yf
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta
import logging
from config import *

class StockDataManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_stock_info(self, symbol):
        """取得股票基本資訊"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', 0)
            }
        except Exception as e:
            self.logger.error(f"Error getting stock info for {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol):
        """取得即時股價"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='1d')
            
            if hist.empty:
                return None
            
            latest = hist.iloc[-1]
            return {
                'symbol': symbol,
                'price': float(latest['Close']),
                'volume': int(latest['Volume']),
                'change': float(latest['Close'] - latest['Open']),
                'change_percent': float((latest['Close'] - latest['Open']) / latest['Open'] * 100),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'open': float(latest['Open']),
                'timestamp': datetime.now()
            }
        except Exception as e:
            self.logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol, period='1mo', interval='1d'):
        """取得歷史股價資料"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                return None
            
            return hist
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            return None
    
    def calculate_technical_indicators(self, df):
        """計算技術指標"""
        if df is None or df.empty:
            return None
        
        try:
            # RSI
            df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=RSI_PERIOD).rsi()
            
            # MACD
            macd = ta.trend.MACD(df['Close'], window_fast=MACD_FAST, window_slow=MACD_SLOW, window_sign=MACD_SIGNAL)
            df['MACD'] = macd.macd()
            df['MACD_Signal'] = macd.macd_signal()
            df['MACD_Histogram'] = macd.macd_diff()
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(df['Close'], window=BOLLINGER_PERIOD, window_dev=BOLLINGER_STD)
            df['BB_Upper'] = bb.bollinger_hband()
            df['BB_Middle'] = bb.bollinger_mavg()
            df['BB_Lower'] = bb.bollinger_lband()
            
            # Moving Averages
            df['MA_5'] = ta.trend.SMAIndicator(df['Close'], window=5).sma_indicator()
            df['MA_10'] = ta.trend.SMAIndicator(df['Close'], window=10).sma_indicator()
            df['MA_20'] = ta.trend.SMAIndicator(df['Close'], window=20).sma_indicator()
            df['MA_50'] = ta.trend.SMAIndicator(df['Close'], window=50).sma_indicator()
            
            # Volume indicators
            df['Volume_SMA'] = ta.trend.SMAIndicator(df['Volume'], window=20).sma_indicator()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
            
            # Volatility
            df['Volatility'] = df['Close'].pct_change().rolling(window=20).std()
            
            return df
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
            return None
    
    def get_stock_analysis(self, symbol, personality='上班族型交易者'):
        """根據投資人格取得股票分析"""
        try:
            # 取得歷史資料
            period_map = {
                '打工型交易者': '1mo',
                '上班族型交易者': '3mo', 
                '老闆型交易者': '6mo',
                '成長型投資者': '1mo',
                '被動型投資者': '1y'
            }
            
            period = period_map.get(personality, '3mo')
            df = self.get_historical_data(symbol, period=period)
            
            if df is None:
                return None
            
            # 計算技術指標
            df = self.calculate_technical_indicators(df)
            
            if df is None:
                return None
            
            # 取得當前價格
            current_price = self.get_current_price(symbol)
            
            # 根據投資人格生成分析
            analysis = self._generate_personality_analysis(df, current_price, personality)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in stock analysis for {symbol}: {e}")
            return None
    
    def _generate_personality_analysis(self, df, current_price, personality):
        """根據投資人格生成分析建議"""
        if df is None or current_price is None:
            return None
        
        latest = df.iloc[-1]
        analysis = {
            'symbol': current_price['symbol'],
            'current_price': current_price['price'],
            'change_percent': current_price['change_percent'],
            'personality': personality,
            'signals': [],
            'recommendation': '',
            'risk_level': '',
            'technical_indicators': {}
        }
        
        # 基本技術指標
        analysis['technical_indicators'] = {
            'rsi': float(latest['RSI']) if not pd.isna(latest['RSI']) else None,
            'macd': float(latest['MACD']) if not pd.isna(latest['MACD']) else None,
            'macd_signal': float(latest['MACD_Signal']) if not pd.isna(latest['MACD_Signal']) else None,
            'bb_position': self._calculate_bb_position(latest),
            'ma_trend': self._calculate_ma_trend(df),
            'volume_ratio': float(latest['Volume_Ratio']) if not pd.isna(latest['Volume_Ratio']) else None,
            'volatility': float(latest['Volatility']) if not pd.isna(latest['Volatility']) else None
        }
        
        # 根據投資人格生成信號
        if personality == '打工型交易者':
            analysis = self._short_term_signals(analysis, df)
        elif personality == '上班族型交易者':
            analysis = self._balanced_signals(analysis, df)
        elif personality == '老闆型交易者':
            analysis = self._long_term_signals(analysis, df)
        elif personality == '成長型投資者':
            analysis = self._growth_signals(analysis, df)
        elif personality == '被動型投資者':
            analysis = self._passive_signals(analysis, df)
        
        return analysis
    
    def _calculate_bb_position(self, latest):
        """計算布林通道位置"""
        if pd.isna(latest['BB_Upper']) or pd.isna(latest['BB_Lower']):
            return None
        
        price = latest['Close']
        upper = latest['BB_Upper']
        lower = latest['BB_Lower']
        
        if upper == lower:
            return 0.5
        
        position = (price - lower) / (upper - lower)
        return float(position)
    
    def _calculate_ma_trend(self, df):
        """計算均線趨勢"""
        if len(df) < 50:
            return 'insufficient_data'
        
        latest = df.iloc[-1]
        ma5 = latest['MA_5']
        ma20 = latest['MA_20']
        ma50 = latest['MA_50']
        
        if pd.isna(ma5) or pd.isna(ma20) or pd.isna(ma50):
            return 'insufficient_data'
        
        if ma5 > ma20 > ma50:
            return 'strong_uptrend'
        elif ma5 > ma20:
            return 'uptrend'
        elif ma5 < ma20 < ma50:
            return 'strong_downtrend'
        elif ma5 < ma20:
            return 'downtrend'
        else:
            return 'sideways'
    
    def _short_term_signals(self, analysis, df):
        """短線交易信號"""
        latest = df.iloc[-1]
        signals = []
        
        # RSI 信號
        if latest['RSI'] < 30:
            signals.append('RSI 超賣，可能反彈')
        elif latest['RSI'] > 70:
            signals.append('RSI 超買，注意回調')
        
        # MACD 信號
        if latest['MACD'] > latest['MACD_Signal']:
            signals.append('MACD 金叉，短線偏多')
        else:
            signals.append('MACD 死叉，短線偏空')
        
        # 布林通道信號
        bb_pos = analysis['technical_indicators']['bb_position']
        if bb_pos and bb_pos < 0.2:
            signals.append('接近布林下軌，可能反彈')
        elif bb_pos and bb_pos > 0.8:
            signals.append('接近布林上軌，注意回調')
        
        analysis['signals'] = signals
        analysis['risk_level'] = '高'
        analysis['recommendation'] = '適合短線操作，注意停損'
        
        return analysis
    
    def _balanced_signals(self, analysis, df):
        """平衡型投資信號"""
        latest = df.iloc[-1]
        signals = []
        
        # 綜合技術面分析
        ma_trend = analysis['technical_indicators']['ma_trend']
        if ma_trend == 'strong_uptrend':
            signals.append('均線多頭排列，趨勢向上')
        elif ma_trend == 'strong_downtrend':
            signals.append('均線空頭排列，趨勢向下')
        
        # 成交量分析
        if latest['Volume_Ratio'] > 1.5:
            signals.append('成交量放大，關注後續走勢')
        
        # RSI 中性分析
        if 40 <= latest['RSI'] <= 60:
            signals.append('RSI 中性，可觀察其他指標')
        
        analysis['signals'] = signals
        analysis['risk_level'] = '中'
        analysis['recommendation'] = '平衡配置，定期檢視'
        
        return analysis
    
    def _long_term_signals(self, analysis, df):
        """長線投資信號"""
        latest = df.iloc[-1]
        signals = []
        
        # 長期趨勢
        ma_trend = analysis['technical_indicators']['ma_trend']
        if ma_trend == 'strong_uptrend':
            signals.append('長期趨勢向上，適合持有')
        elif ma_trend == 'strong_downtrend':
            signals.append('長期趨勢向下，謹慎持有')
        
        # 波動率分析
        volatility = analysis['technical_indicators']['volatility']
        if volatility and volatility < 0.02:
            signals.append('波動率較低，適合長期持有')
        
        analysis['signals'] = signals
        analysis['risk_level'] = '低'
        analysis['recommendation'] = '長期持有，定期定額'
        
        return analysis
    
    def _growth_signals(self, analysis, df):
        """成長型投資信號"""
        latest = df.iloc[-1]
        signals = []
        
        # 高波動機會
        volatility = analysis['technical_indicators']['volatility']
        if volatility and volatility > 0.05:
            signals.append('高波動，潛在獲利機會大')
        
        # 成交量分析
        if latest['Volume_Ratio'] > 2.0:
            signals.append('成交量暴增，關注突破')
        
        # RSI 極值
        if latest['RSI'] < 20:
            signals.append('極度超賣，可能反彈')
        elif latest['RSI'] > 80:
            signals.append('極度超買，注意風險')
        
        analysis['signals'] = signals
        analysis['risk_level'] = '很高'
        analysis['recommendation'] = '高風險高報酬，嚴格停損'
        
        return analysis
    
    def _passive_signals(self, analysis, df):
        """被動型投資信號"""
        latest = df.iloc[-1]
        signals = []
        
        # 長期趨勢
        ma_trend = analysis['technical_indicators']['ma_trend']
        if ma_trend == 'strong_uptrend':
            signals.append('長期趨勢良好，繼續持有')
        elif ma_trend == 'sideways':
            signals.append('橫盤整理，適合定額投資')
        
        # 低波動
        volatility = analysis['technical_indicators']['volatility']
        if volatility and volatility < 0.015:
            signals.append('低波動，適合被動投資')
        
        analysis['signals'] = signals
        analysis['risk_level'] = '很低'
        analysis['recommendation'] = '被動投資，定期定額'
        
        return analysis 