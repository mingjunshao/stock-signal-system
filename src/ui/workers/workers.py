"""后台工作线程：数据获取、回测、优化、信号生成"""

from PyQt5.QtCore import QThread, pyqtSignal

from src.data_layer.data_manager import DataManager
from src.backtest_engine.backtest_runner import BacktestRunner
from src.backtest_engine.backtest_result import BacktestResult
from src.strategy_engine.base_strategy import BaseStrategy
from src.strategy_engine.strategy_fusion import StrategyFusionEngine
from src.signal_output.signal_generator import SignalGenerator
from src.strategy_engine.signal import FusedSignal
from src.optimizer.optimization_result import OptimizationResult


class DataFetchWorker(QThread):
    """数据获取后台线程"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    finished_signal = pyqtSignal(bool, object)
    
    def __init__(self, data_manager: DataManager, symbols: list) -> None:
        super().__init__()
        self._data_mgr = data_manager
        self._symbols = symbols
        self._stop_flag = False
        
    def run(self) -> None:
        try:
            for i, symbol in enumerate(self._symbols):
                if self._stop_flag:
                    break
                self.log_signal.emit(f"更新数据: {symbol}")
                self.progress_signal.emit(i + 1, len(self._symbols))
                self._data_mgr.update_stock_data(symbol)
            self.finished_signal.emit(True, None)
        except Exception as e:
            self.finished_signal.emit(False, str(e))
            
    def stop(self) -> None:
        self._stop_flag = True


class BacktestWorker(QThread):
    """回测后台线程"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    finished_signal = pyqtSignal(bool, BacktestResult)
    
    def __init__(self, runner: BacktestRunner, symbol: str,
                 strategy: BaseStrategy, start_date: str, end_date: str,
                 params: dict = None) -> None:
        super().__init__()
        self._runner = runner
        self._symbol = symbol
        self._strategy = strategy
        self._start = start_date
        self._end = end_date
        self._params = params
        self._stop_flag = False
        
    def run(self) -> None:
        try:
            self.log_signal.emit(f"开始回测: {self._symbol}")
            result = self._runner.run_backtest(
                self._symbol, self._strategy, self._start, self._end, self._params
            )
            self.finished_signal.emit(True, result)
        except Exception as e:
            self.log_signal.emit(f"回测失败: {e}")
            self.finished_signal.emit(False, None)
            
    def stop(self) -> None:
        self._stop_flag = True


class FusionBacktestWorker(QThread):
    """融合策略回测后台线程"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    finished_signal = pyqtSignal(bool, BacktestResult)
    
    def __init__(self, runner: BacktestRunner, symbol: str,
                 fusion_engine: StrategyFusionEngine,
                 start_date: str, end_date: str) -> None:
        super().__init__()
        self._runner = runner
        self._symbol = symbol
        self._fusion = fusion_engine
        self._start = start_date
        self._end = end_date
        self._stop_flag = False
        
    def run(self) -> None:
        try:
            self.log_signal.emit(f"开始融合回测: {self._symbol}")
            result = self._runner.run_fusion_backtest(
                self._symbol, self._fusion, self._start, self._end
            )
            self.finished_signal.emit(True, result)
        except Exception as e:
            self.log_signal.emit(f"融合回测失败: {e}")
            self.finished_signal.emit(False, None)
            
    def stop(self) -> None:
        self._stop_flag = True


class OptimizerWorker(QThread):
    """参数优化后台线程"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    finished_signal = pyqtSignal(bool, OptimizationResult)
    
    def __init__(self, optimizer, symbol: str, strategy: BaseStrategy,
                 param_space, start_date: str, end_date: str,
                 metric: str = "sharpe_ratio", **kwargs) -> None:
        super().__init__()
        self._optimizer = optimizer
        self._symbol = symbol
        self._strategy = strategy
        self._param_space = param_space
        self._start = start_date
        self._end = end_date
        self._metric = metric
        self._kwargs = kwargs
        self._stop_flag = False
        
    def run(self) -> None:
        try:
            self.log_signal.emit(f"开始优化: {self._symbol}")
            result = self._optimizer.optimize(
                self._symbol, self._strategy, self._param_space,
                self._start, self._end, self._metric, **self._kwargs
            )
            self.finished_signal.emit(True, result)
        except Exception as e:
            self.log_signal.emit(f"优化失败: {e}")
            self.finished_signal.emit(False, None)
            
    def stop(self) -> None:
        self._stop_flag = True


class SignalWorker(QThread):
    """信号生成后台线程"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    finished_signal = pyqtSignal(bool, list)
    
    def __init__(self, generator: SignalGenerator, symbol: str,
                 start_date: str, end_date: str) -> None:
        super().__init__()
        self._generator = generator
        self._symbol = symbol
        self._start = start_date
        self._end = end_date
        self._stop_flag = False
        
    def run(self) -> None:
        try:
            self.log_signal.emit(f"生成信号: {self._symbol}")
            signals = self._generator.generate_historical_signals(
                self._symbol, self._start, self._end
            )
            self.finished_signal.emit(True, signals)
        except Exception as e:
            self.log_signal.emit(f"信号生成失败: {e}")
            self.finished_signal.emit(False, [])
            
    def stop(self) -> None:
        self._stop_flag = True
