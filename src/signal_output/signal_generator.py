"""信号生成器：协调策略→融合→最终信号"""

import pandas as pd
from typing import Dict, List, Optional

from src.core.constants import StrategyType
from src.core.logger import setup_logger
from src.data_layer.data_manager import DataManager
from src.strategy_engine.base_strategy import BaseStrategy
from src.strategy_engine.strategy_fusion import StrategyFusionEngine
from src.strategy_engine.signal import FusedSignal

logger = setup_logger("signal_generator")


class SignalGenerator:
    """信号生成器，协调多策略→融合→最终信号"""

    def __init__(self, fusion_engine: StrategyFusionEngine,
                 data_manager: DataManager) -> None:
        self._fusion = fusion_engine
        self._data_mgr = data_manager

    def generate_signals(self, symbol: str,
                         end_date: str) -> List[FusedSignal]:
        """生成指定股票的最新信号"""
        from datetime import datetime
        start_date = "2020-01-01"
        df = self._data_mgr.fetch_full_data(symbol, start_date, end_date)
        if df.empty:
            return []

        all_signals: Dict[StrategyType, list] = {}
        for strategy in self._fusion.strategies:
            sigs = strategy.generate_signals(df)
            all_signals[strategy.strategy_type] = sigs

        return self._fusion.fuse_signals(all_signals, df)

    def generate_historical_signals(self, symbol: str,
                                    start_date: str, end_date: str) -> List[FusedSignal]:
        """生成历史信号（用于回测和图表标注）"""
        df = self._data_mgr.fetch_full_data(symbol, start_date, end_date)
        if df.empty:
            return []

        all_signals: Dict[StrategyType, list] = {}
        for strategy in self._fusion.strategies:
            sigs = strategy.generate_signals(df)
            all_signals[strategy.strategy_type] = sigs

        return self._fusion.fuse_signals(all_signals, df)

    def get_latest_signal(self, symbol: str) -> Optional[FusedSignal]:
        """获取最新一个信号"""
        from datetime import datetime
        end_date = datetime.now().strftime("%Y-%m-%d")
        signals = self.generate_signals(symbol, end_date)
        if signals:
            return signals[-1]
        return None