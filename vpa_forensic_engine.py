import os
import json
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import pytz

# ==============================================================================
# 0. 核心配置与资产监控池 (CONFIG & 12-TICKER BASKET)
# ==============================================================================
TIINGO_API_KEY = "bcffe3a5cf7eeef085e405cfa4a3e5691b976217"

TARGET_INDEX = "QQQ"
MAG_7 = ["NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA"]
MEMORY_BASKET = ["MU", "SNDK", "WDC", "STX"]  # SNDK 与 WDC 独立审计
ALL_TICKERS = [TARGET_INDEX] + MAG_7 + MEMORY_BASKET

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Token {TIINGO_API_KEY}"
}

# ==============================================================================
# 1. 物理量价特征工程 (VPA FORENSIC ENGINE)
# ==============================================================================
def classify_vpa(open_p, high_p, low_p, close_p, volume, avg_volume):
    """严格根据物理公式法医分类 K 线形态"""
    spread = high_p - low_p
    if spread <= 0.0001:
        spread = 0.0001
    
    body = abs(close_p - open_p)
    upper_wick = high_p - max(open_p, close_p)
    lower_wick = min(open_p, close_p) - low_p
    
    upper_wick_ratio = upper_wick / spread
    lower_wick_ratio = lower_wick / spread
    close_pos = (close_p - low_p) / spread
    rvol = volume / (avg_volume if avg_volume > 0 else 1.0)

    # 1. STOPPING VOLUME 📈
    if rvol >= 1.8 and lower_wick_ratio >= 0.40 and close_pos >= 0.33:
        return "STOPPING_VOLUME", rvol, close_pos, upper_wick_ratio, lower_wick_ratio
    
    # 2. UPTHRUST / TOPPING OUT 🛑
    if rvol >= 1.8 and upper_wick_ratio >= 0.45 and close_pos <= 0.35:
        return "UPTHRUST_TOPPING", rvol, close_pos, upper_wick_ratio, lower_wick_ratio
    
    # 3. LOW VOLUME TEST / NO SUPPLY 🚀
    if rvol <= 0.70 and close_pos >= 0.50:
        return "LOW_VOL_TEST", rvol, close_pos, upper_wick_ratio, lower_wick_ratio
    
    # 4. VALID BREAKOUT 🚀
    if rvol >= 1.6 and (body / spread) >= 0.60 and close_p > open_p:
        return "VALID_BREAKOUT", rvol, close_pos, upper_wick_ratio, lower_wick_ratio
    
    # 5. ABSORPTION 📈
    if 1.2 <= rvol <= 1.5 and close_p >= open_p and upper_wick_ratio <= 0.25:
        return "ABSORPTION", rvol, close_pos, upper_wick_ratio, lower_wick_ratio
    
    return "NORMAL", rvol, close_pos, upper_wick_ratio, lower_wick_ratio

def calculate_volume_profile(df_intraday, price_col='close', vol_col='volume', bins=30):
    """计算盘前 Volume Profile: Premarket POC, VAH, VAL"""
    if df_intraday.empty or df_intraday[vol_col].sum() == 0:
        return None, None, None
    
    min_p = df_intraday['low'].min()
    max_p = df_intraday['high'].max()
    if min_p == max_p:
        return min_p, max_p, min_p
    
    price_bins = np.linspace(min_p, max_p, bins)
    vol_profile = np.zeros(bins - 1)
    
    for _, row in df_intraday.iterrows():
        p = row[price_col]
        v = row[vol_col]
        idx = np.digitize(p, price_bins) - 1
        if 0 <= idx < len(vol_profile):
            vol_profile[idx] += v
            
    poc_idx = np.argmax(vol_profile)
    poc = (price_bins[poc_idx] + price_bins[poc_idx + 1]) / 2.0
    
    total_vol = vol_profile.sum()
    target_va_vol = total_vol * 0.70
    accumulated_vol = vol_profile[poc_idx]
    
    low_idx, high_idx = poc_idx, poc_idx
    while accumulated_vol < target_va_vol and (low_idx > 0 or high_idx < len(vol_profile) - 1):
        next_low_vol = vol_profile[low_idx - 1] if low_idx > 0 else 0
        next_high_vol = vol_profile[high_idx + 1] if high_idx < len(vol_profile) - 1 else 0
        
        if next_low_vol >= next_high_vol and low_idx > 0:
            low_idx -= 1
            accumulated_vol += next_low_vol
        elif high_idx < len(vol_profile) - 1:
            high_idx += 1
            accumulated_vol += next_high_vol
        else:
            break
            
    val = price_bins[low_idx]
    vah = price_bins[high_idx + 1]
    return round(poc, 2), round(vah, 2), round(val, 2)

# ==============================================================================
# 2. Tiingo 数据提取管道 (TIINGO INGESTION)
# ==============================================================================
def fetch_tiingo_daily(ticker, days=90):
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices?startDate={start_date}&token={TIINGO_API_KEY}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                return df
    except Exception as e:
        print(f"[-] Fetch Daily {ticker} Notice: {e}")
    return pd.DataFrame()

def fetch_tiingo_intraday_premarket(ticker):
    today_str = datetime.now().strftime("%Y-%m-%d")
    url = f"https://api.tiingo.com/iex/{ticker}/prices?startDate={today_str}&resampleFreq=1hour&columns=date,open,high,low,close,volume&token={TIINGO_API_KEY}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                return df
    except Exception as e:
        print(f"[-] Fetch Intraday {ticker} Notice: {e}")
    return pd.DataFrame()

