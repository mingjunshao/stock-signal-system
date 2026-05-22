"""交易模拟器：A股T+1规则、佣金+印花税、涨跌停处理"""

import pandas as pd
from typing import List, Tuple

from src.core.constants import (
    COMMISSION_RATE, STAMP_TAX_RATE, MIN_COMMISSION,
    MIN_LOT_SIZE, LIMIT_UP_THRESHOLD, LIMIT_DOWN_THRESHOLD,
)
from src.core.logger import setup_logger
from src.strategy_engine.signal import FusedSignal, SignalType
from src.backtest_engine.backtest_result import TradeRecord

logger = setup_logger("trade_simulator")


class TradeSimulator:
    """模拟交易执行器，遵循A股交易规则"""

    def __init__(self, initial_capital: float = 100000,
                 commission_rate: float = COMMISSION_RATE,
                 stamp_tax_rate: float = STAMP_TAX_RATE,
                 min_commission: float = MIN_COMMISSION) -> None:
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.stamp_tax_rate = stamp_tax_rate
        self.min_commission = min_commission

    def simulate_trades(self, signals: List[FusedSignal],
                        df: pd.DataFrame) -> List[TradeRecord]:
        """根据融合信号模拟交易"""
        trades = []
        position = 0       # 持仓股数
        entry_price = 0.0
        entry_date = ""
        capital = self.initial_capital

        # 按日期排序信号
        signals_sorted = sorted(signals, key=lambda s: s.date)

        for sig in signals_sorted:
            if sig.signal_type == SignalType.HOLD:
                continue

            # 查找信号日的行情数据
            row = df[df["date"] == sig.date]
            if row.empty:
                continue
            row = row.iloc[0]

            close_price = row["close"]
            prev_close = row.get("prev_close", close_price)

            # 涨跌停检查
            price_change = (close_price - prev_close) / prev_close if prev_close > 0 else 0
            is_limit_up = price_change >= LIMIT_UP_THRESHOLD
            is_limit_down = price_change <= LIMIT_DOWN_THRESHOLD

            if sig.signal_type == SignalType.BUY and position == 0:
                # 涨停日无法买入
                if is_limit_up:
                    continue

                # 计算可买入股数（全仓模式，向下取整到100股）
                buy_amount = capital
                shares = int(buy_amount / close_price / MIN_LOT_SIZE) * MIN_LOT_SIZE
                if shares <= 0:
                    continue

                actual_cost = shares * close_price
                commission = self.calculate_commission(actual_cost, is_sell=False)

                entry_price = close_price
                entry_date = sig.date
                position = shares
                capital -= actual_cost + commission

            elif sig.signal_type == SignalType.SELL and position > 0:
                # 跌停日无法卖出
                if is_limit_down:
                    continue

                # A股T+1：当日买入不能当日卖出
                if entry_date == sig.date:
                    continue

                sell_amount = position * close_price
                commission = self.calculate_commission(sell_amount, is_sell=True)

                profit = sell_amount - position * entry_price - commission
                profit_rate = profit / (position * entry_price) * 100  # 转换为百分比
                holding_days = self._calc_holding_days(entry_date, sig.date, df)

                trades.append(TradeRecord(
                    entry_date=entry_date,
                    entry_price=entry_price,
                    exit_date=sig.date,
                    exit_price=close_price,
                    signal_type=sig.signal_type,
                    profit=profit,
                    profit_rate=profit_rate,
                    holding_days=holding_days,
                ))

                capital += sell_amount - commission
                position = 0
                entry_price = 0.0
                entry_date = ""

        # 处理回测结束时的未平仓持仓
        if position > 0 and not df.empty:
            last_row = df.iloc[-1]
            last_date = last_row["date"]
            last_close = last_row["close"]
            
            # 使用最后一天的收盘价计算未实现盈亏（不计算卖出佣金，因为没有实际卖出）
            sell_amount = position * last_close
            commission = 0  # 未实际卖出，不计算佣金
            profit = sell_amount - position * entry_price - commission
            profit_rate = profit / (position * entry_price) * 100  # 转换为百分比
            holding_days = self._calc_holding_days(entry_date, last_date, df)
            
            # 添加未平仓的交易记录，标记出来（exit_date可以设为特殊值或最后日期）
            trades.append(TradeRecord(
                entry_date=entry_date,
                entry_price=entry_price,
                exit_date=f"{last_date}(未平仓)",
                exit_price=last_close,
                signal_type=SignalType.SELL,
                profit=profit,
                profit_rate=profit_rate,
                holding_days=holding_days,
            ))
            
            logger.info(f"回测结束，有未平仓持仓: {entry_date} 买入，持仓 {holding_days} 天，盈亏 {profit:.2f} 元")

        return trades

    def calculate_commission(self, amount: float, is_sell: bool) -> float:
        """计算交易佣金（券商佣金+印花税）"""
        commission = max(amount * self.commission_rate, self.min_commission)
        if is_sell:
            commission += amount * self.stamp_tax_rate
        return commission

    def get_equity_curve(self, trades: List[TradeRecord],
                         df: pd.DataFrame) -> List[Tuple[str, float]]:
        """生成权益曲线"""
        equity = self.initial_capital
        curve = []
        position = 0
        entry_price = 0.0

        for _, row in df.iterrows():
            date = row["date"]
            close = row["close"]

            # 查找当日是否有交易
            for trade in trades:
                if trade.entry_date == date:
                    shares = int(equity / trade.entry_price / MIN_LOT_SIZE) * MIN_LOT_SIZE
                    position = shares
                    entry_price = trade.entry_price
                    equity -= shares * entry_price

                if trade.exit_date == date:
                    equity += position * trade.exit_price
                    position = 0

            # 当日权益 = 现金 + 持仓市值
            total_equity = equity + position * close
            curve.append((date, total_equity))

        return curve

    def _calc_holding_days(self, entry_date: str, exit_date: str,
                           df: pd.DataFrame) -> int:
        """计算持仓天数（交易日）"""
        mask = (df["date"] >= entry_date) & (df["date"] <= exit_date)
        return len(df[mask])