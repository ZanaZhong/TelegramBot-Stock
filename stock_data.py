import yfinance as yf
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta
import logging
import time
import random
import requests
import os
from config import *

class StockDataManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.last_request_time = 0
        self.min_request_interval = 10.0  # 增加最小請求間隔到10秒
        self.max_retries = 1  # 減少重試次數避免過度請求
        self.retry_delay = 30.0  # 大幅增加重試延遲到30秒
        
        # 快取機制
        self.cache = {}
        self.cache_duration = 600  # 增加快取時間到10分鐘
        
        # 全局請求計數器
        self.request_count = 0
        self.max_requests_per_hour = 50  # 減少每小時最大請求數
        self.hourly_reset_time = time.time() + 3600
        
        # API 來源列表（僅穩定可用的免費來源）
        self.api_sources = [
            'yahoo_finance',
            'iex_cloud',
            'alpha_vantage_free'
        ]
    
    def _rate_limit(self):
        """實施速率限制"""
        current_time = time.time()
        
        # 檢查每小時請求限制
        if current_time > self.hourly_reset_time:
            self.request_count = 0
            self.hourly_reset_time = current_time + 3600
        
        if self.request_count >= self.max_requests_per_hour:
            wait_time = self.hourly_reset_time - current_time
            if wait_time > 0:
                self.logger.warning(f"Hourly rate limit reached, waiting {wait_time:.1f} seconds")
                time.sleep(wait_time)
                self.request_count = 0
                self.hourly_reset_time = time.time() + 3600
        
        # 檢查請求間隔
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            # 添加隨機延遲以避免同時請求
            sleep_time += random.uniform(0.1, 0.5)
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def _get_cache_key(self, symbol, data_type, **kwargs):
        """生成快取鍵"""
        key_parts = [symbol, data_type]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}_{v}")
        return "_".join(key_parts)
    
    def _get_from_cache(self, cache_key):
        """從快取取得資料"""
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                return data
            else:
                # 過期，移除
                del self.cache[cache_key]
        return None
    
    def _set_cache(self, cache_key, data):
        """設定快取"""
        self.cache[cache_key] = (data, time.time())
        
        # 清理過期的快取項目
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp > self.cache_duration
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def _make_request_with_retry(self, func, *args, **kwargs):
        """帶重試機制的請求"""
        for attempt in range(self.max_retries):
            try:
                self._rate_limit()
                result = func(*args, **kwargs)
                
                # 檢查結果是否有效
                if result is not None and not (hasattr(result, 'empty') and result.empty):
                    return result
                else:
                    self.logger.warning(f"Empty result received, attempt {attempt + 1}/{self.max_retries}")
                    
            except Exception as e:
                error_str = str(e).lower()
                
                # 檢測各種錯誤類型
                if any(keyword in error_str for keyword in ["429", "too many requests", "rate limit"]):
                    self.logger.warning(f"Rate limit hit, attempt {attempt + 1}/{self.max_retries}")
                    if attempt < self.max_retries - 1:
                        # 指數退避
                        delay = self.retry_delay * (2 ** attempt)
                        time.sleep(delay)
                        continue
                        
                elif any(keyword in error_str for keyword in ["expecting value", "json", "parse"]):
                    self.logger.warning(f"JSON parsing error, attempt {attempt + 1}/{self.max_retries}")
                    if attempt < self.max_retries - 1:
                        # JSON 錯誤時等待更長時間
                        delay = self.retry_delay * (3 ** attempt)
                        time.sleep(delay)
                        continue
                        
                else:
                    self.logger.error(f"Request failed: {e}")
                    
                break
                
        return None
    
    def _get_yahoo_finance_price(self, symbol):
        """從 Yahoo Finance 取得價格"""
        try:
            ticker = yf.Ticker(symbol)
            
            # 嘗試不同的期間來取得資料
            periods = ['1d', '5d', '1mo']
            
            for period in periods:
                try:
                    hist = ticker.history(period=period)
                    
                    if hist is not None and not hist.empty:
                        latest = hist.iloc[-1]
                        
                        # 檢查資料是否有效
                        if latest['Close'] > 0:
                            return {
                                'symbol': symbol,
                                'price': float(latest['Close']),
                                'volume': int(latest['Volume']),
                                'change': float(latest['Close'] - latest['Open']),
                                'change_percent': float((latest['Close'] - latest['Open']) / latest['Open'] * 100),
                                'high': float(latest['High']),
                                'low': float(latest['Low']),
                                'open': float(latest['Open']),
                                'timestamp': datetime.now(),
                                'source': 'yahoo_finance'
                            }
                except Exception as e:
                    self.logger.warning(f"Yahoo Finance period {period} failed for {symbol}: {e}")
                    continue
            
            self.logger.error(f"All Yahoo Finance periods failed for {symbol}")
            return None
            
        except Exception as e:
            self.logger.error(f"Yahoo Finance error for {symbol}: {e}")
            return None
    
    def _get_iex_cloud_price(self, symbol):
        """從 IEX Cloud 取得價格（免費版）"""
        try:
            # 使用 IEX Cloud 免費 API
            url = f"https://cloud.iexapis.com/stable/stock/{symbol}/quote?token=pk_test"
            response = requests.get(url, timeout=15)
            
            if response.status_code != 200:
                return None
                
            data = response.json()
            
            if 'latestPrice' not in data:
                return None
            
            price = float(data.get('latestPrice', 0))
            change = float(data.get('change', 0))
            change_percent = float(data.get('changePercent', 0)) * 100
            volume = int(data.get('volume', 0))
            high = float(data.get('high', price))
            low = float(data.get('low', price))
            open_price = float(data.get('open', price))
            
            return {
                'symbol': symbol,
                'price': price,
                'volume': volume,
                'change': change,
                'change_percent': change_percent,
                'high': high,
                'low': low,
                'open': open_price,
                'timestamp': datetime.now(),
                'source': 'iex_cloud'
            }
        except Exception as e:
            self.logger.error(f"IEX Cloud error for {symbol}: {e}")
            return None
    
    def _get_alpha_vantage_free_price(self, symbol):
        """從 Alpha Vantage 免費版取得價格"""
        try:
            # 使用 Alpha Vantage 免費 API（每分鐘5次請求）
            api_key = "AJOZ00DM4XIUIWWZ"
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
            response = requests.get(url, timeout=15)
            data = response.json()
            
            if 'Global Quote' not in data or not data['Global Quote']:
                return None
            
            quote = data['Global Quote']
            price = float(quote.get('05. price', 0))
            change = float(quote.get('09. change', 0))
            change_percent = float(quote.get('10. change percent', '0%').replace('%', ''))
            volume = int(quote.get('06. volume', 0))
            
            return {
                'symbol': symbol,
                'price': price,
                'volume': volume,
                'change': change,
                'change_percent': change_percent,
                'high': price + change * 0.5,  # 估算
                'low': price - change * 0.5,   # 估算
                'open': price - change,        # 估算
                'timestamp': datetime.now(),
                'source': 'alpha_vantage_free'
            }
        except Exception as e:
            self.logger.error(f"Alpha Vantage Free error for {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol):
        """取得即時股價 - 優先使用 Yahoo Finance，備用 Alpha Vantage"""
        try:
            cache_key = self._get_cache_key(symbol, "price")
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # 優先使用 Yahoo Finance
            result = self._get_yahoo_finance_price(symbol)
            
            if result:
                self.logger.info(f"✅ Successfully got price for {symbol} from {result['source']}")
                self._set_cache(cache_key, result)
                return result
            
            # 如果 Yahoo Finance 失敗，優先使用 Alpha Vantage
            self.logger.warning(f"Yahoo Finance failed for {symbol}, trying Alpha Vantage...")
            result = self._get_alpha_vantage_free_price(symbol)
            
            if result:
                self.logger.info(f"✅ Successfully got price for {symbol} from {result['source']}")
                self._set_cache(cache_key, result)
                return result
            
            # 最後嘗試 IEX Cloud
            self.logger.warning(f"Alpha Vantage failed for {symbol}, trying IEX Cloud...")
            result = self._get_iex_cloud_price(symbol)
            
            if result:
                self.logger.info(f"✅ Successfully got price for {symbol} from {result['source']}")
                self._set_cache(cache_key, result)
                return result
            
            self.logger.error(f"❌ All API sources failed for {symbol}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    def get_stock_info(self, symbol):
        """取得股票基本資訊"""
        try:
            cache_key = self._get_cache_key(symbol, "info")
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            def _get_info():
                ticker = yf.Ticker(symbol)
                info = ticker.info
                return info
            
            info = self._make_request_with_retry(_get_info)
            
            if info is None:
                return None
            
            result = {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', 0)
            }
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting stock info for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol, period='1mo', interval='1d'):
        """取得歷史股價資料"""
        try:
            cache_key = self._get_cache_key(symbol, "history", period=period, interval=interval)
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            def _get_history():
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period, interval=interval)
                return hist
            
            hist = self._make_request_with_retry(_get_history)
            
            if hist is None or hist.empty:
                return None
            
            self._set_cache(cache_key, hist)
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