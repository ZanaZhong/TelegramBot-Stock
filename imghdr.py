"""
imghdr 模組的替代實現
解決 Python 3.13 中 imghdr 被移除的問題
python-telegram-bot 13.15 需要這個模組
"""

import struct
from typing import Optional, Tuple

def what(file: str, h: Optional[bytes] = None) -> Optional[str]:
    """
    識別圖片格式
    返回格式名稱或 None
    """
    if h is None:
        if isinstance(file, str):
            with open(file, 'rb') as f:
                h = f.read(32)
        else:
            location = file.tell()
            h = file.read(32)
            file.seek(location)
    
    if not h:
        return None
    
    # JPEG
    if h[:2] == b'\xff\xd8':
        return 'jpeg'
    
    # PNG
    if h[:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'
    
    # GIF
    if h[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'
    
    # TIFF
    if h[:2] in (b'MM', b'II'):
        return 'tiff'
    
    # BMP
    if h[:2] == b'BM':
        return 'bmp'
    
    # WebP
    if h[:4] == b'RIFF' and h[8:12] == b'WEBP':
        return 'webp'
    
    # ICO
    if h[:4] == b'\x00\x00\x01\x00':
        return 'ico'
    
    return None

def tests() -> None:
    """測試函數"""
    print("imghdr 替代模組已載入")

# 為了相容性，添加一些舊版本的函數
def _jpeg1(h, fp):
    """JPEG 格式檢測"""
    if h[:2] == b'\xff\xd8':
        return 'jpeg'

def _jpeg2(h, fp):
    """JPEG 格式檢測（備用）"""
    if h[:2] == b'\xff\xd8':
        return 'jpeg'

def _png1(h, fp):
    """PNG 格式檢測"""
    if h[:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'

def _gif1(h, fp):
    """GIF 格式檢測"""
    if h[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'

def _tiff1(h, fp):
    """TIFF 格式檢測"""
    if h[:2] in (b'MM', b'II'):
        return 'tiff'

def _bmp1(h, fp):
    """BMP 格式檢測"""
    if h[:2] == b'BM':
        return 'bmp'

def _webp1(h, fp):
    """WebP 格式檢測"""
    if h[:4] == b'RIFF' and h[8:12] == b'WEBP':
        return 'webp'

def _ico1(h, fp):
    """ICO 格式檢測"""
    if h[:4] == b'\x00\x00\x01\x00':
        return 'ico' 