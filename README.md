# Pepe
PEPE Coin Backtesting Strategy
Objective:
The goal is to backtest a trading strategy for PEPE coin futures over a period of 1 month.

Strategy Overview:
Capital: $100,000

Entry: Every day at 09:00 (market open price).

Positions:

Max 6 attempts per day.

If a position hits stop loss, the opposite position is entered.

Position Sizes and Rules:

1st Position (Long): $669 | Take Profit: +15% | Stop Loss: -5% (Reverse on loss)

2nd Position (Short): $1344 | Take Profit: +10% | Stop Loss: -5% (Reverse on loss)

3rd Position (Long): $1347 | Take Profit: +15% | Stop Loss: -5% (Reverse on loss)

4th Position (Short): $2705 | Take Profit: +10% | Stop Loss: -5% (Reverse on loss)

5th Position (Long): $2712 | Take Profit: +15% | Stop Loss: -5% (Reverse on loss)

6th Position (Short): $5446 | Take Profit: +10% | Stop Loss: -5% (Final Stop Loss on loss)

Transaction Fees: 0.02% on each buy and sell.

Exit Conditions: Positions are not closed before the 6th attempt, unless the final stop loss is hit.

Backtesting Details:
Time Period: 1 month.

Data Source: Help is needed to secure 1-hour historical data for PEPE coin.

Leverage: No leverage will be used.

Order Execution: All orders will be executed at the open price of the 09:00 candle.

Stop Loss & Take Profit: The strategy includes specific percentages for take profit and stop loss for each position.
