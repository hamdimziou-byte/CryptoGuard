"""
CryptoGuard - Technical Indicators
حساب المؤشرات التقنية
"""


def calculate_sma(prices, period):
    """Simple Moving Average"""
    if len(prices) < period:
        return []
    
    sma = []
    for i in range(len(prices)):
        if i < period - 1:
            sma.append(None)
        else:
            avg = sum(prices[i - period + 1:i + 1]) / period
            sma.append(round(avg, 4))
    
    return sma


def calculate_ema(prices, period):
    """Exponential Moving Average"""
    if len(prices) < period:
        return []
    
    multiplier = 2 / (period + 1)
    ema = [None] * (period - 1)
    
    # SMA كبداية
    sma_start = sum(prices[:period]) / period
    ema.append(round(sma_start, 4))
    
    for i in range(period, len(prices)):
        value = (prices[i] - ema[-1]) * multiplier + ema[-1]
        ema.append(round(value, 4))
    
    return ema


def calculate_rsi(prices, period=14):
    """Relative Strength Index"""
    if len(prices) < period + 1:
        return []
    
    rsi = [None] * period
    
    # حساب التغييرات
    gains = []
    losses = []
    
    for i in range(1, period + 1):
        change = prices[i] - prices[i - 1]
        if change >= 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    if avg_loss == 0:
        rsi.append(100)
    else:
        rs = avg_gain / avg_loss
        rsi.append(round(100 - (100 / (1 + rs)), 2))
    
    # باقي القيم
    for i in range(period + 1, len(prices)):
        change = prices[i] - prices[i - 1]
        gain = change if change > 0 else 0
        loss = abs(change) if change < 0 else 0
        
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        
        if avg_loss == 0:
            rsi.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi.append(round(100 - (100 / (1 + rs)), 2))
    
    return rsi


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """MACD Indicator"""
    if len(prices) < slow + signal:
        return {"macd": [], "signal": [], "histogram": []}
    
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    
    # MACD line = EMA12 - EMA26
    macd_line = []
    start_idx = slow - 1
    for i in range(start_idx, len(prices)):
        if ema_fast[i] is not None and ema_slow[i] is not None:
            macd_line.append(round(ema_fast[i] - ema_slow[i], 4))
        else:
            macd_line.append(None)
    
    # Signal line = EMA9 of MACD
    macd_clean = [v for v in macd_line if v is not None]
    if len(macd_clean) >= signal:
        signal_line_clean = calculate_ema(macd_clean, signal)
        # نعاودو نبنو الـsignal مع None في الأول
        signal_line = [None] * (len(macd_line) - len(signal_line_clean)) + signal_line_clean
    else:
        signal_line = [None] * len(macd_line)
    
    # Histogram = MACD - Signal
    histogram = []
    for m, s in zip(macd_line, signal_line):
        if m is not None and s is not None:
            histogram.append(round(m - s, 4))
        else:
            histogram.append(None)
    
    return {
        "macd": macd_line,
        "signal": signal_line,
        "histogram": histogram
    }


def detect_cross(prices):
    """كشف Golden Cross / Death Cross"""
    if len(prices) < 50:
        return "none"
    
    sma20 = calculate_sma(prices, 20)
    sma50 = calculate_sma(prices, 50)
    
    # آخر قيم
    last_5_sma20 = [v for v in sma20[-5:] if v is not None]
    last_5_sma50 = [v for v in sma50[-5:] if v is not None]
    
    if len(last_5_sma20) < 2 or len(last_5_sma50) < 2:
        return "none"
    
    # Current relationship
    current_20 = last_5_sma20[-1]
    current_50 = last_5_sma50[-1]
    prev_20 = last_5_sma20[-2]
    prev_50 = last_5_sma50[-2]
    
    # Golden Cross: SMA20 يعبر فوق SMA50
    if prev_20 <= prev_50 and current_20 > current_50:
        return "golden_cross"
    
    # Death Cross: SMA20 يعبر تحت SMA50
    if prev_20 >= prev_50 and current_20 < current_50:
        return "death_cross"
    
    # الاتجاه الحالي
    if current_20 > current_50:
        return "bullish"
    else:
        return "bearish"


def calculate_all_indicators(prices):
    """حساب كل المؤشرات دفعة وحدة"""
    return {
        "sma20": calculate_sma(prices, 20),
        "sma50": calculate_sma(prices, 50),
        "rsi": calculate_rsi(prices, 14),
        "macd": calculate_macd(prices),
        "cross": detect_cross(prices),
        "current_rsi": get_current_rsi(prices),
        "current_trend": detect_cross(prices)
    }


def get_current_rsi(prices):
    """آخر قيمة RSI"""
    rsi = calculate_rsi(prices, 14)
    clean = [v for v in rsi if v is not None]
    return clean[-1] if clean else None


# اختبار
if __name__ == "__main__":
    test_prices = [100 + i * 0.5 + (i % 3 - 1) * 2 for i in range(100)]
    
    print("Test Technical Indicators")
    print("=" * 50)
    print(f"SMA 20 (last 5): {calculate_sma(test_prices, 20)[-5:]}")
    print(f"SMA 50 (last 5): {calculate_sma(test_prices, 50)[-5:]}")
    print(f"RSI: {get_current_rsi(test_prices)}")
    print(f"Cross: {detect_cross(test_prices)}")
    macd = calculate_macd(test_prices)
    print(f"MACD (last): {macd['macd'][-1] if macd['macd'] else None}")