# ==============================================================================
# 3. 核心计算与数据聚合 (PIPELINE AGGREGATION)
# ==============================================================================
def generate_9pm_report():
    print("[*] 正在通过 Tiingo 提取盘前数据并运行量价法医算法...")
    
    # 1. QQQ 4H 宏观与 1H 盘前计算
    qqq_daily = fetch_tiingo_daily(TARGET_INDEX, days=60)
    qqq_intra = fetch_tiingo_intraday_premarket(TARGET_INDEX)
    
    res_4h = round(qqq_daily['high'].max(), 2) if not qqq_daily.empty else 498.50
    sup_4h = round(qqq_daily['low'].tail(20).min(), 2) if not qqq_daily.empty else 488.00
    yesterday_close = round(qqq_daily['close'].iloc[-2], 2) if len(qqq_daily) >= 2 else 492.50
    
    if not qqq_intra.empty:
        pmh = round(qqq_intra['high'].max(), 2)
        pml = round(qqq_intra['low'].min(), 2)
        poc, vah, val = calculate_volume_profile(qqq_intra)
        last_price = round(qqq_intra['close'].iloc[-1], 2)
    else:
        pmh, pml, poc, vah, val, last_price = 495.80, 493.50, 494.10, 494.90, 493.80, 494.70
    
    df_qqq_summary = pd.DataFrame([{
        "Ticker": "QQQ",
        "4H_Major_Res": res_4h,
        "4H_Major_Sup": sup_4h,
        "PMH": pmh,
        "PML": pml,
        "Premarket_POC": poc,
        "VAH": vah,
        "VAL": val,
        "Yesterday_Close": yesterday_close,
        "Last_Premarket_Price": last_price,
        "Status": "ABOVE_POC" if last_price >= poc else "BELOW_POC"
    }])

    # 2. 12 标的宽度与 -20% 折扣监控
    breadth_rows = []
    dip_rows = []
    
    for ticker in ALL_TICKERS:
        daily_df = fetch_tiingo_daily(ticker, days=120)
        intra_df = fetch_tiingo_intraday_premarket(ticker)
        
        peak_high = round(daily_df['high'].max(), 2) if not daily_df.empty else 100.0
        curr_price = round(daily_df['close'].iloc[-1], 2) if not daily_df.empty else 90.0
        drawdown_pct = round(((curr_price - peak_high) / peak_high) * 100, 2)
        
        if ticker == "QQQ":
            group = "INDEX"
        elif ticker in MAG_7:
            group = "MAG_7"
        else:
            group = "MEMORY_FLASH"
            
        vpa_sig = "NORMAL"
        rvol = 1.0
        close_pos = 0.5
        if not intra_df.empty and len(intra_df) > 0:
            last_row = intra_df.iloc[-1]
            avg_vol = intra_df['volume'].mean()
            vpa_sig, rvol, close_pos, _, _ = classify_vpa(
                last_row['open'], last_row['high'], last_row['low'], last_row['close'],
                last_row['volume'], avg_vol
            )
            curr_price = round(last_row['close'], 2)
        
        breadth_rows.append({
            "Ticker": ticker,
            "Group": group,
            "Current_Price": curr_price,
            "Premarket_RVol": round(rvol, 2),
            "Close_Pos": round(close_pos, 2),
            "VPA_Signal": vpa_sig
        })
        
        if ticker != "QQQ":
            in_buy_zone = drawdown_pct <= -20.0
            tp1 = round(curr_price * 1.15, 2) if in_buy_zone else None
            tp2 = round(curr_price * 1.25, 2) if in_buy_zone else None
            sl = round(curr_price * 0.96, 2) if in_buy_zone else None
            
            dip_rows.append({
                "Ticker": ticker,
                "Group": group,
                "52W_Peak": peak_high,
                "Current_Price": curr_price,
                "Drawdown_%": f"{drawdown_pct}%",
                "Status": "IN_BUY_ZONE" if in_buy_zone else "MONITORING",
                "VPA_Setup": vpa_sig,
                "Buy_Trigger": curr_price if in_buy_zone else "-",
                "Hard_SL": sl if in_buy_zone else "-",
                "TP1 (+15%)": tp1 if in_buy_zone else "-",
                "TP2 (+25%)": tp2 if in_buy_zone else "-"
            })

    df_breadth = pd.DataFrame(breadth_rows)
    df_dip = pd.DataFrame(dip_rows)

    # 3. 输出多 Tab 结构化 Excel
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M")
    excel_filename = f"QQQ_VPA_Forensic_{timestamp_str}.xlsx"
    
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        df_qqq_summary.to_excel(writer, sheet_name="QQQ_Coordinates", index=False)
        df_breadth.to_excel(writer, sheet_name="Market_Breadth_12", index=False)
        df_dip.to_excel(writer, sheet_name="Dip_To_Swing_20Pct", index=False)
    
    print(f"\n[+] 成功生成战役 Excel: {excel_filename}")
    
    # 4. 终端直接打印复制文本 (PAYLOAD)
    print("\n" + "="*80)
    print("      可以直接复制发给 Gem 的 9:00 PM RAW DATA PAYLOAD")
    print("="*80)
    payload_text = {
        "QQQ_Coordinates": df_qqq_summary.to_dict(orient="records")[0],
        "Breadth_Summary": df_breadth.to_dict(orient="records"),
        "Dip_Buys_Triggered": df_dip[df_dip['Status'] == 'IN_BUY_ZONE'].to_dict(orient="records")
    }
    print(json.dumps(payload_text, indent=2, ensure_ascii=False))
    print("="*80)

if __name__ == "__main__":
    generate_9pm_report()
