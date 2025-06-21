import argparse
from dataclasses import dataclass
import datetime as dt
from typing import List

import pandas as pd


@dataclass
class Attempt:
    direction: str  # 'long' or 'short'
    size: float
    tp: float  # take profit in decimal, e.g. 0.15
    sl: float  # stop loss in decimal, e.g. 0.05


def load_data(path: str) -> pd.DataFrame:
    """Load 1h OHLCV data from a CSV file."""
    df = pd.read_csv(path, parse_dates=['timestamp'])
    df = df.sort_values('timestamp')
    df.set_index('timestamp', inplace=True)
    return df


def backtest(df: pd.DataFrame) -> pd.DataFrame:
    capital = 100_000.0
    fee_rate = 0.0002  # 0.02% per side

    attempts: List[Attempt] = [
        Attempt('long', 669, 0.15, 0.05),
        Attempt('short', 1344, 0.10, 0.05),
        Attempt('long', 1347, 0.15, 0.05),
        Attempt('short', 2705, 0.10, 0.05),
        Attempt('long', 2712, 0.15, 0.05),
        Attempt('short', 5446, 0.10, 0.05),
    ]

    results = []

    start_date = df.index[0].normalize()
    end_date = start_date + pd.Timedelta(days=30)

    df = df.loc[(df.index >= start_date) & (df.index < end_date)]

    for day, day_df in df.groupby(df.index.date):
        open_row = day_df.between_time('09:00', '09:00')
        if open_row.empty:
            continue
        open_ts = open_row.index[0]
        entry_price = open_row['open'].iloc[0]
        current_idx = open_ts
        for i, attempt in enumerate(attempts, start=1):
            trade_df = day_df.loc[day_df.index > current_idx]
            if trade_df.empty:
                break
            if attempt.direction == 'long':
                tp_price = entry_price * (1 + attempt.tp)
                sl_price = entry_price * (1 - attempt.sl)
            else:
                tp_price = entry_price * (1 - attempt.tp)
                sl_price = entry_price * (1 + attempt.sl)

            exit_price = entry_price
            exit_ts = None
            hit = ''
            for ts, row in trade_df.iterrows():
                high, low = row['high'], row['low']
                if attempt.direction == 'long':
                    if low <= sl_price:
                        exit_price = sl_price
                        exit_ts = ts
                        hit = 'SL'
                        break
                    if high >= tp_price:
                        exit_price = tp_price
                        exit_ts = ts
                        hit = 'TP'
                        break
                else:
                    if high >= sl_price:
                        exit_price = sl_price
                        exit_ts = ts
                        hit = 'SL'
                        break
                    if low <= tp_price:
                        exit_price = tp_price
                        exit_ts = ts
                        hit = 'TP'
                        break
            if exit_ts is None:
                # If neither TP nor SL hit, close at final candle close
                last = trade_df.iloc[-1]
                exit_price = last['close']
                exit_ts = trade_df.index[-1]
                hit = 'EOD'

            qty = attempt.size / entry_price
            if attempt.direction == 'long':
                pnl = (exit_price - entry_price) * qty
            else:
                pnl = (entry_price - exit_price) * qty

            fees = attempt.size * fee_rate * 2
            pnl -= fees
            capital += pnl

            results.append(
                {
                    'date': day,
                    'attempt': i,
                    'direction': attempt.direction,
                    'entry_time': current_idx,
                    'entry_price': entry_price,
                    'exit_time': exit_ts,
                    'exit_price': exit_price,
                    'hit': hit,
                    'pnl': pnl,
                    'capital': capital,
                }
            )

            entry_price = exit_price
            current_idx = exit_ts
            if i == 6 and hit == 'SL':
                break
    return pd.DataFrame(results)


def main():
    parser = argparse.ArgumentParser(description='Backtest PEPE futures strategy.')
    parser.add_argument('csv', help='Path to 1h OHLCV data CSV with columns timestamp, open, high, low, close, volume')
    parser.add_argument('-o', '--output', help='Where to save results CSV')
    args = parser.parse_args()

    df = load_data(args.csv)
    results = backtest(df)
    if args.output:
        results.to_csv(args.output, index=False)
    print(results.tail())
    if not results.empty:
        print(f"Final capital: {results.iloc[-1]['capital']:.2f}")


if __name__ == '__main__':
    main()