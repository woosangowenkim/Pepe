import argparse
from dataclasses import dataclass
from datetime import timedelta
from typing import List

import pandas as pd

@dataclass
class Attempt:
    direction: str  # 'long' 또는 'short'
    size: float     # USD 투자 금액
    tp: float       # 익절 비율 (예: 0.15)
    sl: float       # 손절 비율 (예: 0.05)

def load_data(path: str) -> pd.DataFrame:
    """
    CSV에서 1h OHLCV 데이터를 읽어와,
    UTC 밀리초 타임스탬프를 서울 시간 datetime 인덱스로 변환 후 반환.
    """
    df = pd.read_csv(path)
    # 1) open_time(ms) → UTC datetime
    df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms', utc=True)
    # 2) UTC → Asia/Seoul
    df['timestamp'] = df['timestamp'].dt.tz_convert('Asia/Seoul')
    # 3) 인덱스로 설정
    df = df.set_index('timestamp').sort_index()
    return df[['open','high','low','close','volume']]

def backtest(df: pd.DataFrame) -> pd.DataFrame:
    """
    매일 서울 시간 09:00 시가 진입, 최대 6번 시도하는 PEPE 전략 백테스트.
    """
    capital = 100_000.0
    fee_rate = 0.0002  # 거래당 0.02%

    attempts: List[Attempt] = [
        Attempt('long',  669,  0.15, 0.05),
        Attempt('short', 1344, 0.10, 0.05),
        Attempt('long',  1347, 0.15, 0.05),
        Attempt('short', 2705, 0.10, 0.05),
        Attempt('long',  2712, 0.15, 0.05),
        Attempt('short', 5446, 0.10, 0.05),
    ]

    records = []

    # 백테스트 기간: 데이터 첫날부터 30일간
    start_day = df.index[0].normalize()
    end_day   = start_day + pd.Timedelta(days=30)
    df_period = df.loc[start_day : end_day]

    # 일별로 그룹핑
    for day, group in df_period.groupby(df_period.index.normalize()):
        # 서울 시간 09:00 시가 캔들
        open_candle = group.between_time('09:00','09:00')
        if open_candle.empty:
            continue

        entry_price = open_candle['open'].iloc[0]
        current_ts  = open_candle.index[0]

        for i, at in enumerate(attempts, start=1):
            future = group.loc[group.index > current_ts]
            if future.empty:
                break

            # TP/SL 가격 계산
            if at.direction == 'long':
                tp_price = entry_price * (1 + at.tp)
                sl_price = entry_price * (1 - at.sl)
            else:
                tp_price = entry_price * (1 - at.tp)
                sl_price = entry_price * (1 + at.sl)

            exit_price = entry_price
            exit_ts    = None
            result     = ''

            # TP 또는 SL 발생 탐색
            for ts, row in future.iterrows():
                high, low = row['high'], row['low']
                if at.direction == 'long':
                    if low <= sl_price:
                        exit_price, exit_ts, result = sl_price, ts, 'SL'
                        break
                    if high >= tp_price:
                        exit_price, exit_ts, result = tp_price, ts, 'TP'
                        break
                else:
                    if high >= sl_price:
                        exit_price, exit_ts, result = sl_price, ts, 'SL'
                        break
                    if low <= tp_price:
                        exit_price, exit_ts, result = tp_price, ts, 'TP'
                        break

            # TP/SL 미발생 시 당일 종가 청산
            if exit_ts is None:
                exit_ts    = future.index[-1]
                exit_price = future['close'].iloc[-1]
                result     = 'EOD'

            qty = at.size / entry_price
            pnl = (exit_price - entry_price) * qty if at.direction=='long' else (entry_price - exit_price) * qty
            pnl -= at.size * fee_rate * 2
            capital += pnl

            records.append({
                'date':        day.strftime('%Y-%m-%d'),
                'attempt':     i,
                'direction':   at.direction,
                'entry_time':  current_ts,
                'entry_price': entry_price,
                'exit_time':   exit_ts,
                'exit_price':  exit_price,
                'result':      result,
                'pnl':         pnl,
                'capital':     capital,
            })

            # 다음 시도 준비
            entry_price = exit_price
            current_ts  = exit_ts
            # 6번째 시도에서 SL 발생 시 종료
            if i == 6 and result == 'SL':
                break

    return pd.DataFrame(records)

def main():
    parser = argparse.ArgumentParser(description='PEPE 코인 전략 백테스트 (서울 시간 09:00 진입)')
    parser.add_argument('csv', help='1h OHLCV CSV 경로 (open_time, open, high, low, close, volume)')
    parser.add_argument('-o','--output', help='결과 저장할 CSV 파일명', default=None)
    args = parser.parse_args()

    df     = load_data(args.csv)
    result = backtest(df)

    if args.output:
        result.to_csv(args.output, index=False)

    print(result.tail())
    if not result.empty:
        print(f"최종 자본: {result.iloc[-1]['capital']:.2f} USD, 총 거래: {len(result)}건. ")

if __name__ == '__main__':
    main()
