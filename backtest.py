#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from dataclasses import dataclass
from datetime import timedelta
from typing import List, Tuple, Dict
import pandas as pd
from heapq import heappush, heappop

@dataclass
class Attempt:
    direction: str   # 'long' 또는 'short'
    size: float      # 투자 금액
    tp: float        # 익절 비율
    sl: float        # 손절 비율


def load_data(path: str) -> pd.DataFrame:
    """
    1시간봉 CSV 읽기 및 타임스탬프를 Asia/Seoul로 변환
    """
    df = pd.read_csv(path)
    df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms', utc=True)
    df['timestamp'] = df['timestamp'].dt.tz_convert('Asia/Seoul')
    return df.set_index('timestamp')[['open','high','low','close','volume']].sort_index()


def backtest(df: pd.DataFrame) -> pd.DataFrame:
    """
    - 총 30개 계좌, 각 계좌 100,000$
    - 한국시간 매일 00:00마다 순차적으로 A1→A30 spawn
    - 각 계좌는 최대 6회 시도, pnl>0 익절 시 종료
    - 실패 후 남은 시도는 크로스데이 유지하며 다음 이벤트에서 재시도
    - 매일 00:00 신규 계좌 spawn + 기존 계좌 잔여 시도 병행
    """
    # 거래 수수료
    fee_rate = 0.0002
    # 포지션 설정
    attempts: List[Attempt] = [
        Attempt('long',  669, 0.16, 0.04),
        Attempt('short',1344, 0.12,0.04),
        Attempt('long', 1347, 0.16,0.04),
        Attempt('short',2705, 0.12,0.04),
        Attempt('long', 2712, 0.16,0.04),
        Attempt('short',5446, 0.12,0.04),
    ]
    records = []

    # 시뮬레이션 날짜
    start = df.index[0].normalize()
    end = start + timedelta(days=30)
    days = pd.date_range(start, end, freq='D', tz='Asia/Seoul')

    # 이벤트 큐: (timestamp, account_id, next_attempt, capital, entry_price)
    pending: List[Tuple[pd.Timestamp,int,int,float,float]] = []
    next_account = 1
    last_capital: Dict[int,float] = {}

    def spawn(account_id: int, ts: pd.Timestamp, ai: int, cap: float, price: float):
        heappush(pending, (ts, account_id, ai, cap, price))

    # 매일 00:00 신규 계좌 spawn
    def spawn_new(day: pd.Timestamp):
        nonlocal next_account
        if next_account > 30:
            return
        candle = df[(df.index.normalize()==day)&(df.index.hour==0)]
        if candle.empty:
            return
        ts0 = candle.index[0]
        price0 = candle['open'].iloc[0]
        spawn(next_account, ts0, 1, 100000.0, price0)
        last_capital[next_account] = 100000.0
        next_account += 1

    # 일별 이벤트 처리
    for i, day in enumerate(days):
        # 00:00에 신규 계좌 추가
        spawn_new(day)
        next_mid = day + timedelta(days=1)
        # 00:00~23:59 사이에 발생하는 이벤트 처리
        while pending and pending[0][0] < next_mid:
            ts, aid, ai, cap, price = heappop(pending)
            at = attempts[ai-1]
            # 이후 시점 데이터
            future = df.loc[df.index > ts]
            if future.empty:
                continue
            # TP/SL 계산
            tp = price * (1 + at.tp) if at.direction=='long' else price * (1 - at.tp)
            sl = price * (1 - at.sl) if at.direction=='long' else price * (1 + at.sl)
            exit_ts = None
            exit_price = price
            result = ''
            # SL 우선, TP 다음
            for t, row in future.iterrows():
                low, high = row['low'], row['high']
                if at.direction=='long':
                    if low <= sl:
                        exit_price, exit_ts, result = sl, t, 'SL'
                        break
                    if high >= tp:
                        exit_price, exit_ts, result = tp, t, 'TP'
                        break
                else:
                    if high >= sl:
                        exit_price, exit_ts, result = sl, t, 'SL'
                        break
                    if low <= tp:
                        exit_price, exit_ts, result = tp, t, 'TP'
                        break
            # SL/TP 미발생 -> 다음 첫봉 open으로 EOD
            if exit_ts is None:
                exit_ts = future.index[0]
                exit_price = future['open'].iloc[0]
                result = 'EOD'
            # PnL 계산
            qty = at.size / price
            pnl = ((exit_price - price) if at.direction=='long' else (price - exit_price)) * qty
            pnl -= at.size * fee_rate * 2
            cap += pnl
            last_capital[aid] = cap
            # 기록
            records.append({
                'account_id': aid,
                'date': day.strftime('%Y-%m-%d'),
                'attempt': ai,
                'entry_time': ts,
                'entry_price': price,
                'exit_time': exit_ts,
                'exit_price': exit_price,
                'result': result,
                'pnl': pnl,
                'capital': cap
            })
            # 성공 시 종료
            if pnl > 0:
                continue
            # 실패 후 남은 시도 병행
            if ai < 6:
                spawn(aid, exit_ts, ai+1, cap, exit_price)
            # ai==6 은 최종 종료
    return pd.DataFrame(records)


def main():
    parser = argparse.ArgumentParser(
        description='PEPE 전략 백테스팅 (30개 계좌, 크로스데이 시도)')
    parser.add_argument('csv', help='1h OHLCV CSV 파일 경로')
    parser.add_argument('-o', '--output', help='전체 결과 저장 CSV', default=None)
    args = parser.parse_args()

    df = load_data(args.csv)
    result = backtest(df)

    if args.output:
        result.to_csv(args.output, index=False)

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)

    print('=== 전체 거래 내역 ===')
    print(result.to_string())

    # 계좌별 CSV
    for aid, grp in result.groupby('account_id'):
        fn = f'account_{aid}_results.csv'
        grp.to_csv(fn, index=False)
        print(f'계좌 {aid} 내역 저장: {fn}')

    # 최종 자본 요약
    finals = result.groupby('account_id')['capital'].last()
    print('\n=== 계좌별 최종 자본 ===')
    print(finals.to_string())
    total = len(finals)
    total_pnl = finals.sum() - 100000 * total
    print(f'\n계좌 수: {total}, 총 PnL: {total_pnl:.2f} USD')


if __name__ == '__main__':
    main()