#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from dataclasses import dataclass
from datetime import timedelta
from typing import List

import pandas as pd

@dataclass
class Attempt:
    direction: str  # 'long' 또는 'short'
    size: float     # USD 투자 금액 (고정)
    tp: float       # 익절 비율 (예: 0.16)
    sl: float       # 손절 비율 (예: 0.04)

def load_data(path: str) -> pd.DataFrame:
    """
    CSV에서 1시간봉 OHLCV 데이터를 읽어와,
    open_time(ms) → UTC datetime → Asia/Seoul tz로 변환 후
    timestamp를 인덱스로 설정하여 반환합니다.
    """
    df = pd.read_csv(path)
    df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms', utc=True)
    df['timestamp'] = df['timestamp'].dt.tz_convert('Asia/Seoul')
    return df.set_index('timestamp')[['open','high','low','close','volume']].sort_index()

def backtest(df: pd.DataFrame) -> pd.DataFrame:
    """
    매일 00:00(서울 시간)에 새 계좌를 열고,
    최대 6회까지 연속 시도하며
      • pnl > 0 이면 즉시 종료
      • pnl ≤ 0 이어서 다음 시도 (최대 6회)
    시뮬레이션 결과를 반환합니다.
    """
    fee_rate = 0.0002  # 0.02%

    # 1~6번째 포지션 정의
    attempts: List[Attempt] = [
        Attempt('long',  669,  0.16, 0.04),
        Attempt('short', 1344, 0.12, 0.04),
        Attempt('long',  1347, 0.16, 0.04),
        Attempt('short', 2705, 0.12, 0.04),
        Attempt('long',  2712, 0.16, 0.04),
        Attempt('short', 5446, 0.12, 0.04),
    ]

    records = []
    # 시뮬레이션 기간: 첫봉부터 30일
    start_day = df.index[0].normalize()
    end_day   = start_day + timedelta(days=30)
    days = pd.date_range(start_day, end_day, freq='D', tz='Asia/Seoul')

    for run_start in days:
        # 해당일 00:00 봉 찾기
        day0 = df[(df.index.normalize() == run_start) & (df.index.hour == 0)]
        if day0.empty:
            continue

        capital    = 100_000.0
        entry_price = day0['open'].iloc[0]
        current_ts  = day0.index[0]

        # 최대 6회 시도
        for i in range(6):
            at = attempts[i]
            future = df.loc[df.index > current_ts]
            if future.empty:
                break

            # TP/SL 수준 계산
            if at.direction == 'long':
                tp_price = entry_price * (1 + at.tp)
                sl_price = entry_price * (1 - at.sl)
            else:
                tp_price = entry_price * (1 - at.tp)
                sl_price = entry_price * (1 + at.sl)

            exit_price, exit_ts, result = entry_price, None, ''

            # SL 우선, TP 다음
            for ts, row in future.iterrows():
                if at.direction == 'long':
                    if row['low'] <= sl_price:
                        exit_price, exit_ts, result = sl_price, ts, 'SL'
                        break
                    if row['high'] >= tp_price:
                        exit_price, exit_ts, result = tp_price, ts, 'TP'
                        break
                else:
                    if row['high'] >= sl_price:
                        exit_price, exit_ts, result = sl_price, ts, 'SL'
                        break
                    if row['low'] <= tp_price:
                        exit_price, exit_ts, result = tp_price, ts, 'TP'
                        break

            # TP/SL 미발생 → 다음 첫봉(open)으로 EOD
            if exit_ts is None:
                exit_ts    = future.index[0]
                exit_price = future['open'].iloc[0]
                result     = 'EOD'

            # PnL 및 자본 업데이트
            qty = at.size / entry_price
            pnl = ((exit_price - entry_price) if at.direction=='long'
                   else (entry_price - exit_price)) * qty
            pnl -= at.size * fee_rate * 2
            capital += pnl

            # 기록
            records.append({
                'run_start':   run_start.strftime('%Y-%m-%d'),
                'attempt':     i+1,
                'direction':   at.direction,
                'entry_time':  current_ts,
                'entry_price': entry_price,
                'exit_time':   exit_ts,
                'exit_price':  exit_price,
                'result':      result,
                'pnl':         pnl,
                'capital':     capital,
            })

            # pnl > 0 이면 즉시 종료
            if pnl > 0:
                break

            # 남은 시도 위해 상태 갱신
            entry_price = exit_price
            current_ts  = exit_ts

    return pd.DataFrame(records)

def main():
    parser = argparse.ArgumentParser(
        description='매일 00:00(서울) 진입, 최대 6회 시도 백테스트'
    )
    parser.add_argument('csv',
        help='1h OHLCV CSV 경로 (open_time, open, high, low, close, volume)')
    parser.add_argument('-o','--output',
        help='결과 저장할 CSV 파일명', default=None)
    args = parser.parse_args()

    df     = load_data(args.csv)
    result = backtest(df)

    if args.output:
        result.to_csv(args.output, index=False)

    print(result.tail())
    if not result.empty:
        finals = result.groupby('run_start')['capital'].last()
        print("\n=== 각 계좌 최종 자본 ===")
        print(finals.to_string())
        total = finals.size
        pnl   = finals.sum() - 100_000 * total
        print(f"\n계좌 수: {total}, 전체 PnL: {pnl:.2f} USD")

if __name__ == '__main__':
    main()
