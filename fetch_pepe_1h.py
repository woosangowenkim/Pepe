import requests
import csv
from datetime import datetime, timedelta, timezone

# --- 설정: 원하는 연월 지정 (YYYYMM) ---
target_month = "202412"
year  = int(target_month[:4])
month = int(target_month[4:])

KST = timezone(timedelta(hours=9))

start_kst = datetime(year, month, 1, 0, 0, tzinfo=KST)
if month == 12:
    next_kst = datetime(year+1, 1, 1, 0, 0, tzinfo=KST)
else:
    next_kst = datetime(year, month+1, 1, 0, 0, tzinfo=KST)

start_ts = int(start_kst.astimezone(timezone.utc).timestamp() * 1000)
end_ts   = int(next_kst.astimezone(timezone.utc).timestamp() * 1000)

symbol   = "PEPEUSDT"
interval = "1h"

all_klines = []
while True:
    params = {
        "symbol":    symbol,
        "interval":  interval,
        "startTime": start_ts,
        "endTime":   end_ts,
        "limit":     1000,
    }
    resp  = requests.get("https://api.binance.com/api/v3/klines", params=params, timeout=10)
    chunk = resp.json()
    if not chunk:
        break
    all_klines += chunk
    start_ts = chunk[-1][0] + 1
    if start_ts >= end_ts:
        break

# --- CSV 쓰기 (가독성 위해 readable_time: KST 00:00) ---
filename = f"pepe_{target_month}.csv"
with open(filename, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "open_time","open","high","low","close","volume",
        "close_time","qav","num_trades","taker_base_vol",
        "taker_quote_vol","ignore","readable_time"
    ])
    for row in all_klines:
        dt_utc  = datetime.utcfromtimestamp(row[0] / 1000).replace(tzinfo=timezone.utc)
        dt_kst  = dt_utc.astimezone(KST)  
        readable = dt_kst.strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow(row + [readable])

print(f"총 {len(all_klines)}개의 1시간 봉 데이터를 {filename}에 저장했습니다.")
