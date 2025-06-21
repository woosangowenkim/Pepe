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


PEPE 코인 선물을 내가 만든 전략에 맞춰서 백테스팅을 해보고 싶다
 

내 전략은 다음과 같애:

자본금 : 3,000,000$
계좌30개 
A1 : 100,000$
A2 : 100,000$
계좌는 A1 ~ A30까지 있고, 각 계좌당 동일하게 100,000$이 들어있다

한국시간 매일 00:00 매수 계좌 A1부터 시작한다 
날짜와 상관없이 최종 익절 또는 손절 할때 까지 계속 시도한다
만약에 A1계좌가 당일에 익절하지도 못하고 최종 손절하지도 못했다면 날짜와 상관없이 남은횟수(최대 6번)를 최종 익절 또는 손절 할때 까지 계속 시도한다.
A1계좌가 계속 운영중이라면, 다음날 00:00시에는 A2 계좌가 아래 규칙을 실행한다. 
다른계좌도 동일하게 이 규칙을 적용한다

만약 A1계좌가 성공했다면, A1계좌는 중지한다
아직 전략을 운용중인 계좌가 있다면 날짜와 상관없이 남은횟수(최대 6번)를 최종 익절 또는 손절 할때 까지 계속 운영한다   


1차 매수 669$ (롱) : +16% 익절 -4% 손절 > 손절과 동시에 반대포지션 진입  
2차 매수 1344$ (숏) : +12% 익절 -4% 손절 > 손절과 동시에 반대포지션 진입
3차 매수 1347$ (롱) : +16% 익절 -4% 손절 > 손절과 동시에 반대포지션 진입
4차 매수 2705$ (숏) : +12% 익절 -4% 손절 > 손절과 동시에 반대포지션 진입
5차 매수 2712$ (롱) : +16% 익절 -4% 손절 > 손절과 동시에 반대포지션 진입  
6차 매수 5446$ (숏) : +12% 익절 -4% 손절 > 6차 손절시 최종 손절 처리

