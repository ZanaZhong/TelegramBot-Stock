import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
import seaborn as sns
from stock_data import StockDataManager
import logging

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class ChartGenerator:
    def __init__(self):
        self.stock_manager = StockDataManager()
        self.logger = logging.getLogger(__name__)
    
    def generate_price_chart(self, symbol, period='1mo', style='dark_background'):
        """生成價格走勢圖"""
        try:
            # 取得歷史資料
            df = self.stock_manager.get_historical_data(symbol, period=period)
            if df is None or df.empty:
                return None
            
            # 設定圖表樣式
            plt.style.use(style)
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])
            fig.suptitle(f'{symbol} 價格走勢圖', fontsize=16, fontweight='bold')
            
            # 主圖：價格和成交量
            ax1.plot(df.index, df['Close'], label='收盤價', linewidth=2, color='#00ff88')
            ax1.plot(df.index, df['Open'], label='開盤價', linewidth=1, color='#ff8800', alpha=0.7)
            ax1.fill_between(df.index, df['High'], df['Low'], alpha=0.3, color='#888888', label='高低價範圍')
            
            # 添加移動平均線
            if len(df) >= 20:
                ma20 = df['Close'].rolling(window=20).mean()
                ax1.plot(df.index, ma20, label='20日均線', color='#ff0088', linewidth=1.5)
            
            if len(df) >= 50:
                ma50 = df['Close'].rolling(window=50).mean()
                ax1.plot(df.index, ma50, label='50日均線', color='#8800ff', linewidth=1.5)
            
            ax1.set_ylabel('價格 ($)', fontsize=12)
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            # 成交量圖
            colors = ['red' if close < open else 'green' for close, open in zip(df['Close'], df['Open'])]
            ax2.bar(df.index, df['Volume'], color=colors, alpha=0.7, label='成交量')
            ax2.set_ylabel('成交量', fontsize=12)
            ax2.set_xlabel('日期', fontsize=12)
            ax2.grid(True, alpha=0.3)
            
            # 格式化日期軸
            for ax in [ax1, ax2]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(df)//10)))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            
            # 轉換為 bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='#1e1e1e' if style == 'dark_background' else 'white')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer
            
        except Exception as e:
            self.logger.error(f"Error generating price chart for {symbol}: {e}")
            return None
    
    def generate_technical_chart(self, symbol, period='1mo', style='dark_background'):
        """生成技術指標圖"""
        try:
            # 取得歷史資料並計算技術指標
            df = self.stock_manager.get_historical_data(symbol, period=period)
            if df is None or df.empty:
                return None
            
            df = self.stock_manager.calculate_technical_indicators(df)
            if df is None:
                return None
            
            # 設定圖表樣式
            plt.style.use(style)
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(f'{symbol} 技術分析圖', fontsize=16, fontweight='bold')
            
            # RSI 圖
            ax1.plot(df.index, df['RSI'], color='#00ff88', linewidth=2, label='RSI')
            ax1.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='超買線')
            ax1.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='超賣線')
            ax1.set_ylabel('RSI', fontsize=12)
            ax1.set_title('相對強弱指數 (RSI)', fontsize=12)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax1.set_ylim(0, 100)
            
            # MACD 圖
            ax2.plot(df.index, df['MACD'], color='#00ff88', linewidth=2, label='MACD')
            ax2.plot(df.index, df['MACD_Signal'], color='#ff8800', linewidth=2, label='Signal')
            ax2.bar(df.index, df['MACD_Histogram'], color='#888888', alpha=0.7, label='Histogram')
            ax2.set_ylabel('MACD', fontsize=12)
            ax2.set_title('MACD 指標', fontsize=12)
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # 布林通道圖
            ax3.plot(df.index, df['Close'], color='#00ff88', linewidth=2, label='收盤價')
            ax3.plot(df.index, df['BB_Upper'], color='#ff0088', linewidth=1.5, label='上軌', alpha=0.7)
            ax3.plot(df.index, df['BB_Middle'], color='#888888', linewidth=1.5, label='中軌', alpha=0.7)
            ax3.plot(df.index, df['BB_Lower'], color='#ff0088', linewidth=1.5, label='下軌', alpha=0.7)
            ax3.fill_between(df.index, df['BB_Upper'], df['BB_Lower'], alpha=0.1, color='#888888')
            ax3.set_ylabel('價格 ($)', fontsize=12)
            ax3.set_title('布林通道', fontsize=12)
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            # 成交量圖
            colors = ['red' if close < open else 'green' for close, open in zip(df['Close'], df['Open'])]
            ax4.bar(df.index, df['Volume'], color=colors, alpha=0.7, label='成交量')
            if 'Volume_SMA' in df.columns:
                ax4.plot(df.index, df['Volume_SMA'], color='#ff8800', linewidth=2, label='成交量均線')
            ax4.set_ylabel('成交量', fontsize=12)
            ax4.set_title('成交量分析', fontsize=12)
            ax4.legend()
            ax4.grid(True, alpha=0.3)
            
            # 格式化日期軸
            for ax in [ax1, ax2, ax3, ax4]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(df)//8)))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            
            # 轉換為 bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight',
                       facecolor='#1e1e1e' if style == 'dark_background' else 'white')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer
            
        except Exception as e:
            self.logger.error(f"Error generating technical chart for {symbol}: {e}")
            return None
    
    def generate_comparison_chart(self, symbols, period='1mo', style='dark_background'):
        """生成多股票比較圖"""
        try:
            plt.style.use(style)
            fig, ax = plt.subplots(figsize=(12, 8))
            
            colors = ['#00ff88', '#ff8800', '#0088ff', '#ff0088', '#8800ff']
            
            for i, symbol in enumerate(symbols[:5]):  # 最多比較5支股票
                df = self.stock_manager.get_historical_data(symbol, period=period)
                if df is not None and not df.empty:
                    # 標準化價格（以第一天為基準）
                    normalized_price = df['Close'] / df['Close'].iloc[0] * 100
                    ax.plot(df.index, normalized_price, 
                           label=symbol, color=colors[i % len(colors)], linewidth=2)
            
            ax.set_ylabel('標準化價格 (%)', fontsize=12)
            ax.set_xlabel('日期', fontsize=12)
            ax.set_title('股票表現比較', fontsize=16, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # 格式化日期軸
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            
            # 轉換為 bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight',
                       facecolor='#1e1e1e' if style == 'dark_background' else 'white')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer
            
        except Exception as e:
            self.logger.error(f"Error generating comparison chart: {e}")
            return None
    
    def generate_heatmap_chart(self, symbols, period='1mo'):
        """生成相關性熱力圖"""
        try:
            # 收集所有股票的價格資料
            price_data = {}
            for symbol in symbols[:10]:  # 最多10支股票
                df = self.stock_manager.get_historical_data(symbol, period=period)
                if df is not None and not df.empty:
                    price_data[symbol] = df['Close']
            
            if len(price_data) < 2:
                return None
            
            # 建立相關性矩陣
            price_df = pd.DataFrame(price_data)
            correlation_matrix = price_df.corr()
            
            # 生成熱力圖
            plt.figure(figsize=(10, 8))
            sns.heatmap(correlation_matrix, annot=True, cmap='RdYlBu_r', center=0,
                       square=True, linewidths=0.5, cbar_kws={"shrink": .8})
            plt.title('股票相關性熱力圖', fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            # 轉換為 bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer
            
        except Exception as e:
            self.logger.error(f"Error generating heatmap chart: {e}")
            return None 