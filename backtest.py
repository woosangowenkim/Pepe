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
    df = df.set_index('timestamp').sort_index()
    return df[['open','high','low','close','volume']]

def backtest(df: pd.DataFrame) -> pd.DataFrame:
    """
    매일 서울 시간 00:00 시가에 진입하여,
    최대 6번까지 시도하는 PEPE 전략 백테스트 수행.
    - 초기 자본: 100,000 USD
    - 거래 수수료: 0.02% (매수+매도)
    - 손절(SL) 시에만 반대 포지션 진입
    - 익절(pnl>0) 시 즉시 종료
    - 최대 6번째 시도까지
    """
    capital = 100_000.0
    fee_rate = 0.0002  # 0.02%

    attempts: List[Attempt] = [
        Attempt('long',  669,  0.16, 0.04),
        Attempt('short', 1344, 0.12, 0.04),
        Attempt('long',  1347, 0.16, 0.04),
        Attempt('short', 2705, 0.12, 0.04),
        Attempt('long',  2712, 0.16, 0.04),
        Attempt('short', 5446, 0.12, 0.04),
    ]

    records = []

    start_day = df.index[0].normalize()
    end_day   = start_day + pd.Timedelta(days=30)
    df_period = df.loc[start_day : end_day]

    for day, group in df_period.groupby(df_period.index.normalize()):
        open_candle = group.between_time('00:00','00:00')
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

            # 미래 캔들 스캔: SL 먼저, TP 다음
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

            # TP/SL 미발생 시 EOD 종가 청산
            if exit_ts is None:
                exit_ts    = future.index[-1]
                exit_price = future['close'].iloc[-1]
                result     = 'EOD'

            # PnL 계산 및 자본 업데이트
            qty = at.size / entry_price
            pnl = ((exit_price - entry_price) if at.direction=='long'
                   else (entry_price - exit_price)) * qty
            pnl -= at.size * fee_rate * 2
            capital += pnl

            # 거래 기록 저장
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

            # pnl > 0 이면 당일 종료, 아니면 최대 6회까지 반복
            if pnl > 0 or i == 6:
                break

            # SL 또는 EOD(손실) 시 반대포지션 진입
            entry_price = exit_price
            current_ts  = exit_ts

    return pd.DataFrame(records)

def main():
    parser = argparse.ArgumentParser(
        description='PEPE 코인 전략 백테스트 (서울 시간 00:00 진입)'
    )
    parser.add_argument('csv',
        help='1h OHLCV CSV 파일 경로 (open_time, open, high, low, close, volume)')
    parser.add_argument('-o','--output',
        help='결과를 저장할 CSV 파일명', default=None)
    args = parser.parse_args()

    df     = load_data(args.csv)
    result = backtest(df)

    if args.output:
        result.to_csv(args.output, index=False)

    print(result.tail())
    if not result.empty:
        print(f"최종 자본: {result.iloc[-1]['capital']:.2f} USD, 총 거래 횟수: {len(result)}건")

if __name__ == '__main__':
    main()
